import os
import google.generativeai as genai
from .base import LLMProvider

class GeminiProvider(LLMProvider):
    """LLM provider implementation for Google's Gemini models."""

    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        genai.configure(api_key=self.api_key)
        # Configure the model to output JSON
        self.model = genai.GenerativeModel(
            model_name,
            generation_config={"response_mime_type": "application/json"},
        )

    async def generate(self, prompt: str) -> str:
        """
        Generates a response from the Gemini model.

        Args:
            prompt: The input prompt for the LLM.

        Returns:
            The text response from the LLM.
        """
        response = await self.model.generate_content_async(prompt)
        return response.text 