"""Google Gemini LLM provider implementation."""

import json
import logging
from typing import Dict, Any, Optional, List

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from .base import BaseLLMProvider, LLMResponse, LLMConfig

logger = logging.getLogger(__name__)


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM provider."""
    
    def __init__(self, config: LLMConfig):
        """Initialize Gemini provider."""
        super().__init__(config)
        
        if not GEMINI_AVAILABLE:
            raise ImportError("Google AI package not installed. Run: pip install google-generativeai")
        
        if not config.api_key:
            raise ValueError("Google AI API key is required")
        
        genai.configure(api_key=config.api_key)
        
        # Configure generation settings
        self.generation_config = {
            "temperature": config.temperature,
            "max_output_tokens": config.max_tokens,
        }
        
        # Default models for Gemini
        self.supported_models = [
            # "gemini-1.5-pro",
            # "gemini-1.5-flash",
            # "gemini-1.0-pro",
            # "gemini-pro",
            "models/gemini-2.5-flash"
        ]
        
        self.model = genai.GenerativeModel(config.model)
    
    async def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response using Gemini."""
        try:
            # Combine system prompt with user prompt if provided
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
            
            # Merge generation config with kwargs
            config = {**self.generation_config, **kwargs}
            
            response = await self.model.generate_content_async(
                full_prompt,
                generation_config=config
            )
            
            return LLMResponse(
                content=response.text,
                usage={
                    "prompt_tokens": response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
                    "completion_tokens": response.usage_metadata.candidates_token_count if response.usage_metadata else 0,
                    "total_tokens": response.usage_metadata.total_token_count if response.usage_metadata else 0
                },
                model=self.config.model,
                provider="gemini",
                metadata={
                    "finish_reason": response.candidates[0].finish_reason.name if response.candidates else None,
                    "safety_ratings": [rating.category.name for rating in response.candidates[0].safety_ratings] if response.candidates else []
                }
            )
            
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise
    
    async def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate structured JSON response using Gemini."""
        try:
            # Add JSON schema instruction
            json_instruction = f"\nRespond with valid JSON matching this schema: {json.dumps(schema)}"
            enhanced_prompt = prompt + json_instruction
            
            response = await self.generate(
                prompt=enhanced_prompt,
                system_prompt=system_prompt,
                **kwargs
            )
            
            # Parse JSON response
            return json.loads(response.content)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini JSON response: {e}")
            raise ValueError(f"Invalid JSON response from Gemini: {e}")
        except Exception as e:
            logger.error(f"Gemini structured generation failed: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check Gemini API health."""
        try:
            response = await self.model.generate_content_async(
                "ping",
                generation_config={"max_output_tokens": 1, "temperature": 0}
            )
            return response.text is not None
        except Exception as e:
            logger.warning(f"Gemini health check failed: {e}")
            return False
    
    def get_supported_models(self) -> List[str]:
        """Get supported Gemini models."""
        return self.supported_models
    
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost for Gemini request."""
        # Pricing as of 2024 (approximate, check current pricing)
        pricing = {
            "gemini-1.5-pro": {"input": 0.0035, "output": 0.0105},
            "gemini-1.5-flash": {"input": 0.00035, "output": 0.00105},
            "gemini-1.0-pro": {"input": 0.0005, "output": 0.0015},
            "gemini-pro": {"input": 0.0005, "output": 0.0015}
        }
        
        model_pricing = pricing.get(self.config.model, pricing["gemini-pro"])
        
        input_cost = (prompt_tokens / 1000) * model_pricing["input"]
        output_cost = (completion_tokens / 1000) * model_pricing["output"]
        
        return input_cost + output_cost 