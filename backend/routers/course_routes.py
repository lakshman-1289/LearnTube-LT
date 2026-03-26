from fastapi import APIRouter, HTTPException
import os

from services.transcript_service import extract_transcript
from services.chapter_service import generate_chapters
from course_generator.src.core.courseGenerator import CourseGenerator
from course_generator.src.core.transcript_processor import TranscriptProcessor
from course_generator.src.core.groq_client import GroqClient

router = APIRouter()

def log(msg):
    print(f"[LOG] {msg}")

@router.post("/generate-course-from-youtube")
async def generate_course_from_youtube(body: dict):
    """
    Extract transcript -> generate chapters -> generate course.
    Returns the combined response with chapters and course data.
    Wrapped safely for production.
    """
    try:
        url = body.get("url") or body.get("youtube_url")
        if not url:
            raise Exception("Missing 'url' or 'youtube_url'")

        log(f"Processing video: {url}")
        
        # 1. Extract transcript and segments
        log("Extracting transcript...")
        transcript_result = extract_transcript(url)
        
        # Check if the fallback hit the final fail state
        if transcript_result and transcript_result.get("error") and not transcript_result.get("transcript"):
            log("No captions available via any extraction layer.")
            return {
                "success": False,
                "error": "This video has no accessible captions. Please try another video.",
                "course_data": None,
                "processing_stats": None,
                "video_id": transcript_result.get("videoId", ""),
                "title": "",
                "transcript_length": 0,
                "chapters": [],
            }
            
        if not transcript_result or not transcript_result.get("transcript"):
            raise Exception("Transcript extraction failed at API step")
            
        transcript_text = transcript_result["transcript"]
        if len(transcript_text.strip()) < 100:
            raise Exception("Transcript too short or empty for course generation.")

        # 2. Generate chapters
        log("Generating chapters...")
        segments = transcript_result.get("segments", [])
        chapters = generate_chapters(segments) if segments else []

        # 3. Generate Course using CourseGenerator
        log("Generating course...")
        processor = TranscriptProcessor()
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise Exception("GROQ_API_KEY not found in environment variables.")
            
        groq_client = None
        try:
            groq_client = GroqClient(api_key=groq_api_key)
            course_generator = CourseGenerator(groq_client, processor)
            
            transcript_json = {"content": transcript_text}
            if not processor.validate_transcript(transcript_json):
                raise Exception("Invalid transcript content after extraction")
            
            enhanced_transcript = processor.enhance_transcript_quality(transcript_json)
            course_data = await course_generator.generate_complete_course(enhanced_transcript, transcript_result["title"])
            
            if isinstance(course_data, dict) and "error" in course_data:
                raise Exception(course_data.get("error", "Course generation failed"))
                
        except Exception as e:
            raise Exception(f"Course generation failed: {str(e)}")
        finally:
            if groq_client and hasattr(groq_client, 'session') and groq_client.session:
                await groq_client.session.close()

        # 4. Return combined response
        log("Course generation successful.")
        result = {
            "success": True,
            "course_data": course_data,
            "processing_stats": None,
            "video_id": transcript_result["videoId"],
            "title": transcript_result["title"],
            "transcript_length": len(transcript_text),
            "chapters": [{"title": c.title, "time": c.time} for c in chapters],
        }
        return result

    except Exception as e:
        print(f"[FATAL ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))
