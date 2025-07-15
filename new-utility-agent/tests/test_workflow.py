import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
import pytest
from utility_agent.adapters.eventbus import EventBus, Message
from utility_agent.workflow.graph import build_graph
from utility_agent.workflow.state import AgentState
from utility_agent.api.models import FlexibilityPlan, DERStatus, BaseUtilityState
import datetime

@pytest.mark.asyncio
async def test_agent_communication():
    # Setup event bus
    bus = EventBus()
    await bus.connect()

    # Simulate Solar Agent subscriber
    received = []
    async def solar_callback(data):
        received.append(data)
        # Simulate response: publish status update
        status = DERStatus(agent_id=data['agent_id'], power_output=50.0, flexibility=10.0)
        await bus.publish("solar.status", status)

    await bus.subscribe("utility.curtailment", solar_callback)

    # Utility Agent: run workflow to send curtailment
    graph = build_graph()
    initial_state = AgentState(
        utility_state=BaseUtilityState(),
        latest_statuses=[],
        active_plans=[FlexibilityPlan(agent_id="solar_1", amount=20.0, duration=15, start_time=datetime.datetime.utcnow(), status="pending")],
        unresolved_conflicts=[]
    )
    # Subscribe to status updates in Utility Agent
    utility_received = []
    async def utility_callback(data):
        utility_received.append(data)
        # Update state (simplified)
        initial_state['latest_statuses'].append(DERStatus(**data))

    await bus.subscribe("solar.status", utility_callback)

    # Run the graph (focusing on send_curtailment)
    await graph.ainvoke(initial_state)  # Assuming async invocation

    # Wait for messages
    await asyncio.sleep(2)

    assert len(received) > 0
    assert received[0]['agent_id'] == "solar_1"
    assert len(utility_received) > 0
    assert utility_received[0]['agent_id'] == "solar_1"

    await bus.close()
