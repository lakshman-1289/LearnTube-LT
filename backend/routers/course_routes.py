from fastapi import APIRouter, HTTPException
import os

from services.transcript_service import extract_transcript
from services.chapter_service import generate_chapters
from course_generator.src.core.courseGenerator import CourseGenerator
from llm.factory import LLMFactory
from services.db_service import db_service

router = APIRouter()

def log(msg):
    print(f"[LOG] {msg}")

@router.post("/generate-course-from-youtube")
async def generate_course_from_youtube(body: dict):
    """
    Check cache -> Extract transcript -> generate chapters -> generate course -> cache.
    Returns the combined response with chapters and course data.
    """
    try:
        url = body.get("url") or body.get("youtube_url")
        if not url:
            raise Exception("Missing 'url' or 'youtube_url'")

        log(f"Processing video: {url}")
        
        # We need video ID for cache check. Simplistic extraction.
        # In production this might use a safer regex.
        import re
        video_id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
        video_id = video_id_match.group(1) if video_id_match else url

        # 0. Check MongoDB Cache First
        cached_course = await db_service.get_cached_course(video_id)
        if cached_course:
            log("Returning cached course early.")
            return {
                "success": True,
                "course_data": cached_course.get("course_data"),
                "processing_stats": {"cache_hit": True},
                "video_id": cached_course.get("video_id"),
                "title": cached_course.get("title"),
                "transcript_length": cached_course.get("transcript_length"),
                "chapters": cached_course.get("chapters", []),
            }

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
        chapter_data = [{"title": c.title, "time": c.time} for c in chapters]

        # 3. Generate Course pipeline using CourseGenerator Orchestrator
        log("Generating course...")
            
        llm_client = None
        try:
            llm_client = LLMFactory.create_provider()
            course_generator = CourseGenerator(llm_client)
            
            course_data = await course_generator.generate_complete_course(
                transcript_text=transcript_text,
                video_title=transcript_result["title"],
                video_url=url
            )
            
            if isinstance(course_data, dict) and "error" in course_data:
                raise Exception(course_data.get("error", "Course generation failed"))
                
        except Exception as e:
            raise Exception(f"Course generation failed: {str(e)}")
        finally:
            if llm_client:
                await llm_client.async_close()

        # 4. Save to DB Cache
        transcript_len = len(transcript_text)
        await db_service.cache_course(
            video_id=transcript_result["videoId"],
            youtube_url=url,
            title=transcript_result["title"],
            transcript_length=transcript_len,
            chapters=chapter_data,
            course_data=course_data
        )

        # 5. Return combined response
        log("Course generation successful.")
        result = {
            "success": True,
            "course_data": course_data,
            "processing_stats": {"cache_hit": False},
            "video_id": transcript_result["videoId"],
            "title": transcript_result["title"],
            "transcript_length": transcript_len,
            "chapters": chapter_data,
        }
        return result

    except Exception as e:
        print(f"[FATAL ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))
