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
        
        chunks = chunking_service.chunk_transcript(transcript_text)
        all_topics = []
        
        for i, chunk in enumerate(chunks):
            print(f"[PIPELINE] 🧩 Extracting topics from chunk {i+1}/{len(chunks)}...")
            prompt = Prompts.TOPIC_EXTRACTION.format(transcript=chunk)
            
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
            
            all_topics.extend(result.topics)
            
            # Stay under 12k TPM rate limits roughly
            if i < len(chunks) - 1:
                print("[PIPELINE] ⏱️ Sleeping 12s to respect API rate limits...")
                await asyncio.sleep(12)
                
        return TopicList(topics=all_topics)
