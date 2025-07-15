from .base import HardwareAdapter
from solar_agent.tools.data_generator import SunSpecDataGenerator
from solar_agent.core.models import SunSpecData

class MockAdapter(HardwareAdapter):
    """
    A mock hardware adapter that uses the SunSpecDataGenerator to simulate
    a solar inverter.
    """

    def __init__(self, config: dict):
        """
        Initializes the MockAdapter.

        Args:
            config: A dictionary containing configuration for the data generator,
                    such as 'nameplate_power' and 'fault_probability'.
        """
        self.generator = SunSpecDataGenerator(
            nameplate_power=config.get("nameplate_power", 5000.0),
            fault_probability=config.get("fault_probability", 0.01)
        )

    def get_data(self) -> SunSpecData:
        """Retrieves the latest simulated data."""
        return self.generator.get_data()

    def set_curtailment(self, level: float) -> bool:
        """Sets the curtailment level on the simulator."""
        self.generator.set_curtailment(level)
        return True

    def clear_fault(self) -> bool:
        """Clears any active fault on the simulator."""
        self.generator.clear_fault()
        return True 