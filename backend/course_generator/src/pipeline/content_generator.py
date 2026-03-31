from models.pipeline_schemas import LessonContent
from llm.base import BaseLLMProvider
from llm.prompt_manager import PromptManager

class ContentGenerator:
    def __init__(self, llm_client: BaseLLMProvider):
        self.client = llm_client

    async def generate_lesson_content(self, lesson_title: str, lesson_subtitle: str, transcript_context: str) -> LessonContent:
        """
        Agent strictly responsible for authoring educational content bounding to the schema structure.
        """
        prompt = PromptManager.get_prompt(
            "CONTENT_GENERATOR",
            lesson_title=lesson_title,
            lesson_subtitle=lesson_subtitle,
            transcript_segment=transcript_context
        )
        
        # Adding a system message to be explicit
        messages = [{"role": "system", "content": "You are an expert AI curriculum writer. Return ONLY valid JSON."},
                    {"role": "user", "content": prompt}]
        
        result: LessonContent = await self.client.generate_structured_output(
            messages=messages,
            pydantic_schema=LessonContent,
            max_tokens=3500,
            temperature=0.3 # Low temp for deterministic adherence to fact bounds
        )
        
        return result
