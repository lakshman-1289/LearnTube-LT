# This __init__.py makes this core folder becomes package/module

"""
Core modules for YouTube Course Generator
Contains transcript processing, Groq client, and course generation logic
"""

from .transcript_processor import TranscriptProcessor
from .groq_client import GroqClient
from .courseGenerator import CourseGenerator

__all__ = [
    "TranscriptProcessor",
    "GroqClient",
    "CourseGenerator"
]