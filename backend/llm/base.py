from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Type, Any
from pydantic import BaseModel
import logging

class BaseLLMProvider(ABC):
    """
    Abstract Base Class representing an interchangeable LLM Provider.
    All providers (Groq, OpenAI, Gemini, etc.) must implement this interface.
    """
    
    def __init__(self, api_key: str, default_model: str):
        self.api_key = api_key
        self.default_model = default_model
        self.logger = logging.getLogger(self.__class__.__name__)
        
    @abstractmethod
    async def generate_text(
        self, 
        messages: List[Dict[str, str]], 
        model: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.2
    ) -> str:
        """
        Generates standard text from the LLM based on the provided messages list.
        `messages` format should be generic (e.g. [{"role": "user", "content": "hello"}])
        """
        pass

    @abstractmethod
    async def generate_structured_output(
        self, 
        messages: List[Dict[str, str]], 
        pydantic_schema: Type[BaseModel],
        model: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.2
    ) -> BaseModel:
        """
        Forces structured JSON output conforming to the provided Pydantic schema.
        Returns the parsed Pydantic object.
        """
        pass
        
    async def async_close(self):
        """
        Hook to gracefully close any active sessions (like aiohttp).
        """
        pass
