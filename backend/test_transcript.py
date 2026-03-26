import traceback
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the backend root to Python path
backend_root = Path(__file__).parent
sys.path.insert(0, str(backend_root))

env_path = backend_root / ".env"
load_dotenv(dotenv_path=env_path)

from services.transcript_service import (
    _get_transcript_youtube_api,
    _get_transcript_timedtext_url,
    _get_transcript_ytdlp,
)
from utils.youtube_utils import extract_video_id

url = "https://www.youtube.com/watch?v=A0pu92-pYhE&t=1s" # random video with captions
video_id = extract_video_id(url)
print(f"Testing Extractors for Video ID: {video_id}")
print("========================================")

print("\n[Method 1] Testing youtube-transcript-api...")
try:
    res1 = _get_transcript_youtube_api(video_id)
    if res1:
         print(f"SUCCESS: Method 1 returned transcript of length {len(res1['transcript'])}")
         print(f"Keys: {res1.keys()}")
    else:
         print("FAILED: Method 1 returned None. No stack trace triggered.")
except Exception as e:
    print(f"CRASHED: Method 1 raised exception: {e}")
    traceback.print_exc()

print("\n[Method 2] Testing Direct TimedText Scraping...")
try:
    res2 = _get_transcript_timedtext_url(video_id)
    if res2:
         print(f"SUCCESS: Method 2 returned transcript of length {len(res2['transcript'])}")
         print(f"Keys: {res2.keys()}")
    else:
         print("FAILED: Method 2 returned None. (Can happen if YouTube player format changed or CAPTCHA triggered).")
except Exception as e:
    print(f"CRASHED: Method 2 raised exception: {e}")
    traceback.print_exc()

print("\n[Method 3] Testing yt-dlp Subtitle Download...")
try:
    res3 = _get_transcript_ytdlp(video_id)
    if res3:
         print(f"SUCCESS: Method 3 returned transcript of length {len(res3['transcript'])}")
         print(f"Keys: {res3.keys()}")
    else:
         print("FAILED: Method 3 returned None.")
except Exception as e:
    print(f"CRASHED: Method 3 raised exception: {e}")
    traceback.print_exc()
