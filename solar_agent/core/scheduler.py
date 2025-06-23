"""
Scheduler for periodic Solar Agent tasks.

This module manages the periodic execution of reading collection,
forecasting, anomaly detection, and reporting tasks.
See backend-structure.md for detailed specification.
"""

import asyncio
from typing import Optional, Callable, Any
from datetime import datetime


class Scheduler:
    """Manages periodic task execution for Solar Agent."""
    
    def __init__(self, interval_seconds: int = 300):
        """
        Initialize scheduler.
        
        Args:
            interval_seconds: Interval between task executions in seconds
        """
        self.interval_seconds = interval_seconds
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
        self.callbacks: dict[str, Callable] = {}
        
    async def start(self) -> None:
        """Start the periodic task scheduler."""
        if self.is_running:
            return
            
        self.is_running = True
        self.task = asyncio.create_task(self._run_periodic_loop())
        
    async def stop(self) -> None:
        """Stop the periodic task scheduler."""
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
                
    def register_callback(self, name: str, callback: Callable) -> None:
        """
        Register a callback function to be called during periodic execution.
        
        Args:
            name: Name of the callback
            callback: Async function to call
        """
        self.callbacks[name] = callback
        
    async def _run_periodic_loop(self) -> None:
        """Main periodic execution loop."""
        while self.is_running:
            try:
                # Execute all registered callbacks
                await self._execute_callbacks()
                
                # Wait for next interval
                await asyncio.sleep(self.interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                # TODO: Add proper error handling and logging
                # TODO: Implement exponential backoff for repeated failures
                print(f"Error in periodic loop: {e}")
                await asyncio.sleep(10)  # Brief pause before retry
                
    async def _execute_callbacks(self) -> None:
        """Execute all registered callbacks in sequence."""
        for name, callback in self.callbacks.items():
            try:
                await callback()
            except Exception as e:
                # TODO: Add proper error handling per callback
                print(f"Error executing callback {name}: {e}")
                
    def get_status(self) -> dict[str, Any]:
        """
        Get current scheduler status.
        
        Returns:
            Dictionary with scheduler status information
        """
        return {
            'is_running': self.is_running,
            'interval_seconds': self.interval_seconds,
            'registered_callbacks': list(self.callbacks.keys()),
            'last_execution': datetime.utcnow().isoformat() if self.is_running else None
        } 