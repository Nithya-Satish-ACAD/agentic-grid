from .base import LLMProvider
from .gemini_provider import GeminiProvider
from .openrouter_provider import OpenRouterProvider
from ..config import Config

def get_llm_provider() -> LLMProvider:
    """
    Factory function to get an instance of an LLM provider based on config.

    Returns:
        An instance of the specified LLM provider.

    Raises:
        ValueError: If an unsupported provider name is given.
    """
    provider_name = Config.LLM_PROVIDER.lower()
    
    if provider_name == "gemini":
        return GeminiProvider()
    elif provider_name == "openrouter":
        return OpenRouterProvider()
    else:
        raise ValueError(f"Unsupported LLM provider: {provider_name}") 