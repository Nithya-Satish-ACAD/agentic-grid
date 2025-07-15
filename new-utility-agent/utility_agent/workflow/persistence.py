import json
import os
from typing import Dict, Any
from .state import AgentState
from ..api.models import BaseUtilityState

def save_state(state: AgentState, path: str = "state.json"):
    with open(path, "w") as f:
        json.dump(state, f, default=lambda o: o.__dict__)

def load_state(path: str = "state.json") -> AgentState:
    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
            return AgentState(**data)
    return AgentState(utility_state=BaseUtilityState(), latest_statuses=[], active_plans=[], unresolved_conflicts=[])
