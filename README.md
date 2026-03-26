# 📚 LearnTube – AI-Powered Dynamic Course Generator

## 🚀 Project Overview

**LearnTube** is an AI-powered learning platform that transforms any YouTube educational video into a structured, interactive course.

Many students cannot afford paid courses and rely on YouTube to learn. However, YouTube learning is often:

- Unstructured  

- Lacking documentation  

- Without assessments  

- Without certification  

- Hard to track progress  

LearnTube solves this problem by converting YouTube video content into a complete structured learning experience.

---

## 🎯 Problem Statement

Students who learn through YouTube face several challenges:

- No structured syllabus  

- No organized notes  

- No revision material  

- No progress tracking  

- No certification to prove learning  

- Difficulty identifying key concepts  

There is a gap between **free content availability** and **structured professional learning**.

---

## 💡 Proposed Solution

LearnTube allows a student to:

1. Enter a YouTube video URL  

2. Automatically extract the transcript  

3. Convert the transcript into:

   - Structured modules  

   - Clean documentation  

   - Key concepts  

   - Summaries  

   - Learning roadmap  

4. Generate a proficiency exam  

5. Provide certification upon successful completion  

The system dynamically creates a course for **any valid educational YouTube video**.

---

## 🧠 Key Features

- 🔗 YouTube URL to Course Conversion  

- 📄 Automatic Documentation Generation  

- 🧩 Smart Module Creation  

- 📝 AI-based Question Generation  

- 📊 Progress Tracking  

- 🏆 Certificate Generation  

- 🔐 Secure Authentication (Google OAuth / Credentials)  

- 📦 MongoDB-based Data Storage  

---

## 🛠️ Technology Stack

### Frontend

- Next.js / React  
- Tailwind CSS  
- NextAuth for Authentication  

### Backend

- **Node.js** – API gateway, auth, MongoDB (no transcript extraction in Node)
- **Python Pipeline** – Transcript extraction, chapter generation, orchestration (port 8001)
- **course-generator-api** – Existing Python FastAPI service for AI course generation (port 8000)

### Database

- MongoDB (Atlas / Local)  

### AI / ML

- **Pipeline**: sentence-transformers, scikit-learn, yt-dlp, youtube-transcript-api  
- **Course generator**: Groq (see `course-generator-api`)  

---

## 🧑‍💻 Getting Started (Local Development)

For full setup and endpoint details, see **`Overview.md`**.

### 1. Prerequisites

- **Node.js** (v18+)
- **Python 3.10+**
- **MongoDB** (local or Atlas)
- **yt-dlp** on `PATH` (for transcript fallback)
- **GROQ_API_KEY** in `course-generator-api/.env` (for course generation)

### 2. Environment variables

- **Project root** `.env.local`:
  - `MONGODB_URI`, `EMAIL_USER`, `EMAIL_PASS`, `NEXTAUTH_SECRET`, `NEXTAUTH_URL=http://localhost:3000`
  - Optional: `PIPELINE_URL=http://localhost:8001`
- **course-generator-api** `.env`:
  - `GROQ_API_KEY` (required for `/generate-course`)

### 3. Install dependencies

```bash
# Next.js + Node API
npm install

# Pipeline (transcript + chapter services)
pip install -r requirements.txt

# Course generator (existing service)
cd course-generator-api && pip install -r requirements.txt && cd ..
```

### 4. Run the services

From the project root:

```bash
# Terminal 1: Course generator (port 8000)
npm run start-python

# Terminal 2: Pipeline – transcript + chapter (port 8001)
npm run start-pipeline

# Terminal 3: Next.js (port 3000)
npm run dev
```

Or run all three together:

```bash
npm run dev:all
```

Then open `http://localhost:3000`.

---

## 📚 Additional Documentation

- **Architecture, folder structure, and API endpoints**: see `Overview.md`  
- **Auth flows and endpoint testing examples**: see `Overview.md` section 4 and 5  

---

## 🏗️ System Flow

1. **User** enters YouTube URL on frontend.  
2. **Node.js API** calls **Pipeline service** (`/generate-course-from-youtube`).  
3. **Pipeline** (Python):  
   - **Transcript service** extracts transcript and segments (captions API → timedtext → yt-dlp).  
   - **Chapter service** generates chapters from segments (sentence-transformers + similarity).  
   - Calls existing **course-generator-api** `/generate-course` with transcript.  
4. **Course generator** returns structured course; pipeline returns course + chapters to Node.  
5. **Frontend** displays course, lessons, quizzes; optional MongoDB cache for transcript-only flow.  

---

## ⚠️ Limitations

- Dependent on transcript availability  

- AI-generated content may require refinement  

- Works best for educational videos  

- Requires internet connectivity for API calls  

---

## 🚀 Future Enhancements

- Multi-video playlist support  

- Course comparison  

- Peer discussion forum  

- Instructor rating system  

- PDF downloadable notes  

- Advanced analytics dashboard  

- Blockchain-based certificate verification  

---

## 📌 Short Description

> LearnTube is an AI-powered platform that converts any educational YouTube video into a structured course with documentation, assessments, and certification, enabling students to transform free content into a professional learning experience.


//long-video
https://youtu.be/eIrMbAQSU34?si=j_L1Hj4NYb-8N-NQ

//short-video
https://youtu.be/O2gerCxEXvc?si=vSTz9VMi_s6b2fW7