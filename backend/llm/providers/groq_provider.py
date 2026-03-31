import aiohttp
import asyncio
import json
from typing import Dict, List, Optional, Type
from pydantic import BaseModel
from llm.base import BaseLLMProvider

class GroqProvider(BaseLLMProvider):
    def __init__(self, api_key: str, default_model: str):
        super().__init__(api_key, default_model)
        self.base_url = "https://api.groq.com/openai/v1"
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def _execute_request(self, payload: dict, messages: List[dict]):
        session = await self._get_session()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Adding simple exponential backoff for Groq rate limits
        max_retries = 3
        base_delay = 5
        
        for attempt in range(max_retries):
            try:
                timeout_seconds = 180 + (attempt * 60)
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=timeout_seconds)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        return data["choices"][0]["message"]["content"]
                        
                    elif response.status in (429, 413):
                        # 413 can occur on Groq for Token Per Minute limits on oversized prompts
                        wait = base_delay ** (attempt + 1)
                        if response.status == 413:
                            data_text = await response.text()
                            if "rate_limit_exceeded" not in data_text:
                                raise Exception(f"Payload natively too large for Groq API: {data_text}")
                        
                        self.logger.warning(f"Groq Rate limit hit. Retrying in {wait}s...")
                        await asyncio.sleep(wait)
                        
                    elif response.status == 401:
                        raise Exception(f"Authentication failed: {await response.text()}")
                    else:
                        text = await response.text()
                        if attempt == max_retries - 1:
                            raise Exception(f"Groq API error {response.status}: {text}")
                        await asyncio.sleep(base_delay ** (attempt + 1))
                        
            except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                self.logger.error(f"Groq Connection Error: {str(e)}")
                if attempt == max_retries - 1:
                    raise Exception(f"Network error: {str(e)}")
                await asyncio.sleep(base_delay ** (attempt + 1))
                
        raise Exception("Failed to get response from Groq API")

    async def generate_text(self, messages: List[Dict[str, str]], model: Optional[str] = None, max_tokens: int = 4000, temperature: float = 0.2) -> str:
        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False
        }
        content = await self._execute_request(payload, messages)
        return content.strip()

    async def generate_structured_output(self, messages: List[Dict[str, str]], pydantic_schema: Type[BaseModel], model: Optional[str] = None, max_tokens: int = 4000, temperature: float = 0.2) -> BaseModel:
        # Groq doesn't natively map full strict structure outputs securely yet in identical formatting to OpenAI, 
        # but supports `json_object` format forcing + system prompt injection.
        schema_dump = json.dumps(pydantic_schema.model_json_schema())
        schema_instruction = f" You MUST return a JSON object that strictly adheres to this JSON schema: {schema_dump}. Do not include markdown formatting or extra text."
        
        # Inject instruction to system message or create one
        messages_copy = messages.copy()
        system_msg_idx = next((i for i, m in enumerate(messages_copy) if m["role"] == "system"), -1)
        if system_msg_idx >= 0:
            messages_copy[system_msg_idx]["content"] += schema_instruction
        else:
            messages_copy.insert(0, {"role": "system", "content": f"You are a strict JSON data generator.{schema_instruction}"})

        payload = {
            "model": model or self.default_model,
            "messages": messages_copy,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
            "stream": False
        }
        
        # Retries inherently loop in execute_request but Pydantic parsing needs validation
        content = await self._execute_request(payload, messages_copy)
        
        try:
            json_parsed = json.loads(content)
            return pydantic_schema(**json_parsed)
        except Exception as e:
            self.logger.error(f"Pydantic mapping failed on Groq response: {e}")
            raise Exception(f"Failed to match Pydantic schema: {str(e)}. Raw content: {content}")

    async def async_close(self):
        if self.session and not self.session.closed:
            await self.session.close()
