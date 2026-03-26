# LearnTube Modular Monolith Backend

This is the consolidated backend service for LearnTube. It combines transcript extraction, chapter generation, and AI-powered course generation into a single modular FastAPI application.

## Directory Structure
- `main.py`: The FastAPI application entry point. Contains the app setup, middleware, and health check.
- `routers/`: Contains all the API routes.
  - `course_routes.py`: The primary router holding the `/generate-course-from-youtube` endpoint.
- `services/`: Contains the core logic decoupled from the routers.
  - `transcript_service.py`: Logic for extracting transcripts via YouTube API, timedtext, and yt-dlp.
  - `chapter_service.py`: Logic for grouping transcript segments and generating semantic chapters.
- `course_generator/`: The completely preserved internal logic and module for AI course generation via Groq.
- `models/`: Contains Pydantic schemas.
  - `schemas.py`: Data models such as `TranscriptRequest`, `ChapterItem`, `CourseGeneratorInput`.
- `utils/`: Contains helper functions.
  - `youtube_utils.py`: Helpers for basic operations like URL parsing and text cleaning.

## Setup & Running

1. **Install Requirements**
   Ensure you have all dependencies installed from the unified `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables**
   Ensure you have a `.env` file in the root directory (or in `backend/`) containing your `GROQ_API_KEY`:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

3. **Run the Backend**
   From the main project root, run the application using Uvicorn:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **API Endpoints**

   Below is a detailed list of available endpoints. You can test them using `curl`, Postman, or Thunder Client.

   **Health Check**: 
   Ensure the server is running by hitting the root health endpoint.
   ```bash
   curl http://localhost:8000/health
   ```
   **Expected Response:**
   ```json
   {
     "status": "healthy",
     "service": "LearnTube Backend"
   }
   ```

   **Generate Course**: 
   This is the primary endpoint that processes a YouTube URL, fetches transcripts, creates chapter chunks, and builds the course using the Groq AI model.
   
   Replace `https://www.youtube.com/watch?v=EXAMPLE_ID` with a real video URL.

   ```bash
   curl -X POST http://localhost:8000/generate-course-from-youtube \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.youtube.com/watch?v=EXAMPLE_ID"}'
   ```
   
   Alternatively, using PowerShell (Windows):
   ```powershell
   Invoke-RestMethod -Uri "http://localhost:8000/generate-course-from-youtube" `
     -Method Post `
     -Headers @{"Content-Type"="application/json"} `
     -Body '{"url": "https://www.youtube.com/watch?v=EXAMPLE_ID"}'
   ```
   
   **Expected Response Structure:**
   ```json
   {
     "success": true,
     "course_data": { ...course JSON structure... },
     "processing_stats": null,
     "video_id": "EXAMPLE_ID",
     "title": "Video Title",
     "transcript_length": 5000,
     "chapters": [
       {"title": "Introduction", "time": 0.0},
       {"title": "Main Topic", "time": 125.5}
     ]
   }
   ```

## Refactoring Note
This backend replaces the formerly separate `pipeline_service`, `transcript_service`, `chapter_service`, and `course-generator-api` directories to remove unnecessary internal HTTP calls and `sys.path` manipulations. It enforces a clean modular monolithic design.
