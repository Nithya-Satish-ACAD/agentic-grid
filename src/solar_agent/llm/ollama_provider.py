"""Ollama LLM provider for local models."""

import json
import logging
from typing import Dict, Any, Optional, List
import httpx

from .base import BaseLLMProvider, LLMResponse, LLMConfig

logger = logging.getLogger(__name__)


class OllamaProvider(BaseLLMProvider):
    """Ollama provider for local LLMs."""
    
    def __init__(self, config: LLMConfig):
        """Initialize Ollama provider."""
        super().__init__(config)
        
        # Default Ollama API base URL
        self.api_base = config.api_base or "http://localhost:11434"
        
        # Popular Ollama models
        self.supported_models = [
            "llama3.1",
            "llama3.1:70b",
            "llama3.2", 
            "llama3.2:3b",
            "codellama",
            "codellama:13b",
            "mistral",
            "mistral:7b",
            "mixtral",
            "phi3",
            "gemma2",
            "qwen2.5",
            "solar"
        ]
    
    async def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response using Ollama."""
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                payload = {
                    "model": self.config.model,
                    "prompt": prompt,
                    "options": {
                        "temperature": self.config.temperature,
                        "num_predict": self.config.max_tokens or -1,
                    },
                    "stream": False,
                    **kwargs
                }
                
                if system_prompt:
                    payload["system"] = system_prompt
                
                response = await client.post(
                    f"{self.api_base}/api/generate",
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                
                return LLMResponse(
                    content=result["response"],
                    usage={
                        "prompt_tokens": result.get("prompt_eval_count", 0),
                        "completion_tokens": result.get("eval_count", 0),
                        "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
                    },
                    model=self.config.model,
                    provider="ollama",
                    metadata={
                        "eval_duration": result.get("eval_duration"),
                        "load_duration": result.get("load_duration"),
                        "total_duration": result.get("total_duration")
                    }
                )
                
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise
    
    async def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate structured JSON response using Ollama."""
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
            logger.error(f"Failed to parse Ollama JSON response: {e}")
            raise ValueError(f"Invalid JSON response from Ollama: {e}")
        except Exception as e:
            logger.error(f"Ollama structured generation failed: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check Ollama API health."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.api_base}/api/tags")
                response.raise_for_status()
                return True
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False
    
    async def list_models(self) -> List[str]:
        """List available models from Ollama."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.api_base}/api/tags")
                response.raise_for_status()
                result = response.json()
                return [model["name"] for model in result.get("models", [])]
        except Exception as e:
            logger.warning(f"Failed to list Ollama models: {e}")
            return self.supported_models
    
    def get_supported_models(self) -> List[str]:
        """Get supported Ollama models."""
        return self.supported_models
    
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost for Ollama request (local models are free)."""
        return 0.0  # Local models don't have usage costs 