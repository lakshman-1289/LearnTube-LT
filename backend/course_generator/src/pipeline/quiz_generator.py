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
        schema_snippet = (
            '{\n'
            '  "quizzes": [\n'
            '    {\n'
            '      "id": 1,\n'
            '      "question": "string",\n'
            '      "type": "multiple_choice",\n'
            '      "options": ["string", "string", "string", "string"],\n'
            '      "correctAnswer": 0,\n'
            '      "answer": "string",\n'
            '      "explanation": "string"\n'
            '    }\n'
            '  ]\n'
            '}'
        )

        # System boundaries ensuring precise JSON output
        messages = [
            {"role": "system", "content": f"You are an expert evaluator. Return ONLY valid JSON exactly matching this schema, completely filled out with realistic outputs:\n{schema_snippet}\nDo NOT include markdown or raw JSON Schema `$defs`."},
            {"role": "user", "content": prompt}
        ]
        
        raw_json_str = await self.client.chat_completion(
            messages=messages,
            max_tokens=650,
            temperature=0.4, # Minimal variance mostly focusing on factual scenarios
            response_format={"type": "json_object"},
            model="llama-3.1-8b-instant"
        )
        
        from course_generator.src.core.llm_utils import clean_llm_json
        
        try:
            parsed = clean_llm_json(raw_json_str)
        except Exception:
            parsed = {}
            
        if "quizzes" not in parsed:
            if isinstance(parsed, list):
                parsed = {"quizzes": parsed}
            else:
                # heuristic recovery
                if parsed.get("id") or parsed.get("question"):
                    parsed = {"quizzes": [parsed]}
                else:
                    parsed = {"quizzes": []}

        # Python-side coercion to explicitly satisfy Pydantic
        for i, q in enumerate(parsed.get("quizzes", [])):
            if not isinstance(q, dict): continue
            q["id"] = i + 1
            q["type"] = "multiple_choice"
            
            opts = q.get("options", [])
            if not isinstance(opts, list): opts = [str(opts)]
            # ensure exactly 4 parameters
            while len(opts) < 4: opts.append(f"Option {len(opts)+1}")
            q["options"] = [str(o) for o in opts[:4]]
            
            # coerce correct answers
            ca = q.get("correctAnswer")
            if not isinstance(ca, int):
                try: ca = int(ca)
                except: ca = 0
            if ca < 0 or ca > 3: ca = 0
            q["correctAnswer"] = ca
            
            q["answer"] = q.get("answer") or q["options"][ca]
            q["explanation"] = q.get("explanation") or "Correct answer based on the lesson."
            q["question"] = q.get("question") or "Which is correct?"
        
        return QuizList(**parsed)
