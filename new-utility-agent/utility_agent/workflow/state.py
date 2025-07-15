"""
Defines the state for the Utility Agent's workflow.

The state is represented by a Pydantic model, which allows for type-safe
access and manipulation of the data within the workflow graph.
"""
from utility_agent.api.models import UtilityState

# The UtilityState Pydantic model serves as the schema for our graph's state.
# LangGraph will manage an instance of this class as the state object that
# is passed between nodes in the workflow.

# For clarity, we can alias it if we want, but it's not necessary.
WorkflowState = UtilityState 