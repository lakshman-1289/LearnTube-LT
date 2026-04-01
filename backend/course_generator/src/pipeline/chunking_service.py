import re
from typing import List, Optional

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

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for given text; uses tiktoken if available, else conservative chars/4 heuristic."""
        return self.count_tokens(text)

    def smart_chunk_transcript(
        self,
        transcript_text: str,
        prompt_template: str,
        max_output_tokens: int = 2000,
        token_limit: int = 8000,
        buffer_tokens: int = 50,
        min_chunk_tokens: int = 200
    ) -> List[str]:
        """
        Create sentence-aware chunks that ensure (prompt + chunk + max_output_tokens) <= token_limit.

        - prompt_template should include a single '{transcript}' placeholder.
        - token_limit defaults to 8000 (safe per your requirement).
        - buffer_tokens reserves a small safety margin.
        """
        if '{transcript}' not in prompt_template:
            raise ValueError("prompt_template must contain '{transcript}' placeholder")

        cleaned_text = self.clean_transcript(transcript_text)
        sentences = re.split(r'(?<=[.!?])\s+', cleaned_text)

        # Estimate prompt overhead by substituting empty transcript
        prompt_overhead = prompt_template.replace('{transcript}', '')
        overhead_tokens = self.estimate_tokens(prompt_overhead)

        max_allowed_for_chunk = max(0, token_limit - overhead_tokens - max_output_tokens - buffer_tokens)

        chunks: List[str] = []
        current_chunk_sentences: List[str] = []
        current_tokens = 0

        for sentence in sentences:
            if not sentence.strip():
                continue

            s_tokens = self.estimate_tokens(sentence)

            # If a single sentence itself is larger than allowed, we must truncate the sentence safely
            if s_tokens > max_allowed_for_chunk:
                # Truncate sentence at word boundary to fit
                words = sentence.split()
                acc = []
                acc_tokens = 0
                for w in words:
                    w_tokens = self.estimate_tokens(w + ' ')
                    if acc_tokens + w_tokens > max_allowed_for_chunk:
                        break
                    acc.append(w)
                    acc_tokens += w_tokens

                truncated = ' '.join(acc).rstrip()
                if truncated:
                    # push any existing chunk first
                    if current_chunk_sentences:
                        chunks.append(' '.join(current_chunk_sentences))
                        current_chunk_sentences = []
                        current_tokens = 0

                    chunks.append(truncated + '...')
                # else skip this overlong sentence
                continue

            # If adding this sentence would exceed allowed tokens, finalize current chunk
            if current_tokens + s_tokens > max_allowed_for_chunk and current_chunk_sentences:
                chunks.append(' '.join(current_chunk_sentences))
                current_chunk_sentences = [sentence]
                current_tokens = s_tokens
            else:
                current_chunk_sentences.append(sentence)
                current_tokens += s_tokens

        if current_chunk_sentences:
            chunks.append(' '.join(current_chunk_sentences))

        # Ensure minimum chunk size: if a chunk is too small, try to merge with neighbor
        merged_chunks: List[str] = []
        for c in chunks:
            if not merged_chunks:
                merged_chunks.append(c)
                continue

            if self.estimate_tokens(merged_chunks[-1]) < min_chunk_tokens:
                merged_chunks[-1] = merged_chunks[-1] + ' ' + c
            else:
                merged_chunks.append(c)

        return merged_chunks

chunking_service = ChunkingService()
