# LearnTube Frontend

This is the Next.js frontend for the LearnTube application. It connects to the LearnTube FastAPI backend to generate interactive courses and quizzes directly from YouTube videos.

## Features
- **YouTube Course Generation:** Paste a video link to automatically extract transcripts and generate lessons.
- **Interactive Learning UI:** Browse through chapters, view synthesized notes, and watch the original video segments.
- **Dynamic Quizzes:** Take quizzes auto-generated from the video's content to test your understanding.

---

## Prerequisites
To run the full end-to-end application, ensure you have the following installed:
1. **Node.js** (v18 or higher recommended)
2. **Python** (for script execution)
3. **LearnTube Backend:** The FastAPI backend must be running locally. 

---

## How to Run & Test

### 1. Start the FastAPI Backend
Ensure your Python backend is running. Typically, this is done from your backend directory:
```bash
# Navigate to your backend directory
cd path/to/backend

# Activate virtual environment (if used)
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Run the server (e.g., via uvicorn)
uvicorn main:app --reload --port 8000
```
*Note: Make sure it is running on `http://localhost:8000` because the frontend API routes proxy generation requests to `http://localhost:8000/generate-course`.*

### 2. Start the Frontend
In this `frontend` directory, install the dependencies and start the Next.js development server:

```bash
# Install dependencies
npm install

# Start the development server
npm run dev
```

### 3. Test End-to-End
1. Open your browser and navigate to [http://localhost:3000](http://localhost:3000).
2. You will see the **LearnTube** homepage.
3. In the input box under "Generate Settings", paste a valid YouTube URL (e.g., `https://www.youtube.com/watch?v=...`).
4. Click **Generate**.
5. The application will redirect to the `/learning?url=...` page and display a loading spinner.
6. Once the backend finishes extracting the transcript and generating the content, the generated course (lessons, video segments, notes, and quizzes) will be displayed interactively in the UI.

---

## Current Architecture Updates
- **Simplified UI:** Authentication requirements have been removed for a streamlined testing experience.
- **Direct Backend Integration:** The course generation mechanism bypasses local mock data and relies entirely on the monolithic Python backend responding with course structure data (`courseInfo`, `lessons`, `quizzes`, etc).

> **Note:** Error states are comprehensively handled. If the backend is unreachable or parsing fails, an error will be displayed directly within the learning UI.
