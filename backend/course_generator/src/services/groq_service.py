import os
import time
import random
import logging
import asyncio
from typing import Optional

import aiohttp

from course_generator.src.core.token_utils import count_tokens

logger = logging.getLogger("groq_service")
logger.setLevel(logging.INFO)





# --- New global synchronization primitives ---------------------------------------------------------
# Global asyncio lock to ensure only one Groq request runs at a time
GLOBAL_LOCK = asyncio.Lock()

# Track last request timestamp (float seconds since epoch). Protect access by GLOBAL_LOCK.
LAST_REQUEST_TS = 0.0

# Minimum interval (seconds) to enforce BEFORE every API call. Default to 6s per user request.
MIN_INTERVAL = float(os.getenv("GROQ_MIN_INTERVAL", "6.0"))

# Circuit breaker timestamp: if now < CIRCUIT_BREAKER_UNTIL then breaker is open.
CIRCUIT_BREAKER_UNTIL = 0.0

# Track consecutive 429s globally. If this reaches 3, abort pipeline gracefully.
CONSECUTIVE_429_COUNT = 0

class PipelineAbortError(Exception):
    """Raised when consecutive 429 limits are exceeded."""
    pass

def _is_circuit_open() -> bool:
    return time.time() < CIRCUIT_BREAKER_UNTIL


def _open_circuit(cooldown_seconds: float = 60.0):
    global CIRCUIT_BREAKER_UNTIL
    CIRCUIT_BREAKER_UNTIL = time.time() + float(cooldown_seconds)
    logger.warning(f"[CIRCUIT] Opened circuit for {cooldown_seconds}s until {CIRCUIT_BREAKER_UNTIL}")


def _remaining_cooldown() -> float:
    rem = CIRCUIT_BREAKER_UNTIL - time.time()
    return rem if rem > 0 else 0.0
# --------------------------------------------------------------------------------------------------


async def retry_with_backoff(
    func,
    is_retryable,
    max_retries: int = 5,
    initial_delay: float = 5.0,
    max_delay: float = 120.0,
    jitter_range: tuple = (1.0, 3.0),
):
    attempt = 0
    delay = initial_delay
    while True:
        try:
            attempt += 1
            return await func()
        except Exception as e:
            retryable = is_retryable(e)
            if not retryable or attempt >= max_retries:
                logger.info(f"Not retrying (attempt {attempt}). Error: {e}")
                raise
            jitter = random.uniform(jitter_range[0], jitter_range[1])
            sleep_time = min(max_delay, delay) + jitter
            logger.info(
                f"Retryable error on attempt {attempt}: {e}; base_delay={delay:.1f}s jitter={jitter:.1f}s total_sleep={sleep_time:.1f}s"
            )
            await asyncio.sleep(sleep_time)
            # exponential backoff doubling
            delay = min(max_delay, delay * 2)


async def safe_groq_request(
    prompt: str,
    model: str = "llama-3.1-8b-instant",
    max_tokens: int = 400,
    temperature: float = 0.7,
    token_limit: int = 2000,
    stage_context: Optional[str] = None,
    **kwargs,
) -> str:
    """
    Single canonical Groq request helper.

    Signature:
        safe_groq_request(prompt, model, max_tokens, temperature)

    Returns the assistant content string. Retries on 429, network errors, and invalid/empty responses.
    """
    print("✅ safe_groq_request v2 called")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set in environment")

    # Enforce truncation
    estimated = count_tokens(prompt) + max_tokens
    if estimated > token_limit:
        overage = estimated - token_limit
        logger.warning(f"⚠️ Prompt too large (estimated {estimated} > {token_limit}). Truncating {overage} tokens.")
        # Very rough truncation: 1 token ~ 4 chars
        char_truncate = overage * 4
        if char_truncate < len(prompt):
            prompt = prompt[:len(prompt) - char_truncate] + "... [TRUNCATED]"
        else:
            prompt = prompt[:1000] + "... [TRUNCATED]"
        estimated = token_limit
        
    messages = [{"role": "user", "content": prompt}]
    logger.info(f"📊 [TOKENS] Stage={stage_context or 'unknown'} Estimated tokens={estimated} (limit={token_limit})")

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
    }

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # Implement manual retry loop with circuit-breaker awareness and a global lock
    max_retries = int(os.getenv("GROQ_MAX_RETRIES", "3"))
    backoff_sequence = [10, 30, 60]  # seconds for retries
    attempt = 0

    while True:
        attempt += 1

        # Acquire global lock to prevent concurrent requests
        logger.info(f"[LOCK] Attempting to acquire GLOBAL_LOCK for stage={stage_context}")
        async with GLOBAL_LOCK:
            logger.info(f"[LOCK] Acquired GLOBAL_LOCK for stage={stage_context}")
            
            # If circuit is open, wait inside the lock so no other requests queue immediately
            if _is_circuit_open():
                rem = _remaining_cooldown()
                logger.warning(f"[CIRCUIT] Circuit open, waiting {rem:.1f}s before next attempt")
                await asyncio.sleep(rem)

            # Enforce minimum interval BEFORE the call
            global LAST_REQUEST_TS, CONSECUTIVE_429_COUNT
            now = time.time()
            elapsed = now - LAST_REQUEST_TS if LAST_REQUEST_TS else None
            if LAST_REQUEST_TS and elapsed is not None and elapsed < MIN_INTERVAL:
                wait = MIN_INTERVAL - elapsed
                logger.info(f"[RATE] Waiting {wait:.2f}s to respect min interval before API call")
                await asyncio.sleep(wait)

            # Make the HTTP call while holding the lock (ensures strictly sequential calls)
            try:
                start_ts = time.time()
                logger.info(f"[GROQ] Sending request at {start_ts:.3f} stage={stage_context} est_tokens={estimated}")
                async with aiohttp.ClientSession() as session:
                    async with session.post(os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1") + "/chat/completions", headers=headers, json=payload) as resp:
                        status = resp.status
                        text = await resp.text()
                        logger.info({"stage": stage_context, "status": status, "est_tokens": estimated, "response_len": len(text)})
                        if status == 200:
                            data = await resp.json()
                            if not data or 'choices' not in data or not data['choices']:
                                raise RuntimeError("Empty or malformed choices structure in Groq response")
                            choice = data['choices'][0]
                            if 'message' not in choice or 'content' not in choice['message']:
                                raise RuntimeError("Missing choice.message.content in Groq response")
                            content = choice['message']['content']
                            if not content or not str(content).strip():
                                raise RuntimeError("Empty content in Groq response")
                            # update last request timestamp
                            LAST_REQUEST_TS = time.time()
                            CONSECUTIVE_429_COUNT = 0
                            logger.info(f"[GROQ] Request successful; updated LAST_REQUEST_TS={LAST_REQUEST_TS:.3f}")
                            return content
                        elif status == 429:
                            LAST_REQUEST_TS = time.time()
                            logger.warning(f"[GROQ] Received 429 Rate Limit for stage={stage_context}")
                            CONSECUTIVE_429_COUNT += 1
                            if CONSECUTIVE_429_COUNT >= 3:
                                logger.error("[FATAL] Received 3 consecutive 429s. Aborting pipeline.")
                                raise PipelineAbortError("Pipeline aborted gracefully due to consecutive 429s")
                            # Open circuit for cooldown period
                            _open_circuit(60.0)
                            # fall through to retry handling after releasing lock
                            raise RuntimeError("HTTP 429 Rate limit")
                        else:
                            raise RuntimeError(f"Groq API error {status}: {text}")

            except aiohttp.ClientError as ce:
                LAST_REQUEST_TS = time.time()
                logger.warning(f"[GROQ] Network error during Groq request: {ce}")
                # will go to retry below
                last_exc = ce
            except PipelineAbortError as pae:
                # Rethrow instantly without releasing to retry block (lock will be released in finally)
                raise
            except Exception as e:
                LAST_REQUEST_TS = time.time()
                # If it's a rate/429 we set circuit and will retry per policy, otherwise rethrow
                last_exc = e
            finally:
                logger.info(f"[LOCK] Releasing GLOBAL_LOCK for stage={stage_context}")

        # If we reached here, the call failed (either network or 429 or other). Decide retry.
        # If 429/circuit was opened, wait until cooldown before retrying.
        if attempt > max_retries:
            logger.error(f"[GROQ] Exhausted retries ({max_retries}). Last error: {last_exc}")
            raise RuntimeError(f"Groq request failed after {max_retries} attempts: {last_exc}")

        # Wait for circuit cooldown if open
        if _is_circuit_open():
            rem = _remaining_cooldown()
            logger.info(f"[RETRY] Waiting for circuit cooldown {rem:.1f}s before retry (attempt {attempt})")
            await asyncio.sleep(rem)

        # Exponential backoff per attempt (10, 30, 60)
        backoff = backoff_sequence[min(attempt - 1, len(backoff_sequence) - 1)]
        jitter = random.uniform(1.0, 3.0)
        wait_time = backoff + jitter
        logger.info(f"[RETRY] Sleeping backoff {backoff}s + jitter {jitter:.1f}s = {wait_time:.1f}s before retry (attempt {attempt})")
        await asyncio.sleep(wait_time)


def get_rate_status() -> dict:
    """Return current rate limiter and circuit-breaker status for instrumentation."""
    return {
        "circuit_open": _is_circuit_open(),
        "remaining_cooldown": _remaining_cooldown(),
        "last_request_ts": LAST_REQUEST_TS,
        "min_interval": MIN_INTERVAL,
    }
