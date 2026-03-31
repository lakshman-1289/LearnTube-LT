import os
import logging
from typing import Dict, Type
from llm.base import BaseLLMProvider

# Placeholder imports - these will be fully defined in step 2.
from llm.providers.groq_provider import GroqProvider
from llm.providers.openai_provider import OpenAIProvider
from llm.providers.gemini_provider import GeminiProvider
from llm.providers.anthropic_provider import AnthropicProvider
from llm.providers.perplexity_provider import PerplexityProvider

logger = logging.getLogger("LLMFactory")

class LLMFactory:
    """
    Decides at runtime which LLM provider to instantiate based on environment variables.
    Defaults to Groq if LLM_PROVIDER is not explicitly specified.
    """
    
    _providers_map: Dict[str, Type[BaseLLMProvider]] = {
        "groq": GroqProvider,
        "openai": OpenAIProvider,
        "gemini": GeminiProvider,
        "anthropic": AnthropicProvider,
        "perplexity": PerplexityProvider
    }
    
    @classmethod
    def create_provider(cls, forced_provider: str | None = None) -> BaseLLMProvider:
        provider_name = forced_provider or os.getenv("LLM_PROVIDER", "groq").lower()
        
        provider_class = cls._providers_map.get(provider_name)
        if not provider_class:
            logger.warning(f"Provider '{provider_name}' not found, falling back to 'groq'")
            provider_name = "groq"
            provider_class = GroqProvider
            
        # Determine specific keys and models per provider for fallback abstraction
        if provider_name == "groq":
            api_key = os.getenv("GROQ_API_KEY")
            model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        elif provider_name == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        elif provider_name == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        elif provider_name == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest")
        elif provider_name == "perplexity":
            api_key = os.getenv("PERPLEXITY_API_KEY")
            model = os.getenv("PERPLEXITY_MODEL", "llama-3.1-sonar-large-128k-online")
        else:
            raise ValueError(f"Unknown provider routing config: {provider_name}")
            
        if not api_key:
            raise ValueError(f"CRITICAL: Implementation failed! {provider_name.upper()}_API_KEY is missing in env.")
            
        logger.info(f"Instantiating {provider_name.capitalize()} provider using model '{model}'")
        return provider_class(api_key=api_key, default_model=model)
