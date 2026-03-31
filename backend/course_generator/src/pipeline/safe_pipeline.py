import re
import os
import hashlib
import asyncio
from typing import List, Optional, Dict, Any

from course_generator.src.core.token_utils import count_tokens

from course_generator.src.services.groq_service import safe_groq_request


def _clean_text(text: str) -> str:
    text = re.sub(r'\b(um|uh|ah|like|you know)\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(gonna)\b', 'going to', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(wanna)\b', 'want to', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def smart_chunk_text(
    text: str,
    prompt_template: str,
    max_input_tokens: int = 8000,
    max_output_tokens: int = 1000,
    buffer_tokens: int = 50,
    min_chunk_tokens: int = 200,
) -> List[str]:
    """
    Token-aware, sentence-preserving chunking.

    Ensures that for each chunk, token_count(prompt_without_transcript) + token_count(chunk) + max_output_tokens + buffer_tokens <= max_input_tokens
    """
    if '{transcript}' not in prompt_template:
        raise ValueError("prompt_template must contain '{transcript}' placeholder")

    cleaned = _clean_text(text)
    sentences = re.split(r'(?<=[.!?])\s+', cleaned)

    # Estimate prompt overhead
    prompt_overhead = prompt_template.replace('{transcript}', '')
    overhead_tokens = count_tokens(prompt_overhead)

    max_allowed_for_chunk = max(0, max_input_tokens - overhead_tokens - max_output_tokens - buffer_tokens)

    chunks: List[str] = []
    current_sentences: List[str] = []
    current_tokens = 0

    for s in sentences:
        if not s.strip():
            continue
        s_tokens = count_tokens(s)

        # If single sentence too big, split at word boundaries
        if s_tokens > max_allowed_for_chunk and max_allowed_for_chunk > 0:
            words = s.split()
            acc = []
            acc_tokens = 0
            for w in words:
                wt = count_tokens(w + ' ')
                if acc_tokens + wt > max_allowed_for_chunk:
                    break
                acc.append(w)
                acc_tokens += wt

            truncated = ' '.join(acc).rstrip()
            if truncated:
                # flush current
                if current_sentences:
                    chunks.append(' '.join(current_sentences))
                    current_sentences = []
                    current_tokens = 0
                chunks.append(truncated + '...')
            # continue with remaining words as separate sentence parts
            continue

        # Normal packing
        if current_tokens + s_tokens > max_allowed_for_chunk and current_sentences:
            chunks.append(' '.join(current_sentences))
            current_sentences = [s]
            current_tokens = s_tokens
        else:
            current_sentences.append(s)
            current_tokens += s_tokens

    if current_sentences:
        chunks.append(' '.join(current_sentences))

    # Merge tiny chunks
    merged: List[str] = []
    for c in chunks:
        if not merged:
            merged.append(c)
            continue
        if count_tokens(merged[-1]) < min_chunk_tokens:
            merged[-1] = merged[-1] + ' ' + c
        else:
            merged.append(c)

    # Debug: print chunk token counts
    for i, c in enumerate(merged):
        print(f"[CHUNKER] Chunk {i+1}/{len(merged)} tokens={count_tokens(c)} chars={len(c)}")

    return merged


# Simple in-memory cache for summaries keyed by sha256(text)
_summary_cache: Dict[str, str] = {}


async def summarize_chunks(
    groq_client,
    chunks: List[str],
    summary_max_tokens: int = 300,
    summary_prompt: Optional[str] = None,
    reuse_cache: bool = True,
) -> List[str]:
    """
    Summarize each chunk into a concise summary (token-bounded). Uses groq_client for requests.
    Caches results in-memory to avoid redundant API calls.
    """
    if summary_prompt is None:
        summary_prompt = (
            "You are a concise summarizer. Produce a short, factual summary of the transcript chunk."
            " Return only plain text summary, about 150-300 words."
            " Do NOT include commentary or instructions.\n\nChunk:\n{transcript}"
        )

    results: List[str] = []

    for i, chunk in enumerate(chunks):
        key = hashlib.sha256(chunk.encode('utf-8')).hexdigest()
        if reuse_cache and key in _summary_cache:
            print(f"[SUMMARIZER] Cache hit for chunk {i+1}")
            results.append(_summary_cache[key])
            continue

        prompt = summary_prompt.format(transcript=chunk)

        messages = [
            {"role": "system", "content": "You are a helpful summarization assistant."},
            {"role": "user", "content": prompt}
        ]

        # Debug log token counts
        total_tokens_est = count_tokens(prompt) + summary_max_tokens
        print(f"[SUMMARIZER] Sending chunk {i+1}/{len(chunks)} tokens_est={total_tokens_est}")

        # Call Groq safely via central safe_groq_request (robust retry + rate limiting)
        resp_text = await safe_groq_request(
            prompt=prompt,
            model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
            max_tokens=summary_max_tokens,
            temperature=0.0,
            token_limit=2000,
            stage_context=f"summarize_chunk_{i+1}",
        )

        # resp_text is plain text summary
        _summary_cache[key] = resp_text.strip()
        results.append(resp_text.strip())

    return results


# safe_groq_request is implemented centrally in services.groq_service.safe_groq_request
