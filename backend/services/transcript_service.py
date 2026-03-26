"""
Hybrid transcript extraction: InnerTube/captions metadata -> timedtext -> yt-dlp.
Returns structured segments with timestamps and full transcript text.
"""
import re
import json
import os
import tempfile
import subprocess
from typing import List, Optional, Dict, Any

from models.schemas import TranscriptSegment
from utils.youtube_utils import extract_video_id, clean_text


# --- Strategy 1: YouTube Transcript API (uses same data as captions / InnerTube) ---
def _get_transcript_youtube_api(video_id: str, lang: str = "en") -> Optional[Dict[str, Any]]:
    """
    Try to get captions via youtube-transcript-api.
    This library retrieves caption track metadata (similar to InnerTube player API)
    and fetches the timedtext content.
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api._errors import (
            TranscriptsDisabled,
            NoTranscriptFound,
            VideoUnavailable,
        )

        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        try:
            transcript = transcript_list.find_transcript([lang])
        except NoTranscriptFound:
            transcript = transcript_list.find_generated_transcript([lang])

        entries = transcript.fetch()
        segments = [
            {"start": entry["start"], "text": entry.get("text", "").strip()}
            for entry in entries
            if entry.get("text")
        ]
        full_text = " ".join(s["text"] for s in segments)
        return {
            "source": "youtube_transcript_api",
            "language": transcript.language_code,
            "is_generated": getattr(transcript, "is_generated", False),
            "segments": segments,
            "transcript": clean_text(full_text),
        }
    except Exception as e:
        print("youtube_transcript_api error:", e)
        import traceback
        traceback.print_exc()
        return None


# --- Strategy 2: Timedtext URL (direct fetch when we have a track URL) ---
def _get_transcript_timedtext_url(video_id: str, lang: str = "en") -> Optional[Dict[str, Any]]:
    """
    Try to get caption track URL from player response and fetch timedtext (json3).
    Fallback when youtube_transcript_api fails (e.g. region restrictions).
    """
    try:
        import requests

        # Get player response that contains caption tracks (InnerTube-style)
        # Get player response that contains caption tracks (InnerTube-style)
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Connection": "keep-alive"
        })

        url = f"https://www.youtube.com/watch?v={video_id}"
        resp = session.get(url, timeout=30)
        if resp.status_code != 200:
            return None

        # Find caption track list in player response (embedded in page)
        match = re.search(r'"captionTracks":\s*(\[.*?\])', resp.text)
        if not match:
            return None

        import json as _json
        try:
            tracks = _json.loads(match.group(1))
        except _json.JSONDecodeError:
            return None

        base_url = None
        for track in tracks:
            if isinstance(track, dict):
                lc = track.get("languageCode") or track.get("vssId", "")
                if lc == lang or (lc and lang in lc) or (not base_url and track.get("baseUrl")):
                    base_url = track.get("baseUrl")
                    if base_url:
                        break
        if not base_url:
            base_url = tracks[0].get("baseUrl") if tracks else None
        if not base_url:
            return None

        # Fetch timedtext (json3 format)
        cap_resp = session.get(base_url, params={"fmt": "json3"}, timeout=15)
        if cap_resp.status_code != 200:
            return None

        data = cap_resp.json()
        events = data.get("events", [])
        segments = []
        for event in events:
            if "segs" not in event:
                continue
            start = event.get("tStartMs", 0) / 1000.0
            text = "".join(seg.get("utf8", "") for seg in event["segs"] if "utf8" in seg).strip()
            if text:
                segments.append({"start": start, "text": text})
        if not segments:
            return None
        full_text = " ".join(s["text"] for s in segments)
        return {
            "source": "timedtext",
            "language": lang,
            "is_generated": True,
            "segments": segments,
            "transcript": clean_text(full_text),
        }
    except Exception as e:
        print("TimedText extractor error:", e)
        import traceback
        traceback.print_exc()
        return None


# --- Strategy 3: yt-dlp (download subtitles) ---
def _get_transcript_ytdlp(video_id: str, lang: str = "en") -> Optional[Dict[str, Any]]:
    """
    Fallback: use yt-dlp to write auto-subs in json3 format and parse segments.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        out_tpl = os.path.join(tmpdir, "%(id)s.%(ext)s")
        import sys
        cmd = [
            sys.executable, "-m", "yt_dlp",
            f"https://www.youtube.com/watch?v={video_id}",
            "--write-auto-subs",
            "--sub-lang", lang,
            "--skip-download",
            "--sub-format", "json3",
            "-o", out_tpl,
            "--no-warnings",
            "-q",
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=120, cwd=tmpdir)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return None

        for fname in os.listdir(tmpdir):
            if fname.endswith(".json3"):
                path = os.path.join(tmpdir, fname)
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                events = data.get("events", [])
                segments = []
                for event in events:
                    if "segs" not in event:
                        continue
                    start = event.get("tStartMs", 0) / 1000.0
                    text = "".join(
                        seg.get("utf8", "") for seg in event["segs"] if "utf8" in seg
                    ).strip()
                    if text:
                        segments.append({"start": start, "text": text})
                if not segments:
                    return None
                full_text = " ".join(s["text"] for s in segments)
                return {
                    "source": "yt-dlp",
                    "language": lang,
                    "is_generated": True,
                    "segments": segments,
                    "transcript": clean_text(full_text),
                }
    return None


def _get_video_title_ytdlp(video_id: str) -> str:
    """Get video title using yt-dlp (no download)."""
    try:
        import sys
        cmd = [
            sys.executable, "-m", "yt_dlp",
            f"https://www.youtube.com/watch?v={video_id}",
            "--get-title",
            "--no-warnings",
            "-q",
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout:
            return result.stdout.strip()
    except Exception:
        pass
    return ""


def extract_transcript(youtube_url: str, lang: str = "en") -> Dict[str, Any]:
    """
    Hybrid extraction: try YouTube transcript API (captions), then timedtext URL, then yt-dlp.
    Returns dict with videoId, title, metadata, segments, transcript.
    Raises ValueError if no transcript can be retrieved.
    """
    video_id = extract_video_id(youtube_url)
    title = _get_video_title_ytdlp(video_id)

    result = _get_transcript_youtube_api(video_id, lang)
    if result and result.get("segments"):
        segments = [TranscriptSegment(start=s["start"], text=s["text"]) for s in result["segments"]]
        return {
            "videoId": video_id,
            "title": title,
            "metadata": {
                "source": result["source"],
                "language": result.get("language", lang),
                "is_generated": result.get("is_generated", False),
            },
            "segments": segments,
            "transcript": result["transcript"],
        }

    result = _get_transcript_timedtext_url(video_id, lang)
    if result and result.get("segments"):
        segments = [TranscriptSegment(start=s["start"], text=s["text"]) for s in result["segments"]]
        return {
            "videoId": video_id,
            "title": title,
            "metadata": {
                "source": result["source"],
                "language": result.get("language", lang),
                "is_generated": result.get("is_generated", False),
            },
            "segments": segments,
            "transcript": result["transcript"],
        }

    result = _get_transcript_ytdlp(video_id, lang)
    if result and result.get("segments"):
        segments = [TranscriptSegment(start=s["start"], text=s["text"]) for s in result["segments"]]
        return {
            "videoId": video_id,
            "title": title,
            "metadata": {
                "source": result["source"],
                "language": result.get("language", lang),
                "is_generated": result.get("is_generated", False),
            },
            "segments": segments,
            "transcript": result["transcript"],
        }

    raise ValueError(
        "No captions accessible for this video (tried captions API, timedtext, and yt-dlp)."
    )
