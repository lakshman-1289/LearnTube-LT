from pydantic import BaseModel, Field
from typing import List, Literal, Optional

# --- SUB-MODELS FOR SECTIONS ---

class Point(BaseModel):
    subtitle: str = Field(..., description="Subtitle for this specific point")
    content: str = Field(..., description="Detailed explanation or content")

class Section(BaseModel):
    title: str = Field(..., description="Title of the section")
    type: Literal["concept", "example"] = Field(..., description="Type of the section: must be 'concept' or 'example'")
    points: List[Point] = Field(..., description="Bullet points explaining the concept or example")

class LessonContent(BaseModel):
    introduction: str = Field(..., description="Introduction text for the lesson")
    sections: List[Section] = Field(..., description="List of conceptually rich sections")
    conclusion: str = Field(..., description="Conclusion text summarizing the lesson")

# --- SUB-MODELS FOR QUIZ ---

class Quiz(BaseModel):
    id: int = Field(..., description="Unique integer ID for the quiz")
    question: str = Field(..., description="The multiple-choice question")
    type: str = Field(default="multiple_choice", description="Must be 'multiple_choice'")
    options: List[str] = Field(..., min_length=4, max_length=4, description="List of exactly 4 string options")
    correctAnswer: int = Field(..., ge=0, le=3, description="Index of the correct answer (0-3)")
    answer: str = Field(..., description="The exact text of the correct answer")
    explanation: str = Field(..., description="Why this answer is correct and others are wrong")

# --- SUB-MODELS FOR LESSON ---

class VideoMeta(BaseModel):
    start: str = Field(..., description="Start timestamp (e.g., '00:00:00')")
    end: str = Field(..., description="End timestamp (e.g., '00:05:00')")

class Lesson(BaseModel):
    id: int = Field(..., description="Unique integer ID for the lesson (start from 1)")
    title: str = Field(..., description="Lesson title")
    subtitle: str = Field(..., description="Lesson subtitle")
    type: str = Field(default="video", description="Must be 'video'")
    videoMeta: VideoMeta = Field(..., description="Start/end markers")
    completed: bool = Field(default=False)
    current: bool = Field(default=False)
    content: LessonContent = Field(..., description="Main educational content")
    quizzes: List[Quiz] = Field(..., description="Quizzes associated with this lesson")

# --- ROOT COURSE INFO AND EXAM ---

class CourseInfo(BaseModel):
    title: str = Field(..., description="Global Course Title")
    subtitle: str = Field(..., description="Global Course Subtitle")
    duration: str = Field(..., description="Estimated total duration (e.g. '45min', '1h 30min')")
    totalLessons: int = Field(..., description="Number of lessons")

class VideoSource(BaseModel):
    url: str = Field(..., description="Original YouTube URL")

class FinalExam(BaseModel):
    enabled: bool = Field(default=True)
    prerequisiteCompletion: int = Field(default=100)
    timeLimit: str = Field(default="1h 30min")
    questionCount: int = Field(..., description="Total questions across the course or exam")
    passingScore: int = Field(default=70)
    examType: str = Field(default="application_based")

# --- ROOT FINAL COURSE ---
class FinalCourse(BaseModel):
    courseInfo: CourseInfo
    videoSource: VideoSource
    lessons: List[Lesson]
    finalExam: FinalExam

# --- INTERNAL PIPELINE MODELS (For intermediate stages) ---
class ExtractedTopic(BaseModel):
    title: str = Field(..., description="The distinct topic covered")
    summary: str = Field(..., description="A short summary of what is discussed here")
    start_time: str = Field(..., description="Start timestamp HH:MM:SS")
    end_time: str = Field(..., description="End timestamp HH:MM:SS")

class TopicList(BaseModel):
    topics: List[ExtractedTopic]

class BaseLessonOutline(BaseModel):
    title: str
    subtitle: str
    videoMeta: VideoMeta
    
class LessonPlan(BaseModel):
    lessons: List[BaseLessonOutline]

class QuizList(BaseModel):
    quizzes: List[Quiz]
