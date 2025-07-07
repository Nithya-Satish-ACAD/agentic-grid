"""LangGraph workflow definition for Solar Agent."""

import logging
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from solar_agent.workflow.state import WorkflowState
from solar_agent.workflow.nodes import (
    read_solar_data,
    generate_forecast,
    check_performance,
    raise_underperformance_alert,
    await_curtailment,
    apply_curtailment,
    monitor_faults,
    raise_fault_alert,
    maintenance_mode,
)


logger = logging.getLogger(__name__)


def should_generate_forecast(state: WorkflowState) -> str:
    """Conditional logic for forecast generation."""
    if state.error_count > 0:
        return "monitor_faults"
    return "generate_forecast"


def should_check_performance(state: WorkflowState) -> str:
    """Conditional logic for performance checking."""
    if state.error_count > 0:
        return "monitor_faults"
    return "check_performance"


def should_raise_performance_alert(state: WorkflowState) -> str:
    """Conditional logic for performance alert."""
    # This would check the performance_ok flag from check_performance
    performance_ok = getattr(state, 'performance_ok', True)
    if not performance_ok:
        return "raise_underperformance_alert"
    return "await_curtailment"


def should_apply_curtailment(state: WorkflowState) -> str:
    """Conditional logic for curtailment application."""
    if state.active_curtailment:
        return "apply_curtailment"
    return "monitor_faults"


def should_raise_fault_alert(state: WorkflowState) -> str:
    """Conditional logic for fault alert."""
    if state.active_faults and any(f.is_critical for f in state.active_faults):
        return "raise_fault_alert"
    return "handle_maintenance_mode"


def should_continue_or_end(state: WorkflowState) -> str:
    """Conditional logic for workflow continuation."""
    if state.maintenance_mode:
        return "handle_maintenance_mode"
    if state.error_count >= 3:  # Max retries reached
        return END
    return "read_solar_data"  # Continue the loop


def create_solar_agent_graph(
    adapter,
    utility_client=None,
    enable_persistence: bool = True
) -> StateGraph:
    """Create the Solar Agent LangGraph workflow.
    
    Args:
        adapter: Hardware adapter instance
        utility_client: HTTP client for Utility Agent communication
        enable_persistence: Whether to enable state persistence
        
    Returns:
        Configured StateGraph instance
    """
    logger.info("Creating Solar Agent workflow graph")
    
    # Create the state graph
    workflow = StateGraph(WorkflowState)
    
    # Add nodes to the graph
    workflow.add_node("read_solar_data", 
                     lambda state: read_solar_data(state, adapter))
    
    workflow.add_node("generate_forecast", 
                     lambda state: generate_forecast(state))
    
    workflow.add_node("check_performance", 
                     lambda state: check_performance(state))
    
    workflow.add_node("raise_underperformance_alert", 
                     lambda state: raise_underperformance_alert(state))
    
    workflow.add_node("await_curtailment", 
                     lambda state: await_curtailment(state))
    
    workflow.add_node("apply_curtailment", 
                     lambda state: apply_curtailment(state, adapter))
    
    workflow.add_node("monitor_faults", 
                     lambda state: monitor_faults(state, adapter))
    
    workflow.add_node("raise_fault_alert", 
                     lambda state: raise_fault_alert(state))
    
    workflow.add_node("handle_maintenance_mode", 
                     lambda state: maintenance_mode(state))
    
    # Define the workflow edges
    # Start with reading solar data
    workflow.set_entry_point("read_solar_data")
    
    # From read_solar_data, conditionally go to generate_forecast or monitor_faults
    workflow.add_conditional_edges(
        "read_solar_data",
        should_generate_forecast,
        {
            "generate_forecast": "generate_forecast",
            "monitor_faults": "monitor_faults"
        }
    )
    
    # From generate_forecast, conditionally go to check_performance or monitor_faults  
    workflow.add_conditional_edges(
        "generate_forecast",
        should_check_performance,
        {
            "check_performance": "check_performance",
            "monitor_faults": "monitor_faults"
        }
    )
    
    # From check_performance, conditionally raise alert or continue
    workflow.add_conditional_edges(
        "check_performance", 
        should_raise_performance_alert,
        {
            "raise_underperformance_alert": "raise_underperformance_alert",
            "await_curtailment": "await_curtailment"
        }
    )
    
    # From raise_underperformance_alert, go to await_curtailment
    workflow.add_edge("raise_underperformance_alert", "await_curtailment")
    
    # From await_curtailment, conditionally apply curtailment or monitor faults
    workflow.add_conditional_edges(
        "await_curtailment",
        should_apply_curtailment,
        {
            "apply_curtailment": "apply_curtailment", 
            "monitor_faults": "monitor_faults"
        }
    )
    
    # From apply_curtailment, go to monitor_faults
    workflow.add_edge("apply_curtailment", "monitor_faults")
    
    # From monitor_faults, conditionally raise fault alert or continue
    workflow.add_conditional_edges(
        "monitor_faults",
        should_raise_fault_alert,
        {
            "raise_fault_alert": "raise_fault_alert",
            "handle_maintenance_mode": "handle_maintenance_mode" 
        }
    )
    
    # From raise_fault_alert, go to handle_maintenance_mode
    workflow.add_edge("raise_fault_alert", "handle_maintenance_mode")
    
    # From handle_maintenance_mode, conditionally continue or end
    workflow.add_conditional_edges(
        "handle_maintenance_mode",
        should_continue_or_end,
        {
            "handle_maintenance_mode": "handle_maintenance_mode",
            "read_solar_data": "read_solar_data",
            END: END
        }
    )
    
    # Configure persistence if enabled
    # Persistence is not supported in current LangGraph version. Implement your own if needed.
    # if enable_persistence:
    #     memory = MemorySaver()
    #     workflow.set_memory(memory)
    #     logger.info("Workflow persistence enabled")
    
    # Compile the workflow
    app = workflow.compile()
    
    logger.info("Solar Agent workflow graph created successfully")
    return app


def create_simple_workflow(adapter) -> StateGraph:
    """Create a simplified workflow for testing.
    
    Args:
        adapter: Hardware adapter instance
        
    Returns:
        Simple StateGraph instance
    """
    workflow = StateGraph(WorkflowState)
    
    # Add basic nodes
    workflow.add_node("read_data", 
                     lambda state: read_solar_data(state, adapter))
    workflow.add_node("monitor", 
                     lambda state: monitor_faults(state, adapter))
    
    # Simple linear flow
    workflow.set_entry_point("read_data")
    workflow.add_edge("read_data", "monitor")
    workflow.add_edge("monitor", "read_data")  # Loop back
    
    return workflow.compile()


class WorkflowManager:
    """
    Manager class for Solar Agent workflow execution.
    Handles state persistence, workflow execution, and human-in-the-loop interrupts.
    """
    
    def __init__(
        self, 
        adapter,
        utility_client=None,
        enable_persistence: bool = True
    ):
        """Initialize workflow manager.
        
        Args:
            adapter: Hardware adapter instance
            utility_client: HTTP client for Utility Agent
            enable_persistence: Whether to enable state persistence
        """
        self.adapter = adapter
        self.utility_client = utility_client
        self.workflow = create_solar_agent_graph(
            adapter, 
            utility_client, 
            enable_persistence
        )
        self.is_running = False
        
    async def start_workflow(
        self, 
        agent_id: str,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> str:
        """Start the workflow execution.
        
        Args:
            agent_id: Unique identifier for the agent
            initial_state: Optional initial state dictionary
            
        Returns:
            Thread ID for the workflow execution
        """
        if self.is_running:
            raise RuntimeError("Workflow is already running")
        
        # Create initial state
        if initial_state:
            state = WorkflowState(agent_id=agent_id, **initial_state)
        else:
            state = WorkflowState(agent_id=agent_id)
        
        # Start workflow execution
        config = {"thread_id": agent_id}
        
        try:
            self.is_running = True
            result = await self.workflow.ainvoke(state, config=config)
            logger.info(f"Workflow started for agent {agent_id}")
            return agent_id
        except Exception as e:
            self.is_running = False
            logger.error(f"Failed to start workflow: {e}")
            raise
    
    async def stop_workflow(self) -> None:
        """Stop the workflow execution."""
        self.is_running = False
        logger.info("Workflow stopped")
    
    async def get_state(self, thread_id: str) -> Optional[WorkflowState]:
        """Get current workflow state.
        
        Args:
            thread_id: Thread ID of the workflow
            
        Returns:
            Current workflow state or None
        """
        try:
            config = {"thread_id": thread_id}
            state_snapshot = self.workflow.get_state(config)
            if state_snapshot and state_snapshot.values:
                return state_snapshot.values
            return None
        except Exception as e:
            logger.error(f"Failed to get workflow state: {e}")
            return None
    
    async def update_state(
        self, 
        thread_id: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update workflow state.
        
        Args:
            thread_id: Thread ID of the workflow
            updates: State updates to apply
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            config = {"thread_id": thread_id}
            self.workflow.update_state(config, updates)
            logger.info(f"Workflow state updated for thread {thread_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update workflow state: {e}")
            return False
    
    async def interrupt_workflow(
        self, 
        thread_id: str, 
        interrupt_data: Dict[str, Any]
    ) -> bool:
        """Interrupt workflow for human-in-the-loop.
        
        Args:
            thread_id: Thread ID of the workflow
            interrupt_data: Interrupt context data
            
        Returns:
            True if interrupt successful, False otherwise
        """
        try:
            # Update state with interrupt data
            updates = {
                "pending_approval": True,
                "approval_context": interrupt_data
            }
            return await self.update_state(thread_id, updates)
        except Exception as e:
            logger.error(f"Failed to interrupt workflow: {e}")
            return False 