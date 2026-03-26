"""
Main entry point for YouTube Course Generator
This file can be used for standalone course generation
"""

import asyncio
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from course_generator.src.core.transcript_processor import TranscriptProcessor
from course_generator.src.core.groq_client import GroqClient
from course_generator.src.core.courseGenerator import CourseGenerator

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

async def generate_course_from_transcript(transcript_content: str) -> dict:
    """
    Main function to generate course from transcript content
    """
    # Initialize components
    processor = TranscriptProcessor()
    groq_client = GroqClient(api_key=os.getenv("GROQ_API_KEY"))
    course_generator = CourseGenerator(groq_client, processor)
    
    # Prepare transcript JSON
    transcript_json = {"content": transcript_content}
    
    # Validate transcript
    if not processor.validate_transcript(transcript_json):
        raise ValueError("Invalid transcript content")
    
    # Enhance transcript quality
    enhanced_transcript = processor.enhance_transcript_quality(transcript_json)
    
    try:
        # Generate course
        course_data = await course_generator.generate_complete_course(enhanced_transcript)
        return course_data
    except Exception as e:
        raise Exception(f"Course generation failed: {str(e)}")
    finally:
        if hasattr(groq_client, 'session') and groq_client.session:
            await groq_client.session.close()

async def main():
    """
    Example usage of the course generator
    """
    # Sample transcript for testing
    sample_transcript = """
    Welcome to this comprehensive Python programming course. In this tutorial, we'll start with the basics of Python programming. 
    Python is a high-level programming language that was created by Guido van Rossum and first released in 1991. 
    Python is known for its simplicity and readability. Let's begin with variables. In Python, you can create variables by 
    simply assigning a value to them. For example, name equals John, age equals 25. Python supports several data types 
    including integers, floats, strings, and booleans. Integers are whole numbers like 1, 2, 3. Floats are decimal numbers 
    like 3.14, 2.5. Strings are text enclosed in quotes like Hello World. Booleans are True or False values. 
    Now let's talk about conditional statements. If statements allow you to execute code based on certain conditions. 
    For example, if age is greater than 18, print adult, else print minor. Loops are used to repeat code. 
    The for loop iterates over a sequence, while the while loop continues as long as a condition is true. 
    Functions are reusable blocks of code. You define a function using the def keyword followed by the function name and parameters.
    """
    
    try:
        print("🚀 Starting course generation...")
        course_data = await generate_course_from_transcript(sample_transcript)
        
        print("✅ Course generated successfully!")
        print(f"📚 Course Title: {course_data['courseInfo']['title']}")
        print(f"📖 Total Lessons: {course_data['courseInfo']['totalLessons']}")
        print(f"❓ Total Quizzes: {sum(len(lesson.get('quizzes', [])) for lesson in course_data['lessons'])}")
        
        # Save to file
        with open('generated_course.json', 'w') as f:
            json.dump(course_data, f, indent=2)
        print("💾 Course saved to generated_course.json")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
