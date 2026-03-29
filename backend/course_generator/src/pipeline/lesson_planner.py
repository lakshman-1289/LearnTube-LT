import json
from models.pipeline_schemas import LessonPlan, TopicList
from course_generator.src.core.groq_client import GroqClient
from course_generator.src.pipeline.prompts import Prompts

class LessonPlanner:
    def __init__(self, groq_client: GroqClient):
        self.client = groq_client

    async def plan_lessons(self, topics: TopicList) -> LessonPlan:
        """
        Plans lessons from an extracted topic list.
        """
        topics_json = topics.model_dump_json(indent=2)
        prompt = Prompts.LESSON_PLANNER.format(topics_json=topics_json)
        
        messages = [{"role": "user", "content": prompt}]
        
        result: LessonPlan = await self.client.chat_completion(
            messages=messages,
            max_tokens=2500,
            temperature=0.3, # slightly higher for creativity on titles
            response_format={"type": "json_object"},
            model="llama-3.3-70b-versatile",
            pydantic_model=LessonPlan
        )
        
        return result
