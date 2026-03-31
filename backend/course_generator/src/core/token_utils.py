"""Token utilities: token counting using tiktoken when available, with safe fallback.

This module centralizes token estimation so other parts (chunker, requesters)
can share the same logic without circular imports.
"""
from typing import Optional
try:
    import tiktoken
    ENCODER = tiktoken.get_encoding("cl100k_base")
except Exception:
    ENCODER = None


def count_tokens(text: str) -> int:
    """Estimate tokens for a text. Uses tiktoken when available, else chars/4 heuristic.

    This function is conservative when tiktoken is not available.
    """
    if not text:
        return 0
    if ENCODER:
        try:
            return len(ENCODER.encode(text))
        except Exception:
            # Fall back to heuristic on unexpected encoder errors
            pass
    return max(0, len(text) // 4)
