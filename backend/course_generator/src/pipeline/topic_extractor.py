from typing import Dict
from models.pipeline_schemas import TopicList
from course_generator.src.core.groq_client import GroqClient
from course_generator.src.pipeline.prompts import Prompts

class TopicExtractor:
    def __init__(self, groq_client: GroqClient):
        self.client = groq_client

    async def extract_topics(self, transcript_text: str) -> TopicList:
        """
        Extracts topics from the given plain transcript text in chunks to avoid rate limits.
        """
        from course_generator.src.pipeline.chunking_service import chunking_service
        import asyncio
        import json
        import os

        # Determine safe token limit per request (default to 1500 to heavily reduce TPM load)
        safe_limit = int(os.getenv("GROQ_SAFE_TOKEN_LIMIT", "1500"))

        # We ask the model to produce up to 500 tokens of output for topic extraction
        max_output_tokens = 500

        # Use smart chunking to ensure prompt + chunk + output <= safe_limit
        chunks = chunking_service.smart_chunk_transcript(
            transcript_text=transcript_text,
            prompt_template=Prompts.TOPIC_EXTRACTION,
            max_output_tokens=max_output_tokens,
            token_limit=safe_limit,
            buffer_tokens=50
        )
        all_topics = []
        
        for i, chunk in enumerate(chunks):
            print(f"[PIPELINE] 🧩 Extracting topics from chunk {i+1}/{len(chunks)}...")
            prompt = Prompts.TOPIC_EXTRACTION.format(transcript=chunk)

            messages = [{"role": "user", "content": prompt}]

            # We request strict JSON formatting enforcing TopicList structure
            result: TopicList = await self.client.chat_completion(
                messages=messages,
                max_tokens=max_output_tokens,
                temperature=0.2,
                response_format={"type": "json_object"},
                model="llama-3.1-8b-instant",
                pydantic_model=TopicList
            )
            
            all_topics.extend(result.topics)
            
            # Stay under 12k TPM rate limits roughly
            if i < len(chunks) - 1:
                print("[PIPELINE] ⏱️ Sleeping 12s to respect API rate limits...")
                await asyncio.sleep(12)
                
        return TopicList(topics=all_topics)
