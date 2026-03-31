import aiohttp
import asyncio
import json
from typing import Dict, List, Optional, Type
from pydantic import BaseModel
from llm.base import BaseLLMProvider

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str, default_model: str):
        super().__init__(api_key, default_model)
        self.base_url = "https://api.openai.com/v1"
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def _execute_request(self, payload: dict) -> str:
        session = await self._get_session()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        max_retries = 3
        base_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Dynamic timeout handling allowing 120s for processing large contexts
                timeout_seconds = 120 + (attempt * 30)
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=timeout_seconds)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        return data["choices"][0]["message"]["content"]
                        
                    elif response.status == 429:
                        wait = base_delay ** (attempt + 1)
                        self.logger.warning(f"OpenAI Rate limit hit. Retrying in {wait}s...")
                        await asyncio.sleep(wait)
                        
                    elif response.status == 401:
                        raise Exception(f"OpenAI Authentication failed: {await response.text()}")
                        
                    else:
                        text = await response.text()
                        if attempt == max_retries - 1:
                            raise Exception(f"OpenAI API error {response.status}: {text}")
                        await asyncio.sleep(base_delay ** (attempt + 1))
                        
            except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                self.logger.error(f"OpenAI Connection Error: {str(e)}")
                if attempt == max_retries - 1:
                    raise Exception(f"Network error: {str(e)}")
                await asyncio.sleep(base_delay ** (attempt + 1))
                
        raise Exception("Failed to get response from OpenAI API")

    async def generate_text(self, messages: List[Dict[str, str]], model: Optional[str] = None, max_tokens: int = 4000, temperature: float = 0.2) -> str:
        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False
        }
        content = await self._execute_request(payload)
        return content.strip()

    async def generate_structured_output(self, messages: List[Dict[str, str]], pydantic_schema: Type[BaseModel], model: Optional[str] = None, max_tokens: int = 4000, temperature: float = 0.2) -> BaseModel:
        # Utilize OpenAI's strict Structured Output parsing algorithm allowing direct instantiation maps
        schema_dict = pydantic_schema.model_json_schema()
        
        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": pydantic_schema.__name__.lower(),
                    "schema": schema_dict,
                    "strict": True
                }
            },
            "stream": False
        }
        
        content = await self._execute_request(payload)
        
        try:
            return pydantic_schema.model_validate_json(content)
        except Exception as e:
            self.logger.error(f"Pydantic mapping failed on OpenAI response: {e}")
            raise Exception(f"Failed to match Pydantic schema: {str(e)}. Raw content: {content}")

    async def async_close(self):
        if self.session and not self.session.closed:
            await self.session.close()
