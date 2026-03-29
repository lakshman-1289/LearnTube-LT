import re
from typing import List

class ChunkingService:
    def __init__(self, chunk_size: int = 2000):
        self.chunk_size = chunk_size
        try:
            import tiktoken
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.encoding = None

    def count_tokens(self, text: str) -> int:
        if self.encoding:
            return len(self.encoding.encode(text))
        return len(text) // 4

    def clean_transcript(self, transcript: str) -> str:
        content = re.sub(r'\b(um|uh|ah|like|you know)\b', '', transcript, flags=re.IGNORECASE)
        content = re.sub(r'\b(gonna)\b', 'going to', content, flags=re.IGNORECASE)
        content = re.sub(r'\b(wanna)\b', 'want to', content, flags=re.IGNORECASE)
        content = re.sub(r'\s+', ' ', content)
        return content.strip()

    def chunk_transcript(self, transcript_text: str) -> List[str]:
        """
        Takes raw transcript and outputs a list of semantically meaningful chunks (approx bounded by token limits)
        """
        cleaned_text = self.clean_transcript(transcript_text)
        sentences = re.split(r'(?<=[.!?])\s+', cleaned_text)
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for sentence in sentences:
            if not sentence.strip():
                continue
                
            sentence_tokens = self.count_tokens(sentence)
            if current_tokens + sentence_tokens > self.chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
                current_tokens = sentence_tokens
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
                
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        return chunks

chunking_service = ChunkingService()
