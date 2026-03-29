import json
from models.pipeline_schemas import LessonContent, QuizList
from course_generator.src.core.groq_client import GroqClient
from course_generator.src.pipeline.prompts import Prompts

class QuizGenerator:
    def __init__(self, groq_client: GroqClient):
        self.client = groq_client

    async def generate_quizzes(self, lesson_content: LessonContent) -> QuizList:
        """
        Agent to construct precise quizzes from generated educational content.
        """
        prompt = Prompts.QUIZ_GENERATOR.format(
            lesson_content=lesson_content.model_dump_json()
        )
        
        # System boundaries ensuring precise JSON output
        messages = [{"role": "system", "content": "You are an expert evaluator. Return ONLY valid JSON format strictly mapping to Quiz schema."},
                    {"role": "user", "content": prompt}]
        
        result: QuizList = await self.client.chat_completion(
            messages=messages,
            max_tokens=2000,
            temperature=0.4, # Minimal variance mostly focusing on factual scenarios
            response_format={"type": "json_object"},
            model="llama-3.3-70b-versatile",
            pydantic_model=QuizList
        )
        
        return result
