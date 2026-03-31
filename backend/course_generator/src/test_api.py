from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
import traceback
from models.schemas import CourseGeneratorInput

# Now import your modules
from course_generator.src.core.transcript_processor import TranscriptProcessor
from course_generator.src.core.courseGenerator import CourseGenerator
from llm.factory import LLMFactory

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

app = FastAPI(title="YouTube Course Generator Test API", version="1.0.0")

# Enable CORS for testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TranscriptInput(BaseModel):
    content: str

class CourseResponse(BaseModel):
    success: bool
    course_data: dict = None
    error: str = None
    processing_stats: dict = None

# Initialize components
processor = TranscriptProcessor()
client = LLMFactory.create_provider()
course_generator = CourseGenerator(client)

@app.post("/generate-course", response_model=CourseResponse)
async def generate_course_from_transcript(transcript: CourseGeneratorInput):
    """
    Test endpoint: Convert transcript JSON to complete course structure
    """
    try:
        # Input validation
        transcript_json = {"content": transcript.content}
        if not processor.validate_transcript(transcript_json):
            raise HTTPException(status_code=400, detail="Invalid transcript content")
        
        # Process through your complete pipeline
        start_time = time.time()
        course_data = await course_generator.generate_complete_course(transcript_json)
        processing_time = time.time() - start_time
        
        # Processing statistics
        stats = {
            "processing_time_seconds": round(processing_time, 2),
            "input_tokens": processor.count_tokens(transcript.content),
            "output_size_kb": round(len(json.dumps(course_data)) / 1024, 2),
            "lessons_generated": len(course_data.get("lessons", [])),
            "total_quizzes": sum(len(lesson.get("quizzes", [])) for lesson in course_data.get("lessons", []))
        }
        
        # Validate that we have actual course structure, not just analysis
        if "courseInfo" not in course_data or "lessons" not in course_data:
            return CourseResponse(
                success=False,
                error="Generated data is not in proper course format"
            )
        
        return CourseResponse(
            success=True,
            course_data=course_data,
            processing_stats=stats
        )
    except Exception as e:
        return CourseResponse(
            success=False,
            error=str(e)
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Course Generator API"}

@app.post("/test-llm")
async def test_llm_connection():
    try:
        # Check if the provider has a test connection module
        if hasattr(client, 'test_connection') and callable(client.test_connection):
            return await client.test_connection()
        return {"success": True, "response": "LLM API reachable", "provider": "LLMFactory"}
    except Exception as e:
        print("ERROR OCCURRED:")
        traceback.print_exc()
        return {"success": False, "error": str(e)}

        
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
