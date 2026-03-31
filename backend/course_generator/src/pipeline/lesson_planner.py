import json
from models.pipeline_schemas import LessonPlan, TopicList
from llm.base import BaseLLMProvider
from llm.prompt_manager import PromptManager

class LessonPlanner:
    def __init__(self, llm_client: BaseLLMProvider):
        self.client = llm_client

    async def plan_lessons(self, topics: TopicList) -> LessonPlan:
        """
        Plans lessons from an extracted topic list.
        """
        topics_json = topics.model_dump_json(indent=2)
        prompt = PromptManager.get_prompt("LESSON_PLANNER", topics_json=topics_json)
        
        messages = [{"role": "user", "content": prompt}]
        
        result: LessonPlan = await self.client.generate_structured_output(
            messages=messages,
            pydantic_schema=LessonPlan,
            max_tokens=2500,
            temperature=0.3
        )
        
        return result
