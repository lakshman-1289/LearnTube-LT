from fastapi import APIRouter, HTTPException
import os

from services.transcript_service import extract_transcript
from services.chapter_service import generate_chapters
from course_generator.src.core.courseGenerator import CourseGenerator
from course_generator.src.core.transcript_processor import TranscriptProcessor
from course_generator.src.core.groq_client import GroqClient

router = APIRouter()

@router.post("/generate-course-from-youtube")
async def generate_course_from_youtube(body: dict):
    """
    Extract transcript -> generate chapters -> generate course.
    Returns the combined response with chapters and course data.
    """
    url = body.get("url") or body.get("youtube_url")
    if not url:
        raise HTTPException(status_code=400, detail="Missing 'url' or 'youtube_url'")

    # 1. Extract transcript and segments
    try:
        transcript_result = extract_transcript(url)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcript extraction failed: {e}")

    transcript_text = transcript_result["transcript"]
    if not transcript_text or len(transcript_text.strip()) < 100:
        raise HTTPException(
            status_code=422,
            detail="Transcript too short or empty for course generation.",
        )

    # 2. Generate chapters
    segments = transcript_result["segments"]
    chapters = generate_chapters(segments) if segments else []

    # 3. Generate Course using CourseGenerator
    try:
        # Initialize components exactly as in old course generator main.py
        processor = TranscriptProcessor()
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise HTTPException(status_code=500, detail="GROQ_API_KEY not found in environment variables.")
            
        groq_client = GroqClient(api_key=groq_api_key)
        course_generator = CourseGenerator(groq_client, processor)
        
        # Format the transcript for the processor
        transcript_json = {"content": transcript_text}
        
        # Validate and enhance
        if not processor.validate_transcript(transcript_json):
            raise HTTPException(status_code=400, detail="Invalid transcript content after extraction")
        
        enhanced_transcript = processor.enhance_transcript_quality(transcript_json)
        
        # Generate complete course structure
        course_data = await course_generator.generate_complete_course(enhanced_transcript, transcript_result["title"])
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Important to close groq client session
        if hasattr(groq_client, 'session') and groq_client.session:
            await groq_client.session.close()

    # 4. Return combined response (matching exact expected format)
    # The new CourseResponse includes success, course_data, processing_stats, etc.
    # We construct the final payload combining extraction info and course_data.
    
    # Check if there was an error embedded in course_data
    if isinstance(course_data, dict) and "error" in course_data:
        raise HTTPException(
            status_code=500,
            detail=course_data.get("error", "Course generation failed")
        )

    # Note: course_generator.generate_complete_course returns the raw course dict
    # We wrap it in the expected format.
    return {
        "success": True,
        "course_data": course_data,
        "processing_stats": None, # Could be calculated, omitted for simplicity
        "video_id": transcript_result["videoId"],
        "title": transcript_result["title"],
        "transcript_length": len(transcript_text),
        "chapters": [{"title": c.title, "time": c.time} for c in chapters],
    }
