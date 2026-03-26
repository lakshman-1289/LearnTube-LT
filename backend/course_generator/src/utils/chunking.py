import re

class ChunkingUtils:

    @staticmethod
    def split_text(text: str, max_length: int = 3000) -> list:
        """
        Split text into chunks safely for LLM processing
        """

        sentences = re.split(r'(?<=[.!?]) +', text)

        chunks = []
        current_chunk = ""

        for sentence in sentences:

            if len(current_chunk) + len(sentence) <= max_length:
                current_chunk += sentence + " "
            else:
                chunks.append(current_chunk.strip())
                current_chunk = sentence + " "

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks