import asyncio
import json
import os
from typing import Dict, List, Optional
import aiohttp


class GroqClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.base_url = "https://api.groq.com/openai/v1"
        self.session: Optional[aiohttp.ClientSession] = None

        if not self.api_key:
            raise ValueError("Groq API key required. Set GROQ_API_KEY in .env")

    async def _get_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4000,
        temperature: float = 0.2,
        response_format: Optional[Dict] = None,
        model: str = "llama-3.3-70b-versatile",
        pydantic_model=None
    ) -> str:
        """
        Send chat completion request to Groq API
        Includes retry logic and timeout handling
        """

        session = await self._get_session()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Automatically inject JSON schema instructions to guide the model if a pydantic model is provided
        if pydantic_model:
            import json
            schema_dump = json.dumps(pydantic_model.model_json_schema())
            schema_instruction = f" You MUST return a JSON object that strictly adheres to this JSON schema: {schema_dump}. Do not include markdown formatting or extra text."
            
            system_msg_idx = next((i for i, m in enumerate(messages) if m["role"] == "system"), -1)
            if system_msg_idx >= 0:
                messages[system_msg_idx]["content"] += schema_instruction
            else:
                messages.insert(0, {"role": "system", "content": f"You are a strict JSON data generator.{schema_instruction}"})

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False
        }

        if response_format:
            payload["response_format"] = response_format

        max_retries = 3
        base_delay = 5

        for attempt in range(max_retries):

            try:
                print(f"🔄 Attempt {attempt+1}/{max_retries} - Sending request to Groq...")

                timeout_seconds = 180 + (attempt * 60)

                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=timeout_seconds)
                ) as response:

                    print(f"📡 Response status: {response.status}")

                    if response.status == 200:
                        data = await response.json()

                        if "choices" not in data or not data["choices"]:
                            raise Exception("Invalid response structure from Groq API")

                        content = data["choices"][0]["message"]["content"]

                        if not content:
                            raise Exception("Empty response from Groq")

                        print(f"✅ Received response ({len(content)} characters)")
                        
                        content = content.strip()
                        
                        # Apply Pydantic validation if a schema is provided
                        if pydantic_model:
                            try:
                                # First we check if it is parseable json
                                import json
                                json_parsed = json.loads(content)
                                # Then validate
                                validated = pydantic_model(**json_parsed)
                                return validated
                            except Exception as e:
                                print(f"⚠️ Pydantic validation failed: {str(e)}")
                                # Optionally append the error to messages for the next retry
                                messages.append({
                                    "role": "assistant",
                                    "content": content
                                })
                                messages.append({
                                    "role": "user",
                                    "content": f"Your previous response failed validation: {str(e)}. Please fix the JSON and follow the schema strictly."
                                })
                                if attempt == max_retries - 1:
                                    raise Exception(f"Failed to match Pydantic schema: {str(e)}")
                                continue

                        return content

                    elif response.status == 429:
                        wait = base_delay ** (attempt + 1)
                        print(f"⚠️ Rate limit hit. Retrying in {wait}s...")
                        await asyncio.sleep(wait)

                    elif response.status == 401:
                        text = await response.text()
                        raise Exception(f"Authentication failed: {text}")

                    else:
                        text = await response.text()
                        print(f"❌ Groq API error {response.status}: {text}")

                        if attempt == max_retries - 1:
                            raise Exception(f"Groq API error {response.status}: {text}")

                        await asyncio.sleep(base_delay ** (attempt + 1))

            except asyncio.TimeoutError:

                print(f"⏰ Request timeout (attempt {attempt+1})")

                if attempt == max_retries - 1:
                    raise Exception("Groq API request timed out")

                await asyncio.sleep(base_delay ** (attempt + 1))

            except aiohttp.ClientError as e:

                print(f"🔌 Network error: {str(e)}")

                if attempt == max_retries - 1:
                    raise Exception(f"Network error: {str(e)}")

                await asyncio.sleep(base_delay ** (attempt + 1))

            except json.JSONDecodeError:

                print("⚠️ Invalid JSON received")

                if attempt == max_retries - 1:
                    raise Exception("Invalid JSON from Groq API")

                await asyncio.sleep(base_delay ** (attempt + 1))

        raise Exception("Failed to get response from Groq API")

    async def test_connection(self) -> Dict[str, str]:
        """
        Test if Groq API works
        """

        try:

            response = await self.chat_completion(
                messages=[{
                    "role": "user",
                    "content": "Reply with 'Connection successful'"
                }],
                max_tokens=50,
                temperature=0
            )

            return {
                "success": True,
                "provider": "Groq",
                "model": "llama-3.3-70b-versatile",
                "response": response
            }

        except Exception as e:

            return {
                "success": False,
                "provider": "Groq",
                "error": str(e)
            }

    async def close_session(self):
        """Close aiohttp session"""

        if self.session and not self.session.closed:
            await self.session.close()
            print("🔌 Groq session closed")

    async def __aenter__(self):
        await self._get_session()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close_session()

    def __del__(self):
        if self.session and not self.session.closed:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.session.close())
            except:
                pass