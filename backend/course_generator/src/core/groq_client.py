import asyncio
import json
import os
from typing import Dict, List, Optional
import aiohttp


class GroqClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.base_url = "https://api.groq.com/openai/v1"
        self.session: Optional[aiohttp.ClientSession] = None

        if not self.api_key:
            raise ValueError("Groq API key required. Set GROQ_API_KEY in .env")

    async def _get_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 500,
        temperature: float = 0.2,
        response_format: Optional[Dict] = None,
        model: str = "llama-3.1-8b-instant",
        pydantic_model=None,
        allow_chunking: bool = True,
    ) -> str:
        """
        Send chat completion request to Groq API
        Includes retry logic and timeout handling
        """

        def _estimate_tokens_for_messages(msgs: List[Dict[str, str]]) -> int:
            """Rudimentary token estimator: approximate tokens by characters/4.
            This is intentionally conservative and configurable via GROQ_TOKEN_LIMIT.
            """
            total_chars = 0
            for m in msgs:
                # Some messages may not have content or may be non-strings
                c = m.get("content") or ""
                if not isinstance(c, str):
                    c = str(c)
                total_chars += len(c)

            # heuristic: ~4 characters per token (conservative)
            return max(0, total_chars // 4)

        # Configurable token safety limit (Groq account-level TPM limit per minute)
        token_limit = int(os.getenv("GROQ_TOKEN_LIMIT", "2000"))
        # Force truncation in case of TPM overflow
        auto_truncate = True

        session = await self._get_session()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Automatically inject JSON schema instructions to guide the model if a pydantic model is provided
        if pydantic_model:
            import json
            schema_dump = json.dumps(pydantic_model.model_json_schema())
            schema_instruction = f" You MUST return a JSON object that strictly adheres to this JSON schema: {schema_dump}. Do not include markdown formatting or extra text."
            
            system_msg_idx = next((i for i, m in enumerate(messages) if m["role"] == "system"), -1)
            if system_msg_idx >= 0:
                messages[system_msg_idx]["content"] += schema_instruction
            else:
                messages.insert(0, {"role": "system", "content": f"You are a strict JSON data generator.{schema_instruction}"})

        # Estimate tokens consumed by messages + requested output tokens
        est_message_tokens = _estimate_tokens_for_messages(messages)
        est_total_tokens = est_message_tokens + max_tokens

        if est_total_tokens > token_limit:
            msg = (
                f"Estimated tokens ({est_total_tokens}) exceed token limit ({token_limit})."
            )
            print(f"⚠️ {msg}")

            if not auto_truncate:
                # If chunking is enabled, attempt to split the large user message into smaller calls
                auto_chunk = os.getenv("GROQ_AUTO_CHUNK", "true").lower() in ("1", "true", "yes")

                if auto_chunk and allow_chunking:
                    # Find a large user message to split
                    user_msgs_idx = [i for i, m in enumerate(messages) if m.get("role") == "user"]
                    if user_msgs_idx:
                        # Prefer the longest user message
                        longest_idx = max(user_msgs_idx, key=lambda i: len(str(messages[i].get("content") or "")))
                        content_to_split = str(messages[longest_idx].get("content") or "")

                        # Determine chars per chunk roughly from token_limit
                        available_tokens_per_call = max(100, token_limit - max_tokens - 50)
                        chars_per_chunk = max(1000, available_tokens_per_call * 4)

                        chunks = [content_to_split[i:i+chars_per_chunk] for i in range(0, len(content_to_split), chars_per_chunk)]
                        print(f"ℹ️ Auto-chunking user message into {len(chunks)} pieces (≈{chars_per_chunk} chars each)")

                        results = []
                        for idx, chunk in enumerate(chunks):
                            print(f"🔁 Chunk {idx+1}/{len(chunks)} - sending smaller request to Groq")
                            # make a shallow copy of messages and replace the chosen user content
                            chunked_messages = [dict(m) for m in messages]
                            chunked_messages[longest_idx]["content"] = chunk

                            # Recursive call but disallow further chunking to avoid loops
                            chunk_result = await self.chat_completion(
                                messages=chunked_messages,
                                max_tokens=max_tokens,
                                temperature=temperature,
                                response_format=response_format,
                                model=model,
                                pydantic_model=pydantic_model,
                                allow_chunking=False,
                            )

                            results.append(chunk_result)

                        # If pydantic_model was provided, results are model instances; try merging
                        if pydantic_model:
                            try:
                                merged_dict = {}
                                # convert each result to dict
                                dicts = [r.model_dump() if hasattr(r, 'model_dump') else (r.dict() if hasattr(r, 'dict') else r) for r in results]
                                # Merge list fields by concatenation, keep scalar from first
                                for k in dicts[0].keys():
                                    values = [d.get(k) for d in dicts]
                                    if all(isinstance(v, list) for v in values):
                                        merged_dict[k] = [item for sub in values for item in sub]
                                    else:
                                        merged_dict[k] = values[0]

                                merged_model = pydantic_model(**merged_dict)
                                return merged_model
                            except Exception as e:
                                print(f"⚠️ Failed to merge chunked pydantic results: {e}")
                                # Fall back to returning raw concatenated strings
                                return "\n".join([r if isinstance(r, str) else str(r) for r in results])

                        # If no pydantic_model, simply concatenate string responses
                        return "\n".join([r if isinstance(r, str) else str(r) for r in results])

                # If chunking not enabled or unsuccessful, raise
                raise Exception(
                    msg + " Set GROQ_AUTO_TRUNCATE=true to enable automatic truncation or reduce your message size."
                )

            # Auto-truncate messages proportionally to fit within limit
            available_for_messages = max(0, token_limit - max_tokens - 50)  # keep small buffer
            if available_for_messages <= 0:
                raise Exception(msg + " Not enough room for messages after reserving max_tokens.")

            reduction_ratio = available_for_messages / max(1, est_message_tokens)
            print(f"ℹ️ Auto-truncating messages to {int(reduction_ratio*100)}% of original size to fit token limit")

            # Truncate each message content proportionally
            for m in messages:
                c = m.get("content") or ""
                if not isinstance(c, str):
                    c = str(c)
                keep_chars = int(len(c) * reduction_ratio)
                if keep_chars < len(c):
                    # keep a small suffix to indicate truncation
                    truncated = c[:max(0, keep_chars - 12)].rstrip()
                    m["content"] = truncated + "... [truncated]"

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False
        }

        if response_format:
            payload["response_format"] = response_format

        max_retries = 3

        import time
        from course_generator.src.services.groq_service import (
            GLOBAL_LOCK, MIN_INTERVAL, _is_circuit_open, _remaining_cooldown, _open_circuit, PipelineAbortError
        )
        import course_generator.src.services.groq_service as groq_service_module

        attempt = 0
        while attempt < max_retries:
            attempt += 1

            try:
                print(f"🔄 Attempt {attempt}/{max_retries} - Sending request to Groq...")

                timeout_seconds = 180 + (attempt * 60)
                
                async with GLOBAL_LOCK:
                    if _is_circuit_open():
                        rem = _remaining_cooldown()
                        print(f"⚠️ [CIRCUIT] Circuit open, waiting {rem:.1f}s before request")
                        await asyncio.sleep(rem)
                        
                    now = time.time()
                    elapsed = now - groq_service_module.LAST_REQUEST_TS if groq_service_module.LAST_REQUEST_TS else None
                    min_interval = 5.0
                    if groq_service_module.LAST_REQUEST_TS and elapsed is not None and elapsed < min_interval:
                        wait_t = min_interval - elapsed
                        print(f"⏳ [RATE] Waiting {wait_t:.2f}s to respect global interval")
                        await asyncio.sleep(wait_t)

                    async with session.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=timeout_seconds)
                    ) as response:

                        str_status = response.status
                        groq_service_module.LAST_REQUEST_TS = time.time()
                        
                        if str_status == 200:
                            groq_service_module.CONSECUTIVE_429_COUNT = 0
                        elif str_status == 429:
                            print(f"❌ [GROQ] 429 Rate Limit hit!")
                            groq_service_module.CONSECUTIVE_429_COUNT += 1
                            if groq_service_module.CONSECUTIVE_429_COUNT >= 3:
                                raise PipelineAbortError("Pipeline aborted due to 3 consecutive 429s in GroqClient")
                            _open_circuit(60.0)
                            raise RuntimeError("HTTP_429")

                        if str_status == 200:
                            data = await response.json()
                            if "choices" not in data or not data["choices"]:
                                raise Exception("Invalid response structure from Groq API")
                            content = data["choices"][0]["message"]["content"]
                            if not content:
                                raise Exception("Empty response from Groq")
                            print(f"✅ Received response ({len(content)} characters)")
                            content = content.strip()
                            # Pydantic validation...
                            if pydantic_model:
                                try:
                                    import json
                                    json_parsed = json.loads(content)
                                    validated = pydantic_model(**json_parsed)
                                    return validated
                                except Exception as e:
                                    print(f"⚠️ Pydantic validation failed: {str(e)}")
                                    messages.append({"role": "assistant", "content": content})
                                    messages.append({"role": "user", "content": f"Fix JSON strictly: {str(e)}"})
                                    if attempt == max_retries:
                                        raise Exception(f"Failed to match Pydantic schema: {str(e)}")
                                    continue
                            return content
                            
                        elif str_status == 401:
                            text = await response.text()
                            raise Exception(f"Authentication failed: {text}")

                        else:
                            text = await response.text()
                            raise RuntimeError(f"API_ERROR_{str_status}")

            except PipelineAbortError:
                raise
            except aiohttp.ClientError as e:
                groq_service_module.LAST_REQUEST_TS = time.time()
                print(f"🔌 Network connection error: {str(e)}")
                last_exc = RuntimeError("CONNECTION_ERROR")
            except asyncio.TimeoutError:
                groq_service_module.LAST_REQUEST_TS = time.time()
                print(f"⏰ Timeout error")
                last_exc = RuntimeError("CONNECTION_ERROR")
            except Exception as e:
                groq_service_module.LAST_REQUEST_TS = time.time()
                last_exc = e

            if attempt >= max_retries:
                raise Exception(f"Groq API request failed after {max_retries} attempts: {str(last_exc)}")
                
            error_str = str(last_exc)
            if "HTTP_429" in error_str:
                print(f"🔁 [RETRY] 429 Hit. Next attempt will wait for circuit cooldown.")
                continue
            elif "CONNECTION_ERROR" in error_str or "API_ERROR" in error_str:
                delay = 6.0
                print(f"🔁 [RETRY] Connection issue. Waiting {delay:.1f}s before attempt.")
                await asyncio.sleep(delay)
                continue
            else:
                delay = 6.0
                print(f"🔁 [RETRY] Error occurred. Waiting {delay:.1f}s before attempt.")
                await asyncio.sleep(delay)
                continue


    async def test_connection(self) -> Dict[str, str]:
        """
        Test if Groq API works
        """

        try:

            response = await self.chat_completion(
                messages=[{
                    "role": "user",
                    "content": "Reply with 'Connection successful'"
                }],
                max_tokens=50,
                temperature=0
            )

            return {
                "success": True,
                "provider": "Groq",
                "model": "llama-3.3-70b-versatile",
                "response": response
            }

        except Exception as e:

            return {
                "success": False,
                "provider": "Groq",
                "error": str(e)
            }

    async def close_session(self):
        """Close aiohttp session"""

        if self.session and not self.session.closed:
            await self.session.close()
            print("🔌 Groq session closed")

    async def __aenter__(self):
        await self._get_session()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close_session()

    def __del__(self):
        if self.session and not self.session.closed:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.session.close())
            except:
                pass