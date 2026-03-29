from typing import Dict
from models.pipeline_schemas import TopicList
from course_generator.src.core.groq_client import GroqClient
from course_generator.src.pipeline.prompts import Prompts

class TopicExtractor:
    def __init__(self, groq_client: GroqClient):
        self.client = groq_client

    async def extract_topics(self, transcript_text: str) -> TopicList:
        """
        Extracts topics from the given plain transcript text.
        """
        prompt = Prompts.TOPIC_EXTRACTION.format(transcript=transcript_text)
        
        messages = [{"role": "user", "content": prompt}]
        
        # We request strict JSON formatting enforcing TopicList structure
        result: TopicList = await self.client.chat_completion(
            messages=messages,
            max_tokens=2000,
            temperature=0.2,
            response_format={"type": "json_object"},
            model="llama-3.3-70b-versatile",
            pydantic_model=TopicList
        )
        
        return result
