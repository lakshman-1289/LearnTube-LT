import re
import json
import os
import tempfile
import subprocess
import requests
import time
from typing import Optional, Dict, Any

from models.schemas import TranscriptSegment
from utils.youtube_utils import extract_video_id, clean_text


# ---------------- GLOBAL SESSION ----------------
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9"
})


def safe_request(url):
    for i in range(3):
        try:
            return session.get(url, timeout=10)
        except Exception as e:
            print(f"[Retry {i}] {e}")
            time.sleep(2)
    return None


# ---------------- STRATEGY 1 ----------------
def _get_transcript_youtube_api(video_id: str, lang="en"):
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        transcript_list = YouTubeTranscriptApi.list_transcripts(
            video_id,
            proxies={"http": None, "https": None}
        )

        try:
            transcript = transcript_list.find_manually_created_transcript([lang])
        except:
            try:
                transcript = transcript_list.find_generated_transcript([lang])
            except:
                available_generated = list(transcript_list._generated_transcripts.keys())
                if available_generated:
                    transcript = transcript_list.find_generated_transcript(available_generated)
                else:
                    available_manual = list(transcript_list._manually_created_transcripts.keys())
                    if available_manual:
                        transcript = transcript_list.find_manually_created_transcript(available_manual)
                    else:
                        return None

        data = transcript.fetch()

        segments = [
            {"start": seg["start"], "text": seg.get("text", "").strip()}
            for seg in data if seg.get("text")
        ]

        if not segments:
            return None

        return {
            "source": "youtube_transcript_api",
            "language": transcript.language_code,
            "is_generated": transcript.is_generated,
            "segments": segments,
            "transcript": clean_text(" ".join(s["text"] for s in segments)),
        }

    except Exception as e:
        print("[ERROR] youtube-transcript-api:", e)
        return None


# ---------------- STRATEGY 2 ----------------
def _get_transcript_timedtext(video_id: str, lang="en"):
    try:
        url = f"https://video.google.com/timedtext?v={video_id}&lang={lang}"
        resp = safe_request(url)

        if not resp or not resp.text.strip():
            return None

        import xml.etree.ElementTree as ET
        root = ET.fromstring(resp.text)

        segments = []
        for child in root:
            text = child.text.strip() if child.text else ""
            if text:
                segments.append({
                    "start": float(child.attrib.get("start", 0)),
                    "text": text
                })

        if not segments:
            return None

        return {
            "source": "timedtext",
            "language": lang,
            "is_generated": True,
            "segments": segments,
            "transcript": clean_text(" ".join(s["text"] for s in segments)),
        }

    except Exception as e:
        print("[ERROR] timedtext:", e)
        return None


# ---------------- STRATEGY 3 ----------------
def _get_transcript_ytdlp(video_id: str, lang="en"):
    import yt_dlp

    try:
        ydl_opts = {
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": [lang],
            "skip_download": True,
            "quiet": True,
            "socket_timeout": 15,

            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "web"]
                }
            },

            # ✅ FIXED FORMAT
            "js_runtimes": {
                "node": {}
            }
        }

        url = f"https://www.youtube.com/watch?v={video_id}"

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        all_subs = info.get("subtitles") or {}
        auto_subs = info.get("automatic_captions") or {}
        
        merged_subs = {}
        merged_subs.update(auto_subs)
        merged_subs.update(all_subs)

        if not merged_subs:
            return None

        # Fuzzy match for the requested language (e.g. 'en', 'en-US', 'en-GB')
        sub_url = None
        detected_lang = lang
        for key in merged_subs.keys():
            if key == lang or key.startswith(lang + "-"):
                sub_url = merged_subs[key][0]["url"]
                detected_lang = key
                break

        if not sub_url and merged_subs:
            # fallback to any available language
            detected_lang = list(merged_subs.keys())[0]
            sub_url = merged_subs[detected_lang][0]["url"]

        if not sub_url:
            return None
        resp = safe_request(sub_url)

        if not resp:
            return None

        try:
            data = resp.json()
            segments = []
            for event in data.get("events", []):
                if "segs" not in event:
                    continue

                text = "".join(seg.get("utf8", "") for seg in event["segs"]).strip()
                if text:
                    segments.append({
                        "start": event.get("tStartMs", 0) / 1000,
                        "text": text
                    })

            if segments:
                return {
                    "source": "yt-dlp",
                    "language": detected_lang,
                    "is_generated": True,
                    "segments": segments,
                    "transcript": clean_text(" ".join(s["text"] for s in segments)),
                }
            return None
        except:
            print("[WARN] yt-dlp parsing json failed, trying text fallback")
            
            import re
            lines = resp.text.split('\n')
            temp_text = ""
            for line in lines:
                line = line.strip()
                if not line or "-->" in line or line.startswith("WEBVTT") or line.isdigit() or line.startswith("Kind:") or line.startswith("Language:"):
                    continue
                clean_line = re.sub(r'<[^>]+>', '', line)
                if clean_line:
                    temp_text += " " + clean_line

            text_content = clean_text(temp_text) if temp_text else clean_text(resp.text)
            
            if not text_content:
                return None
                
            segments = [{"start": 0, "text": text_content, "duration": 0}]
            
            return {
                "source": "yt-dlp",
                "language": detected_lang,
                "is_generated": True,
                "segments": segments,
                "transcript": text_content,
            }

    except Exception as e:
        print("[ERROR] yt-dlp:", e)
        return None





def _get_video_title_ytdlp(video_id: str) -> str:
    """Get video title using yt-dlp (no download)."""
    try:
        import sys
        import subprocess
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


# ---------------- ASR FALLBACK ----------------
def _get_transcript_asr(video_id: str, lang="en") -> Optional[Dict[str, Any]]:
    import sys
    import shutil
    
    if not shutil.which("ffmpeg"):
        print("[WARN] ffmpeg not found, skipping ASR fallback")
        return None

    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            raw_audio = os.path.join(temp_dir, "raw_audio.%(ext)s")
            raw_audio_mp3 = raw_audio.replace("%(ext)s", "mp3")
            trimmed_audio = os.path.join(temp_dir, "trimmed_audio.mp3")

            dl_cmd = [
                sys.executable, "-m", "yt_dlp",
                "-x",
                "--audio-format", "mp3",
                "-o", raw_audio,
                url
            ]
            subprocess.run(dl_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

            trim_cmd = [
                "ffmpeg",
                "-y",
                "-i", raw_audio_mp3,
                "-t", "600",
                "-c", "copy",
                trimmed_audio
            ]
            subprocess.run(trim_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

            from faster_whisper import WhisperModel
            model = WhisperModel("tiny", compute_type="int8")
            segments_gen, _ = model.transcribe(trimmed_audio)

            segments = []
            for seg in segments_gen:
                if seg.text and seg.text.strip():
                    segments.append({
                        "start": seg.start,
                        "text": seg.text.strip()
                    })

            if not segments:
                return None

            return {
                "source": "asr_fallback",
                "language": lang,
                "is_generated": True,
                "segments": segments,
                "transcript": clean_text(" ".join(s["text"] for s in segments)),
            }
    except Exception as e:
        print(f"[ERROR] asr_fallback: {e}")
        return None


# ---------------- MAIN FUNCTION ----------------
def extract_transcript(youtube_url: str, lang="en"):

    video_id = extract_video_id(youtube_url)
    title = _get_video_title_ytdlp(video_id)

    for func in [
        _get_transcript_youtube_api,
        _get_transcript_timedtext,
        _get_transcript_ytdlp,
        _get_transcript_asr,
    ]:
        result = func(video_id, lang)
        if result and result.get("segments"):
            print(f"[INFO] Using transcript source: {result['source']}")
            print(f"[INFO] Detected language: {result.get('language', lang)}")
            return _format_output(video_id, result, title)

    print("[WARN] All methods failed to extract transcript.")
    return {
        "videoId": video_id,
        "title": title,
        "metadata": {
            "source": "none",
            "language": lang,
            "is_generated": False,
        },
        "segments": [],
        "transcript": "",
    }


def _format_output(video_id, result, title):
    return {
        "videoId": video_id,
        "title": title,
        "metadata": {
            "source": result["source"],
            "language": result.get("language", "en"),
            "is_generated": result.get("is_generated", True),
        },
        "segments": [
            TranscriptSegment(start=s["start"], text=s["text"])
            for s in result["segments"]
        ],
        "transcript": result["transcript"],
    }