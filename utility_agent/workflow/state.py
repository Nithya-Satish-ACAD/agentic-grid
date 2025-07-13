from typing import TypedDict, List
from ..api.models import UtilityState as BaseUtilityState, DERStatus, FlexibilityPlan, Conflict

class AgentState(TypedDict):
    utility_state: BaseUtilityState
    latest_statuses: List[DERStatus]
    active_plans: List[FlexibilityPlan]
    unresolved_conflicts: List[Conflict]
    # Add more state fields as needed for workflow
# Note: State supports multiple DER types via DERAgent.type
