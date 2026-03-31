from models.pipeline_schemas import LessonContent
from course_generator.src.core.groq_client import GroqClient
import os
from course_generator.src.pipeline.prompts import Prompts
from course_generator.src.pipeline.safe_pipeline import (
    smart_chunk_text,
    summarize_chunks,
    count_tokens,
)
from course_generator.src.services.groq_service import safe_groq_request
from course_generator.src.core.llm_utils import clean_llm_json, normalize_lesson
from pydantic import ValidationError
import json


class ContentGenerator:
    def __init__(self, groq_client: GroqClient):
        self.client = groq_client

    async def generate_lesson_content(self, lesson_title: str, lesson_subtitle: str, transcript_context: str) -> LessonContent:
        """
        Two-stage generation:
        1) Token-aware chunking + summarization (reduce transcript to concise summary chunks)
        2) Generate lesson content from the combined summaries using a compact prompt

        This ensures we never send >8000 tokens per request and keeps semantic integrity.
        """

        # 1) Chunk transcript strictly by tokens (safe limit 2000; reserve room for summary output)
        prompt_template = "Summarize the transcript chunk:\n{transcript}\n"
        chunks = smart_chunk_text(
            transcript_context,
            prompt_template=prompt_template,
            max_input_tokens=2000,
            max_output_tokens=300,
            buffer_tokens=50,
        )

        # 2) Summarize each chunk (cached)
        summaries = await summarize_chunks(self.client, chunks, summary_max_tokens=300)

        # Combine summaries into a single short context (still small)
        combined_summary = "\n\n".join(summaries)
        print(f"[CONTENT_GEN] Combined summary tokens={count_tokens(combined_summary)} chars={len(combined_summary)}")

        # 3) Build a strict prompt that enforces exact JSON schema and forbids extra text/markdown
        schema_snippet = (
            '{\n'
            '  "lessonTitle": "string",\n'
            '  "introduction": "string",\n'
            '  "sections": [\n'
            '    {"title": "string", "type": "string", "points": ["string"] }\n'
            '  ],\n'
            '  "conclusion": "string"\n'
            '}'
        )

        strict_prompt = (
            "You are an expert educational content writer.\n"
            "Produce EXACTLY and ONLY a JSON object that matches the schema below.\n"
            "Do NOT include any markdown, explanation, or extra fields. Return raw JSON only.\n"
            "Do NOT include trailing commas. Do NOT wrap JSON in code fences.\n"
            "Follow the schema EXACTLY. If any field is missing, return an empty string or empty list (do not omit keys).\n\n"
            "SCHEMA:\n" + schema_snippet + "\n\n"
            "GROUND TRUTH (use only this summary; do NOT hallucinate):\n" + combined_summary + "\n\n"
            f"Context fields you can use:\n- lessonTitle: {lesson_title}\n- lessonSubtitle (do NOT include this field in the output schema)\n\n"
            "Return ONLY valid JSON matching the schema exactly."
        )

        # We removed the LLM retries; we just coerce it on the backend.
        json_text = await safe_groq_request(
            prompt=strict_prompt,
            model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
            max_tokens=500,
            temperature=0.2,
            token_limit=2000,
            stage_context=f"generate_lesson_{lesson_title}" ,
        )

        try:
            parsed = clean_llm_json(json_text)
        except Exception as e:
            print(f"⚠️ [CONTENT_GEN] Failed to extract JSON: {e}")
            parsed = {}

        # The super-strict normalizer forces the parsed dict into the Pydantic schema shape implicitly
        normalized = normalize_lesson(parsed)
        print(f"📊 [CONTENT_GEN] Normalized JSON preview: {str(normalized)[:300]}")
        
        try:
            validated = LessonContent(**normalized)
            print(f"✅ [CONTENT_GEN] Success. Lesson Content validated perfectly after Python normalization.")
            return validated
        except ValidationError as ve:
            raise RuntimeError(f"Validation inherently failed despite normalization: {ve}\nNORMD: {normalized}")
