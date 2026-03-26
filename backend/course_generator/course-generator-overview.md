# Course Generator API (unchanged – consumed by Pipeline)

This service is called by the LearnTube Pipeline (`/generate-course-from-youtube`).
Do not modify; it provides `POST /generate-course` with `{ content: "<transcript>" }`.

Flow:
  main.py / test_api.py
     ↓
  CourseGenerator
     ↓
  GroqClient
     ↓
  Groq API
     ↓
  Llama-3 model