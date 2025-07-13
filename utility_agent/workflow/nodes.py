import logging
from typing import Dict, Any
from langgraph.graph import StateGraph
from utility_agent.adapters.eventbus import EventBus
from ..api.models import DERStatus, FlexibilityPlan, Conflict, Commitment
from .state import AgentState
import datetime

logger = logging.getLogger(__name__)
event_bus = EventBus()

def collect_status(state: AgentState) -> Dict[str, Any]:
    # Simulate aggregating from event bus (in real: listen via subscribe)
    new_status = DERStatus(agent_id="solar_1", power_output=100.0, flexibility=20.0)
    state['latest_statuses'].append(new_status)
    logger.info("Collected new status")
    return state

def negotiate_flexibility(state: AgentState) -> Dict[str, Any]:
    # Stub for future Beckn integration
    plan = FlexibilityPlan(agent_id="solar_1", amount=10.0, duration=30, start_time=datetime.datetime.utcnow())
    state['active_plans'].append(plan)
    logger.info("Negotiated flexibility plan")
    return state

def conflict_resolver(state: AgentState) -> Dict[str, Any]:
    if state['unresolved_conflicts']:
        conflict = state['unresolved_conflicts'][0]
        conflict.resolved = True
        conflict.resolution = "Resolved by timestamp priority"
        logger.info("Resolved conflict")
    return state

async def send_curtailment(state: AgentState) -> Dict[str, Any]:
    # Publish via event bus
    for plan in state['active_plans']:
        if plan.status == "pending":
            await event_bus.publish("utility.curtailment", plan)
            plan.status = "sent"
    logger.info("Sent curtailment commands")
    return state

def monitor_ack(state: AgentState) -> Dict[str, Any]:
    # Check for acks (stub: assume received after delay)
    for plan in state['active_plans']:
        if plan.status == "sent":
            plan.status = "confirmed"
            # If no ack, fallback to battery or alert
    logger.info("Monitored acknowledgments")
    return state

def alert_operator(state: AgentState) -> Dict[str, Any]:
    state['utility_state'].alerts.append("DER offline detected")
    logger.info("Alerted operator")
    return state

def handle_blackout(state: AgentState) -> Dict[str, Any]:
    state['utility_state'].mode = "blackout"
    # Suspend market flows
    logger.info("Handled blackout: switched to blackout mode")
    return state

def update_forecast(state: AgentState) -> Dict[str, Any]:
    # Adjust plans based on statuses
    logger.info("Updated forecast")
    return state
