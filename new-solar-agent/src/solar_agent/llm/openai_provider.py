"""OpenAI LLM provider implementation."""

import json
import logging
from typing import Dict, Any, Optional, List

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .base import BaseLLMProvider, LLMResponse, LLMConfig

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider."""
    
    def __init__(self, config: LLMConfig):
        """Initialize OpenAI provider."""
        super().__init__(config)
        
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package not installed. Run: pip install openai")
        
        if not config.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = openai.AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.api_base,
            timeout=config.timeout
        )
        
        # Default models for OpenAI
        self.supported_models = [
            "gpt-4o",
            "gpt-4o-mini", 
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k"
        ]
    
    async def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response using OpenAI."""
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            # Merge config params with kwargs
            params = {
                "model": self.config.model,
                "messages": messages,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                **kwargs
            }
            
            response = await self.client.chat.completions.create(**params)
            
            return LLMResponse(
                content=response.choices[0].message.content,
                usage=response.usage.model_dump() if response.usage else None,
                model=response.model,
                provider="openai",
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "response_id": response.id
                }
            )
            
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise
    
    async def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate structured JSON response using OpenAI."""
        try:
            # Add JSON schema instruction to system prompt
            json_instruction = f"\nRespond with valid JSON matching this schema: {json.dumps(schema)}"
            enhanced_system = (system_prompt or "") + json_instruction
            
            # Use function calling for better structured output
            if "tools" not in kwargs and "functions" not in kwargs:
                kwargs["response_format"] = {"type": "json_object"}
            
            response = await self.generate(
                prompt=prompt,
                system_prompt=enhanced_system,
                **kwargs
            )
            
            # Parse JSON response
            return json.loads(response.content)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI JSON response: {e}")
            raise ValueError(f"Invalid JSON response from OpenAI: {e}")
        except Exception as e:
            logger.error(f"OpenAI structured generation failed: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check OpenAI API health."""
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1,
                temperature=0
            )
            return response.choices[0].message.content is not None
        except Exception as e:
            logger.warning(f"OpenAI health check failed: {e}")
            return False
    
    def get_supported_models(self) -> List[str]:
        """Get supported OpenAI models."""
        return self.supported_models
    
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost for OpenAI request."""
        # Pricing as of 2024 (approximate, check current pricing)
        pricing = {
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
            "gpt-3.5-turbo-16k": {"input": 0.003, "output": 0.004}
        }
        
        model_pricing = pricing.get(self.config.model, pricing["gpt-3.5-turbo"])
        
        input_cost = (prompt_tokens / 1000) * model_pricing["input"]
        output_cost = (completion_tokens / 1000) * model_pricing["output"]
        
        return input_cost + output_cost 