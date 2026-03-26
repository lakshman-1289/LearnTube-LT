import sys
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi

print("YT-DLP Version:", yt_dlp.version.__version__)

url = "https://www.youtube.com/watch?v=O2gerCxEXvc"
video_id = "O2gerCxEXvc"

print("Testing YoutubeTranscriptApi...")
try:
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    print("YTAPI Length:", len(transcript))
except Exception as e:
    print("YTAPI Failed:", type(e).__name__, str(e))

print("Testing yt-dlp...")
ydl_opts = {
    "writesubtitles": True,
    "writeautomaticsub": True,
    "subtitleslangs": ["en"],
    "skip_download": True,
    "quiet": True,
}
try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        subs = info.get("subtitles") or info.get("automatic_captions")
        if subs and "en" in subs:
            print("YT-DLP Subs URL found:", subs["en"][0]["url"][:50], "...")
        else:
            print("YT-DLP No english subtitles found in info dict.")
except Exception as e:
    print("YT-DLP Failed:", type(e).__name__, str(e))
