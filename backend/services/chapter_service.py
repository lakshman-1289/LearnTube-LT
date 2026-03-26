"""
Generate chapter timestamps from transcript segments using semantic embeddings
and similarity thresholds to detect topic shifts.
"""
import re
from typing import List, Optional

from models.schemas import TranscriptSegment, ChapterItem


# Minimum words per block to avoid tiny segments
MIN_WORDS_PER_BLOCK = 15
# Gap in seconds between segments that suggests a natural break
PAUSE_GAP_SECONDS = 2.0
# Similarity below this threshold suggests a topic shift (tune as needed)
SIMILARITY_THRESHOLD = 0.5


def _merge_segments_into_blocks(
    segments: List[TranscriptSegment],
    min_words: int = MIN_WORDS_PER_BLOCK,
    pause_gap: float = PAUSE_GAP_SECONDS,
) -> List[dict]:
    """
    Merge small transcript segments into paragraph-like blocks.
    Uses pause gaps as additional split points.
    """
    if not segments:
        return []

    blocks = []
    current_text: List[str] = []
    current_start = segments[0].start
    prev_end = segments[0].start

    for seg in segments:
        gap = seg.start - prev_end
        if gap >= pause_gap and current_text:
            block_text = " ".join(current_text).strip()
            if block_text and len(block_text.split()) >= min_words:
                blocks.append({
                    "start": current_start,
                    "text": block_text,
                })
            current_text = []
            current_start = seg.start

        current_text.append(seg.text.strip())
        prev_end = seg.start + 0.1  # approximate end

    if current_text:
        block_text = " ".join(current_text).strip()
        if block_text:
            blocks.append({"start": current_start, "text": block_text})

    return blocks


def _get_embeddings(texts: List[str], model_name: str = "all-MiniLM-L6-v2"):
    """Compute sentence embeddings using sentence-transformers."""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(model_name)
        return model.encode(texts, show_progress_bar=False)
    except Exception:
        return None


def _cosine_similarity(a, b) -> float:
    """Cosine similarity between two vectors."""
    import numpy as np
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


def _detect_chapter_boundaries(
    blocks: List[dict],
    threshold: float = SIMILARITY_THRESHOLD,
) -> List[dict]:
    """
    Detect topic shifts by comparing adjacent block embeddings.
    Returns list of chapter starts: [{"start": time, "text": block_text}, ...].
    """
    if not blocks or len(blocks) <= 1:
        return [{"title": blocks[0]["text"][:80] + ("..." if len(blocks[0]["text"]) > 80 else ""), "time": blocks[0]["start"]}] if blocks else []

    texts = [b["text"] for b in blocks]
    embeddings = _get_embeddings(texts)
    if embeddings is None:
        # Fallback: use first block and every N blocks as chapters
        chapters = [{"title": _summarize_title(blocks[0]["text"]), "time": blocks[0]["start"]}]
        step = max(1, len(blocks) // 5)
        for i in range(step, len(blocks), step):
            chapters.append({"title": _summarize_title(blocks[i]["text"]), "time": blocks[i]["start"]})
        return chapters

    import numpy as np
    chapters = [{"title": _summarize_title(blocks[0]["text"]), "time": blocks[0]["start"]}]
    for i in range(1, len(blocks)):
        sim = _cosine_similarity(embeddings[i - 1], embeddings[i])
        if sim < threshold:
            chapters.append({"title": _summarize_title(blocks[i]["text"]), "time": blocks[i]["start"]})

    return chapters


def _summarize_title(text: str, max_words: int = 8) -> str:
    """Create a short chapter title from block text (first few words or cleaned)."""
    text = re.sub(r"\s+", " ", text).strip()
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "..."


def generate_chapters(segments: List[TranscriptSegment]) -> List[ChapterItem]:
    """
    Merge segments into blocks, detect topic shifts via embeddings,
    and return chapter timestamps with titles.
    """
    if not segments:
        return []

    blocks = _merge_segments_into_blocks(segments)
    if not blocks:
        return []

    chapter_dicts = _detect_chapter_boundaries(blocks)
    return [ChapterItem(title=c["title"], time=c["time"]) for c in chapter_dicts]
