import aiohttp
from typing import Optional
from llm.providers.openai_provider import OpenAIProvider

class PerplexityProvider(OpenAIProvider):
    """
    Perplexity's REST API natively supports exact compatibility with the OpenAI Chat Completion spec.
    We elegantly extend the structure natively via subclass logic while overriding specific endpoints. 
    """
    def __init__(self, api_key: str, default_model: str):
        super().__init__(api_key, default_model)
        self.base_url = "https://api.perplexity.ai"

    # Perplexity automatically inherits _execute_request, generate_text, and generate_structured_output.
    # Note: Their structured output support for `response_format` JSON schema compatibility depends on the 
    # exact model being used. Like Anthropic, we could fallback if needed, but since Perplexity models 
    # (like llama-3.1-sonar) support OpenAI's schema or sys-prompts, the inherited base will perform natively.
