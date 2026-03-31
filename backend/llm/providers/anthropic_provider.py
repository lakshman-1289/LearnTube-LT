import aiohttp
import asyncio
import json
from typing import Dict, List, Optional, Type
from pydantic import BaseModel
from llm.base import BaseLLMProvider

class AnthropicProvider(BaseLLMProvider):
    def __init__(self, api_key: str, default_model: str):
        super().__init__(api_key, default_model)
        self.base_url = "https://api.anthropic.com/v1"
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    def _convert_messages(self, messages: List[Dict[str, str]]):
        """Extract explicit system prompt from generic messages for Anthropic API requirements"""
        anthropic_msgs = []
        system_content = ""
        
        for msg in messages:
            if msg["role"] == "system":
                system_content += msg["content"] + "\n\n"
            else:
                anthropic_msgs.append(msg)
                
        return anthropic_msgs, system_content.strip()

    async def _execute_request(self, payload: dict) -> str:
        session = await self._get_session()
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        max_retries = 3
        base_delay = 5
        
        for attempt in range(max_retries):
            try:
                timeout_seconds = 180 + (attempt * 60)
                async with session.post(
                    f"{self.base_url}/messages",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=timeout_seconds)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        return data["content"][0]["text"]
                        
                    elif response.status == 429:
                        wait = base_delay ** (attempt + 1)
                        self.logger.warning(f"Anthropic Rate limit hit. Retrying in {wait}s...")
                        await asyncio.sleep(wait)
                        
                    elif response.status == 400:
                        text = await response.text()
                        raise Exception(f"Anthropic Bad Request: {text}")
                    elif response.status == 401:
                        text = await response.text()
                        raise Exception(f"Anthropic Auth Error: {text}")
                    else:
                        text = await response.text()
                        if attempt == max_retries - 1:
                            raise Exception(f"Anthropic API error {response.status}: {text}")
                        await asyncio.sleep(base_delay ** (attempt + 1))
                        
            except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                self.logger.error(f"Anthropic Connection Error: {str(e)}")
                if attempt == max_retries - 1:
                    raise Exception(f"Network error: {str(e)}")
                await asyncio.sleep(base_delay ** (attempt + 1))
                
        raise Exception("Failed to get response from Anthropic API")

    async def generate_text(self, messages: List[Dict[str, str]], model: Optional[str] = None, max_tokens: int = 4000, temperature: float = 0.2) -> str:
        anthropic_msgs, system_content = self._convert_messages(messages)
        
        payload = {
            "model": model or self.default_model,
            "messages": anthropic_msgs,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        if system_content:
            payload["system"] = system_content
            
        content = await self._execute_request(payload)
        return content.strip()

    async def generate_structured_output(self, messages: List[Dict[str, str]], pydantic_schema: Type[BaseModel], model: Optional[str] = None, max_tokens: int = 4000, temperature: float = 0.2) -> BaseModel:
        # Anthropic doesn't support an explicit response_format forcing globally like OpenAI 
        # outside of tool calling parsing, which requires more boilerplate. 
        # Using string injection is equally robust natively inside Haiku/Sonnet due to their high instruction adherence.
        
        schema_dict = json.dumps(pydantic_schema.model_json_schema())
        schema_instruction = f" You MUST return a JSON object that strictly adheres to this JSON schema: {schema_dict}. Do not include markdown formatting, backticks, or conversational text. Output raw JSON."
        
        messages_copy = messages.copy()
        
        # Inject standard string forced JSON output requirement
        sys_msg_idx = next((i for i, m in enumerate(messages_copy) if m["role"] == "system"), -1)
        if sys_msg_idx >= 0:
            messages_copy[sys_msg_idx]["content"] += schema_instruction
        else:
            messages_copy.insert(0, {"role": "system", "content": f"You are a strict JSON data generator.{schema_instruction}"})
            
        anthropic_msgs, system_content = self._convert_messages(messages_copy)
        
        payload = {
            "model": model or self.default_model,
            "messages": anthropic_msgs,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_content
        }
        
        content = await self._execute_request(payload)
        
        try:
            # Manually strip potential bad hallucinated markdown ticks Anthropic occasionally sneaks in
            cleaned = content.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
                
            return pydantic_schema.model_validate_json(cleaned.strip())
        except Exception as e:
            self.logger.error(f"Pydantic mapping failed on Anthropic response: {e}")
            raise Exception(f"Failed to match Pydantic schema: {str(e)}. Raw content: {content}")

    async def async_close(self):
        if self.session and not self.session.closed:
            await self.session.close()
