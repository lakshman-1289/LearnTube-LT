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
        
        schema_snippet = (
            '{\n'
            '  "lessons": [\n'
            '    {\n'
            '      "title": "string",\n'
            '      "subtitle": "string",\n'
            '      "videoMeta": {"start": "00:00:00", "end": "00:05:00"}\n'
            '    }\n'
            '  ]\n'
            '}'
        )

        messages.append({"role": "system", "content": f"Return ONLY valid JSON exactly matching this schema:\n{schema_snippet}\nDo NOT output raw schemas or markdown."})

        raw_json_str = await self.client.chat_completion(
            messages=messages,
            max_tokens=500,
            temperature=0.3, # slightly higher for creativity on titles
            response_format={"type": "json_object"},
            model="llama-3.1-8b-instant"
        )
        
        from course_generator.src.core.llm_utils import clean_llm_json
        try: parsed = clean_llm_json(raw_json_str)
        except Exception: parsed = {}
        
        if "lessons" not in parsed:
            if isinstance(parsed, list): parsed = {"lessons": parsed}
            else: parsed = {"lessons": [parsed]}
            
        for l in parsed.get("lessons", []):
            if not isinstance(l, dict): continue
            if "title" not in l: l["title"] = "Lesson Section"
            if "subtitle" not in l: l["subtitle"] = "Core Concepts"
            if "videoMeta" not in l or not isinstance(l["videoMeta"], dict):
                l["videoMeta"] = {"start": "00:00:00", "end": "00:00:00"}
                
        result = LessonPlan(**parsed)
        
        return result
