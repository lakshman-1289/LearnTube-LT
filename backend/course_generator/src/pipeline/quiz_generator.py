import json
from models.pipeline_schemas import LessonContent, QuizList
from llm.base import BaseLLMProvider
from llm.prompt_manager import PromptManager

class QuizGenerator:
    def __init__(self, llm_client: BaseLLMProvider):
        self.client = llm_client

    async def generate_quizzes(self, lesson_content: LessonContent) -> QuizList:
        """
        Agent to construct precise quizzes from generated educational content.
        """
        prompt = PromptManager.get_prompt(
            "QUIZ_GENERATOR", 
            lesson_content=lesson_content.model_dump_json()
        )
        
        # System boundaries ensuring precise JSON output
        messages = [{"role": "system", "content": "You are an expert evaluator. Return ONLY valid JSON format strictly mapping to Quiz schema."},
                    {"role": "user", "content": prompt}]
        
        result: QuizList = await self.client.generate_structured_output(
            messages=messages,
            pydantic_schema=QuizList,
            max_tokens=2000,
            temperature=0.4 # Minimal variance mostly focusing on factual scenarios
        )
        
        return result
