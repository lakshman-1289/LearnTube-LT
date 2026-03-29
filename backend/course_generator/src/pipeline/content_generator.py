from models.pipeline_schemas import LessonContent
from course_generator.src.core.groq_client import GroqClient
from course_generator.src.pipeline.prompts import Prompts

class ContentGenerator:
    def __init__(self, groq_client: GroqClient):
        self.client = groq_client

    async def generate_lesson_content(self, lesson_title: str, lesson_subtitle: str, transcript_context: str) -> LessonContent:
        """
        Agent strictly responsible for authoring educational content bounding to the schema structure.
        """
        prompt = Prompts.CONTENT_GENERATOR.format(
            lesson_title=lesson_title,
            lesson_subtitle=lesson_subtitle,
            transcript_segment=transcript_context
        )
        
        # Adding a system message to be explicit
        messages = [{"role": "system", "content": "You are an expert AI curriculum writer. Return ONLY valid JSON."},
                    {"role": "user", "content": prompt}]
        
        result: LessonContent = await self.client.chat_completion(
            messages=messages,
            max_tokens=3500,
            temperature=0.3, # Low temp for deterministic adherence to fact bounds
            response_format={"type": "json_object"},
            model="llama-3.3-70b-versatile",
            pydantic_model=LessonContent
        )
        
        return result
