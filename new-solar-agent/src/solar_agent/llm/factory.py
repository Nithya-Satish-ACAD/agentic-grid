"""LLM provider factory."""

import logging
from typing import Dict, Type, Optional

from .base import BaseLLMProvider, LLMConfig
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiProvider
from .ollama_provider import OllamaProvider

logger = logging.getLogger(__name__)


class LLMFactory:
    """Factory for creating LLM providers."""
    
    _providers: Dict[str, Type[BaseLLMProvider]] = {
        "openai": OpenAIProvider,
        "gemini": GeminiProvider,
        "google": GeminiProvider,  # Alias for gemini
        "ollama": OllamaProvider,
    }
    
    @classmethod
    def create_provider(cls, config: LLMConfig) -> BaseLLMProvider:
        """Create an LLM provider based on configuration.
        
        Args:
            config: LLM configuration
            
        Returns:
            Configured LLM provider instance
            
        Raises:
            ValueError: If provider is not supported
        """
        provider_name = config.provider.lower()
        
        if provider_name not in cls._providers:
            raise ValueError(
                f"Unsupported LLM provider: {provider_name}. "
                f"Supported providers: {list(cls._providers.keys())}"
            )
        
        provider_class = cls._providers[provider_name]
        
        try:
            return provider_class(config)
        except Exception as e:
            logger.error(f"Failed to create {provider_name} provider: {e}")
            raise
    
    @classmethod
    def register_provider(cls, name: str, provider_class: Type[BaseLLMProvider]):
        """Register a custom LLM provider.
        
        Args:
            name: Provider name
            provider_class: Provider class
        """
        cls._providers[name.lower()] = provider_class
        logger.info(f"Registered custom LLM provider: {name}")
    
    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """Get list of supported provider names.
        
        Returns:
            List of provider names
        """
        return list(cls._providers.keys())


def create_llm_provider(
    provider: str,
    model: str,
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    temperature: float = 0.1,
    max_tokens: Optional[int] = None,
    timeout: int = 30,
    **extra_params
) -> BaseLLMProvider:
    """Convenience function to create an LLM provider.
    
    Args:
        provider: Provider name (openai, gemini, ollama)
        model: Model name
        api_key: API key (if required)
        api_base: API base URL (for custom endpoints)
        temperature: Generation temperature
        max_tokens: Maximum tokens to generate
        timeout: Request timeout in seconds
        **extra_params: Additional provider-specific parameters
        
    Returns:
        Configured LLM provider instance
    """
    config = LLMConfig(
        provider=provider,
        model=model,
        api_key=api_key,
        api_base=api_base,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        extra_params=extra_params
    )
    
    return LLMFactory.create_provider(config) 