"""Mock solar data generator for development and testing."""

import threading
import time
import math
import random
from solar_agent.core.models import SunSpecData, SunSpecInverterStatus

class SunSpecDataGenerator:
    """
    Simulates a live feed of SunSpec data for a solar inverter.
    This class runs in a background thread to continuously update a SunSpecData
    object, simulating a realistic day/night cycle and allowing for the injection
    of specific events like faults or curtailment.
    """
    def __init__(self, nameplate_power: float = 5000.0, fault_probability: float = 0.01):
        # The core data object, starts with default values
        self._data = SunSpecData(
            nameplate_power=nameplate_power,
            inverter_status=SunSpecInverterStatus.NORMAL,
            ac_power=0.0,
            daily_yield=0.0,
            dc_voltage=0.0,
            irradiance=0.0,
            ambient_temp=20.0,
            fault_message=None
        )
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._simulation_thread = threading.Thread(target=self._run_simulation, daemon=True)
        self._day_cycle_seconds = 60  # Complete day/night cycle every 60 seconds
        self._is_curtailed = False
        self._curtailment_level_percent = 0.0
        self._fault_probability = fault_probability

    def get_data(self) -> SunSpecData:
        """Returns a thread-safe copy of the current SunSpec data."""
        with self._lock:
            # If curtailed, ensure the reported power respects the curtailment limit
            if self._is_curtailed:
                # Create a copy to modify before returning
                data_copy = self._data.copy(deep=True)
                # Curtailment is a percentage of nameplate power
                curtailment_limit = self._data.nameplate_power * (1 - self._curtailment_level_percent / 100.0)
                data_copy.ac_power = min(self._data.ac_power, curtailment_limit)
                return data_copy
            return self._data.copy(deep=True)

    def start(self):
        """Starts the background simulation thread."""
        if not self._simulation_thread.is_alive():
            self._stop_event.clear()
            self._simulation_thread.start()

    def stop(self):
        """Stops the background simulation thread."""
        self._stop_event.set()
        if self._simulation_thread.is_alive():
            self._simulation_thread.join()

    def trigger_fault(self, message: str = "Grid Voltage Out of Range"):
        """Injects a fault condition into the simulation."""
        with self._lock:
            self._data.inverter_status = SunSpecInverterStatus.FAULT
            self._data.fault_message = message
            self._data.ac_power = 0.0 # When a fault occurs, power drops to zero

    def clear_fault(self):
        """Resets the inverter status to NORMAL."""
        with self._lock:
            self._data.inverter_status = SunSpecInverterStatus.NORMAL
            self._data.fault_message = None
            self._is_curtailed = False
            self._curtailment_level_percent = 0.0

    def set_curtailment(self, level: float):
        """
        Sets the curtailment level. A level of 100.0 means full curtailment (zero power).
        A level of 0.0 means no curtailment.

        Args:
            level: The percentage of power to curtail (0.0 to 100.0).
        """
        with self._lock:
            if 0.0 <= level <= 100.0:
                self._is_curtailed = level > 0
                self._curtailment_level_percent = level
            # Power output is adjusted in the simulation loop and get_data

    def _run_simulation(self):
        """The main simulation loop, which runs in a separate thread."""
        start_time = time.time()
        while not self._stop_event.is_set():
            # Calculate progress through the day/night cycle
            cycle_progress = (time.time() - start_time) % self._day_cycle_seconds / self._day_cycle_seconds
            
            # Simulate irradiance with a sine wave (0 at night, 1000 at peak day)
            irradiance = max(0, 1000 * math.sin(cycle_progress * math.pi))

            with self._lock:
                # Randomly trigger a fault based on probability
                if random.random() < self._fault_probability:
                    self.trigger_fault()

                # If a fault is active, power is 0 and we don't update further
                if self._data.inverter_status == SunSpecInverterStatus.FAULT:
                    self._data.ac_power = 0
                    time.sleep(1)
                    continue

                # Calculate potential power based on irradiance
                potential_power = 0.0
                if irradiance > 0:
                    self._data.inverter_status = SunSpecInverterStatus.NORMAL
                    efficiency_factor = 0.9 + random.uniform(-0.02, 0.02)
                    potential_power = round(irradiance * (self._data.nameplate_power / 1000) * efficiency_factor, 2)
                    self._data.dc_voltage = round(300 + irradiance * 0.1, 2)
                else:
                    self._data.inverter_status = SunSpecInverterStatus.STANDBY
                    self._data.dc_voltage = 0.0
                
                # If curtailed, the final power is the minimum of potential and the limit
                if self._is_curtailed:
                    curtailment_limit = self._data.nameplate_power * (1 - self._curtailment_level_percent / 100.0)
                    self._data.ac_power = min(potential_power, curtailment_limit)
                else:
                    self._data.ac_power = potential_power

                # Update other values
                self._data.irradiance = round(irradiance, 2)
                self._data.ambient_temp = round(20 + 10 * math.sin(cycle_progress * math.pi), 2)
                
                # Update daily yield (integrating power over time)
                self._data.daily_yield += self._data.ac_power / 3600 # Convert W to Wh, then add to kWh
                self._data.daily_yield = round(self._data.daily_yield, 4)
            
            time.sleep(1)