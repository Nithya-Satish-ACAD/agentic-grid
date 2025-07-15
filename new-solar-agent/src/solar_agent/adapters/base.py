from abc import ABC, abstractmethod
from typing import Any

from solar_agent.core.models import SunSpecData


class BaseAdapter(ABC):
    """Abstract base class for all adapters."""

    @abstractmethod
    def __init__(self, **kwargs: Any) -> None:
        """Initialize the adapter."""
        pass


class HardwareAdapter(BaseAdapter):
    """Abstract base class for a hardware adapter."""

    @abstractmethod
    def get_data(self) -> SunSpecData:
        """
        Retrieves the current data from the hardware.

        Returns:
            A SunSpecData object representing the hardware's state.
        """
        pass

    @abstractmethod
    def set_curtailment(self, level: float) -> bool:
        """
        Sets the curtailment level on the hardware.

        Args:
            level: The curtailment percentage (0.0 to 100.0).

        Returns:
            True if the command was successful, False otherwise.
        """
        pass

    @abstractmethod
    def clear_fault(self) -> bool:
        """
        Clears any active fault condition on the hardware.

        Returns:
            True if the command was successful, False otherwise.
        """
        pass 