from abc import ABC, abstractmethod

class LLMProvider(ABC):
    """Abstract base class for a generic LLM provider."""

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """
        Generates a response from the LLM based on a given prompt.

        Args:
            prompt: The input prompt for the LLM.

        Returns:
            The text response from the LLM.
        """
        pass 