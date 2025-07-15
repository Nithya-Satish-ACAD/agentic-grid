"""
LLM provider implementation for OpenRouter.
"""
import httpx
import logging
from .base import LLMProvider
from ..config import Config

logger = logging.getLogger(__name__)

class OpenRouterProvider(LLMProvider):
    """An LLM provider that uses the OpenRouter API."""

    def __init__(self):
        self.api_key = Config.OPENROUTER_API_KEY
        self.model = Config.OPENROUTER_MODEL
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set.")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if Config.OPENROUTER_SITE_URL:
            self.headers["HTTP-Referer"] = Config.OPENROUTER_SITE_URL
        if Config.OPENROUTER_SITE_NAME:
            self.headers["X-Title"] = Config.OPENROUTER_SITE_NAME
            
        self._client = httpx.AsyncClient(
            base_url="https://openrouter.ai/api/v1",
            headers=self.headers,
            timeout=30
        )
        logger.info(f"OpenRouter provider initialized with model: {self.model}")

    async def generate(self, prompt: str) -> str:
        """
        Generates a response from OpenRouter based on a given prompt.
        """
        logger.debug(f"Sending prompt to OpenRouter: {prompt}")
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }
        try:
            response = await self._client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            logger.debug(f"Received from OpenRouter: {content}")
            return content
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from OpenRouter: {e.response.status_code} - {e.response.text}")
            raise
        except (httpx.RequestError, KeyError, IndexError) as e:
            logger.error(f"Error processing OpenRouter response: {e}")
            raise 