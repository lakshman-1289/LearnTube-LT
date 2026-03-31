# This __init__.py makes this core folder becomes package/module

"""
Core modules for YouTube Course Generator
Contains transcript processing, Groq client, and course generation logic
"""

from .transcript_processor import TranscriptProcessor
from .courseGenerator import CourseGenerator

__all__ = [
    "TranscriptProcessor",
    "CourseGenerator"
]