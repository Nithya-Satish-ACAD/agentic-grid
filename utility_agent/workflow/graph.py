from langgraph.graph import StateGraph, END
from utility_agent.workflow.nodes import (
    collect_status,
    negotiate_flexibility,
    conflict_resolver,
    send_curtailment,
    monitor_ack,
    alert_operator,
    handle_blackout,
    update_forecast,
)
from utility_agent.workflow.state import AgentState

def build_graph() -> StateGraph:
    workflow = StateGraph(AgentState)

    workflow.add_node("collect_status", collect_status)
    workflow.add_node("negotiate_flexibility", negotiate_flexibility)
    workflow.add_node("conflict_resolver", conflict_resolver)
    workflow.add_node("send_curtailment", send_curtailment)
    workflow.add_node("monitor_ack", monitor_ack)
    workflow.add_node("alert_operator", alert_operator)
    workflow.add_node("handle_blackout", handle_blackout)
    workflow.add_node("update_forecast", update_forecast)

    # Define edges (simplified flow)
    workflow.set_entry_point("collect_status")
    workflow.add_edge("collect_status", "negotiate_flexibility")
    workflow.add_edge("negotiate_flexibility", "conflict_resolver")
    workflow.add_edge("conflict_resolver", "send_curtailment")
    workflow.add_edge("send_curtailment", "monitor_ack")
    workflow.add_conditional_edges(
        "monitor_ack",
        lambda state: "alert_operator" if any(plan.status != "confirmed" for plan in state['active_plans']) else "update_forecast",
    )
    workflow.add_edge("alert_operator", "handle_blackout")
    workflow.add_edge("handle_blackout", END)
    workflow.add_edge("update_forecast", END)

    return workflow.compile()
