"""
Solar inverter adapters package.

This package contains adapter implementations for different solar inverter types.
"""

from .base import InverterAdapter
from .simulated import SimulatedAdapter

__all__ = ['InverterAdapter', 'SimulatedAdapter'] 