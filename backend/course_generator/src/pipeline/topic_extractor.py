from typing import Dict
from models.pipeline_schemas import TopicList
from llm.base import BaseLLMProvider
from llm.prompt_manager import PromptManager

class TopicExtractor:
    def __init__(self, llm_client: BaseLLMProvider):
        self.client = llm_client

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
            prompt = PromptManager.get_prompt("TOPIC_EXTRACTION", transcript=chunk)
            
            messages = [{"role": "user", "content": prompt}]
            
            # Utilizing the Provider-Agnostic Structured Output interface
            result: TopicList = await self.client.generate_structured_output(
                messages=messages,
                pydantic_schema=TopicList,
                max_tokens=2000,
                temperature=0.2
            )
            
            all_topics.extend(result.topics)
            
            # Stay under TPM limits if necessary based on model speed
            if i < len(chunks) - 1:
                print("[PIPELINE] ⏱️ Sleeping briefly to respect dynamically scaled API rate limits...")
                await asyncio.sleep(5)
                
        return TopicList(topics=all_topics)
