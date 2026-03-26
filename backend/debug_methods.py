import traceback
import sys

video_id = "qzq_-plz0bQ"

print("--- Testing youtube_transcript_api directly ---")
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    
    # List available transcripts
    print("Listing transcripts...")
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    print("Available transcripts:", transcript_list)
    
    # Try fetching English
    print("Fetching English transcript...")
    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
    print(f"Success! Length: {len(transcript)}")
except Exception as e:
    print("FAILED with Exception:")
    traceback.print_exc()

print("\n--- Testing Direct TimedText Scraping ---")
try:
    import requests
    import re
    import json
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    })
    url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"Fetching {url}")
    resp = session.get(url, timeout=15)
    print(f"Response Status: {resp.status_code}")
    print(f"Response Length: {len(resp.text)}")
    
    match = re.search(r'"captionTracks":\s*(\[.*?\])', resp.text)
    if not match:
        print("FAILED: No 'captionTracks' found in the page HTML. This usually means YouTube didn't embed the captions in the initial HTML (often due to bot protection, age restriction, or changes in their web layout).")
        # Check if consent formulation
        if "consent.youtube.com" in resp.text:
            print("Detected consent.youtube.com redirect! YouTube is blocking the request with a cookie/consent wall.")
    else:
        print("Caption tracks found!")
        try:
            tracks = json.loads(match.group(1))
            print("Tracks:", json.dumps(tracks, indent=2))
        except Exception as e:
            print("Valid JSON parse failed:", e)

except Exception as e:
    print("FAILED with Exception:")
    traceback.print_exc()
