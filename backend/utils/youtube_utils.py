import re

def extract_video_id(url: str) -> str:
    """Extract videoId from various YouTube URL formats."""
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11})",
        r"youtu\.be/([0-9A-Za-z_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError("Invalid YouTube URL")

def clean_text(text: str) -> str:
    """Remove extra whitespace and normalize transcript text."""
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    return text.strip()
