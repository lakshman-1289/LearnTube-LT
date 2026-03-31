import aiohttp
import asyncio
import json
from typing import Dict, List, Optional, Type
from pydantic import BaseModel
from llm.base import BaseLLMProvider

class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str, default_model: str):
        super().__init__(api_key, default_model)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[Dict]:
        """Convert standard OpenAI-style messages to Gemini format"""
        gemini_msgs = []
        system_instruction = None
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                # Google Gemini uses a separate system_instruction field 
                system_instruction = {"parts": [{"text": content}]}
            else:
                gemini_role = "user" if role == "user" else "model"
                gemini_msgs.append({
                    "role": gemini_role,
                    "parts": [{"text": content}]
                })
        
        return gemini_msgs, system_instruction

    async def _execute_request(self, payload: dict, model: str) -> str:
        session = await self._get_session()
        headers = {"Content-Type": "application/json"}
        
        max_retries = 3
        base_delay = 5
        
        for attempt in range(max_retries):
            try:
                timeout_seconds = 180 + (attempt * 60)
                async with session.post(
                    f"{self.base_url}/{model}:generateContent?key={self.api_key}",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=timeout_seconds)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        try:
                            return data["candidates"][0]["content"]["parts"][0]["text"]
                        except (KeyError, IndexError):
                            raise Exception("Invalid response structure from Gemini API")
                            
                    elif response.status == 429:
                        wait = base_delay ** (attempt + 1)
                        self.logger.warning(f"Gemini Rate limit hit. Retrying in {wait}s...")
                        await asyncio.sleep(wait)
                        
                    elif response.status == 400:
                        text = await response.text()
                        raise Exception(f"Gemini Bad Request: {text}")
                    else:
                        text = await response.text()
                        if attempt == max_retries - 1:
                            raise Exception(f"Gemini API error {response.status}: {text}")
                        await asyncio.sleep(base_delay ** (attempt + 1))
                        
            except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                self.logger.error(f"Gemini Connection Error: {str(e)}")
                if attempt == max_retries - 1:
                    raise Exception(f"Network error: {str(e)}")
                await asyncio.sleep(base_delay ** (attempt + 1))
                
        raise Exception("Failed to get response from Gemini API")

    async def generate_text(self, messages: List[Dict[str, str]], model: Optional[str] = None, max_tokens: int = 4000, temperature: float = 0.2) -> str:
        gemini_msgs, sys_inst = self._convert_messages(messages)
        target_model = model or self.default_model
        
        payload = {
            "contents": gemini_msgs,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }
        
        if sys_inst:
            payload["systemInstruction"] = sys_inst
            
        content = await self._execute_request(payload, target_model)
        return content.strip()

    async def generate_structured_output(self, messages: List[Dict[str, str]], pydantic_schema: Type[BaseModel], model: Optional[str] = None, max_tokens: int = 4000, temperature: float = 0.2) -> BaseModel:
        gemini_msgs, sys_inst = self._convert_messages(messages)
        target_model = model or self.default_model
        
        # Native structured JSON output configuration for Gemini
        schema_dict = pydantic_schema.model_json_schema()
        
        payload = {
            "contents": gemini_msgs,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "responseMimeType": "application/json",
                # Gemini maps Pydantic compatible JSON Schemas natively
            }
        }
        
        # In Gemini API, it natively converts to "application/json" output if schema is forced manually into a prompt 
        # Or using native schema payload "responseSchema": schema_dict inside generationConfig. 
        # To be robust across multiple minor versions, we inject instruction.
        schema_dump = json.dumps(schema_dict)
        schema_instruction = f" You MUST return a JSON object that strictly adheres to this JSON schema: {schema_dump}. Do not include markdown formatting or extra text."
        
        if sys_inst:
            sys_inst["parts"][0]["text"] += schema_instruction
        else:
            sys_inst = {"parts": [{"text": f"You are a strict JSON data generator.{schema_instruction}"}]}
            
        payload["systemInstruction"] = sys_inst
        
        content = await self._execute_request(payload, target_model)
        
        try:
            return pydantic_schema.model_validate_json(content)
        except Exception as e:
            self.logger.error(f"Pydantic mapping failed on Gemini response: {e}")
            raise Exception(f"Failed to match Pydantic schema: {str(e)}. Raw content: {content}")

    async def async_close(self):
        if self.session and not self.session.closed:
            await self.session.close()
