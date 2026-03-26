"""Pydantic models shared across transcript, chapter, and backend services."""
from pydantic import BaseModel, Field
from typing import List, Optional, Any


class TranscriptSegment(BaseModel):
    """A single transcript segment with timestamp."""
    start: float = Field(..., description="Start time in seconds")
    text: str = Field(..., description="Segment text")


class TranscriptRequest(BaseModel):
    """Request body for transcript extraction."""
    youtube_url: str = Field(..., description="Full YouTube video URL")


class TranscriptResponse(BaseModel):
    """Response from transcript extraction."""
    videoId: str
    title: str = ""
    metadata: dict = Field(default_factory=dict)
    segments: List[TranscriptSegment]
    transcript: str


class ChapterItem(BaseModel):
    """A chapter with title and start time."""
    title: str
    time: float = Field(..., description="Start time in seconds")


class ChapterRequest(BaseModel):
    """Request body for chapter generation."""
    segments: List[TranscriptSegment]


class ChapterResponse(BaseModel):
    """Response from chapter generation."""
    chapters: List[ChapterItem]


class CourseGeneratorInput(BaseModel):
    """Input format expected by the course generator service."""
    content: str = Field(..., description="Full transcript text")
