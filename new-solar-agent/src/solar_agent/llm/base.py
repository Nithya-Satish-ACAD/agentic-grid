"""Base LLM provider interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Standardized LLM response format."""
    content: str
    usage: Optional[Dict[str, int]] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class LLMConfig:
    """LLM configuration settings."""
    provider: str
    model: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    timeout: int = 30
    extra_params: Optional[Dict[str, Any]] = None


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: LLMConfig):
        """Initialize the LLM provider.
        
        Args:
            config: LLM configuration settings
        """
        self.config = config
        self.provider_name = config.provider
        
    @abstractmethod
    async def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate a response from the LLM.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLMResponse with generated content
        """
        pass
    
    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a structured response (JSON) from the LLM.
        
        Args:
            prompt: The user prompt
            schema: JSON schema for structured output
            system_prompt: Optional system prompt
            **kwargs: Additional parameters
            
        Returns:
            Structured data matching the schema
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the LLM provider is available.
        
        Returns:
            True if provider is healthy, False otherwise
        """
        pass
    
    def get_supported_models(self) -> List[str]:
        """Get list of supported models for this provider.
        
        Returns:
            List of model names
        """
        return ["default"]
    
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost for the request.
        
        Args:
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens
            
        Returns:
            Estimated cost in USD
        """
        return 0.0  # Override in specific providers 