import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import asyncio
import json
import logging
from typing import Any, Callable, Dict
import nats
from nats.errors import ConnectionClosedError, TimeoutError
from pydantic import BaseModel, ValidationError
from utility_agent.config import Config

logger = logging.getLogger(__name__)

class EventBus:
    def __init__(self):
        self.nc = None

    async def connect(self):
        try:
            self.nc = await nats.connect(Config.EVENT_BUS_URL)
            logger.info(f"Connected to NATS at {Config.EVENT_BUS_URL}")
        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")
            raise

    async def publish(self, topic: str, payload: BaseModel):
        if not self.nc:
            await self.connect()
        try:
            data = payload.model_dump_json().encode()
            await self.nc.publish(topic, data)
            logger.info(f"Published to {topic}")
        except (ConnectionClosedError, TimeoutError) as e:
            logger.error(f"Publish error: {e}")
            raise

    async def subscribe(self, topic: str, callback: Callable[[Dict[str, Any]], None]):
        if not self.nc:
            await self.connect()
        async def handler(msg):
            try:
                data = json.loads(msg.data.decode())
                callback(data)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
            except ValidationError as e:
                logger.error(f"Validation error: {e}")

        await self.nc.subscribe(topic, cb=handler)
        logger.info(f"Subscribed to {topic}")

    async def close(self):
        if self.nc:
            await self.nc.close()
            logger.info("NATS connection closed")

# Example Pydantic model for messages (expand as needed)
class Message(BaseModel):
    type: str
    data: Dict[str, Any]

# Test harness for cross-host messaging
def test_harness():
    async def run_test():
        bus = EventBus()
        await bus.connect()

        # Subscriber example (simulates Solar Agent)
        async def callback(data):
            logger.info(f"Received message: {data}")

        await bus.subscribe("solar.status", callback)

        # Publisher example (simulates Utility Agent)
        payload = Message(type="curtailment", data={"amount": 50})
        await bus.publish("utility.curtailment", payload)

        # Keep running for 10 seconds to receive messages
        await asyncio.sleep(10)
        await bus.close()

    asyncio.run(run_test())

if __name__ == "__main__":
    test_harness()

# Predefined topics
TOPICS = {
    'solar.status': 'solar.status',
    'utility.curtailment': 'utility.curtailment',
    'battery.status': 'battery.status',
    'load.status': 'load.status',
    'battery.curtailment': 'battery.curtailment',
    'load.curtailment': 'load.curtailment',
}
