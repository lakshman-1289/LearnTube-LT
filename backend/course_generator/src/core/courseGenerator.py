from typing import Dict
from course_generator.src.core.groq_client import GroqClient
from course_generator.src.pipeline.topic_extractor import TopicExtractor
from course_generator.src.pipeline.lesson_planner import LessonPlanner
from course_generator.src.pipeline.content_generator import ContentGenerator
from course_generator.src.pipeline.quiz_generator import QuizGenerator
from course_generator.src.pipeline.course_assembler import CourseAssembler
from models.pipeline_schemas import FinalCourse

class CourseGenerator:
    """
    Acts as the Orchestrator for the entire course generation pipeline.
    Linearly processes nodes: Topic -> Lesson -> Content -> Quizzes -> Assembly
    """
    def __init__(self, groq_client: GroqClient):
        self.client = groq_client
        
        # Initialize specialized agents
        self.topic_extractor = TopicExtractor(self.client)
        self.lesson_planner = LessonPlanner(self.client)
        self.content_generator = ContentGenerator(self.client)
        self.quiz_generator = QuizGenerator(self.client)
        
    async def generate_complete_course(self, transcript_text: str, video_title: str, video_url: str = "original_video_url") -> Dict:
        """
        Coordinates the pipeline execution and returns dict mapping to FinalCourse JSON format.
        """
        try:
            print("[PIPELINE] 🚀 Starting Topic Extraction...")
            topics = await self.topic_extractor.extract_topics(transcript_text)
            print(f"[PIPELINE] ✅ Extracted {len(topics.topics)} topics.")
            
            print("[PIPELINE] 🗓️ Planning Lessons...")
            lesson_plan = await self.lesson_planner.plan_lessons(topics)
            print(f"[PIPELINE] ✅ Planned {len(lesson_plan.lessons)} lessons.")
            
            from course_generator.src.pipeline.chunking_service import chunking_service
            import math
            import asyncio
            
            chunks = chunking_service.chunk_transcript(transcript_text)
            
            lesson_contents = []
            lesson_quizzes = []

            # We process contents and quizzes sequentially (or concurrently if we used asyncio.gather)
            for i, lesson_outline in enumerate(lesson_plan.lessons):
                print(f"[PIPELINE] 📖 Generating content for Lesson {i+1}/{len(lesson_plan.lessons)}: {lesson_outline.title}")
                
                # Linearly map the lesson index to a chunk to keep requests under TPM limits
                chunk_index = math.floor((i / max(len(lesson_plan.lessons), 1)) * len(chunks))
                chunk_index = min(chunk_index, len(chunks) - 1)
                
                # Combine current chunk and the next one to ensure conceptual boundaries aren't heavily cut
                context_chunks = [chunks[chunk_index]]
                if chunk_index < len(chunks) - 1:
                    context_chunks.append(chunks[chunk_index + 1])
                mapped_transcript_context = " ".join(context_chunks)
                
                content = await self.content_generator.generate_lesson_content(
                    lesson_title=lesson_outline.title,
                    lesson_subtitle=lesson_outline.subtitle,
                    transcript_context=mapped_transcript_context # Passing contextual chunks instead of full 30k str
                )
                lesson_contents.append(content)
                
                print(f"[PIPELINE] 🧠 Generating quizzes for Lesson {i+1}")
                quizzes = await self.quiz_generator.generate_quizzes(content)
                lesson_quizzes.append(quizzes)
                
                # Add delay to respect Groq free tier limit of 12000 TPM
                if i < len(lesson_plan.lessons) - 1:
                    print("[PIPELINE] ⏱️ Sleeping 15s to keep Groq TPM boundaries safe...")
                    await asyncio.sleep(15)

            print("[PIPELINE] 🏗️ Assembling Final Course JSON...")
            final_course: FinalCourse = CourseAssembler.assemble_final_course(
                video_url=video_url,
                video_title=video_title,
                lesson_outlines=lesson_plan.lessons,
                lesson_contents=lesson_contents,
                lesson_quizzes=lesson_quizzes
            )

            print("[PIPELINE] 🎉 Success! Returning Pydantic validated course data.")
            return final_course.model_dump()

        except Exception as e:
            print(f"[PIPELINE ERROR] ❌ Generation failed at pipeline stage: {str(e)}")
            return {"error": str(e)}