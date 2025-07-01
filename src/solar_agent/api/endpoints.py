"""FastAPI endpoints for Solar Agent REST API."""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from solar_agent.core.config import settings
from solar_agent.core.models import (
    AgentMode,
    CurtailmentCommand,
    CurtailmentStatus,
)
from solar_agent.api.models import (
    CurtailmentRequest,
    StatusResponse,
    HealthResponse,
    AlertRequest,
    HumanApprovalRequest,
    SuccessResponse,
    ErrorResponse,
    FaultStatusResponse,
    PerformanceMetrics,
    AdapterInfoResponse,
)


logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix=settings.api_prefix)

# Global state storage (in production, this would be in a database)
_workflow_manager = None
_adapter = None


def get_workflow_manager():
    """Dependency to get workflow manager instance."""
    global _workflow_manager
    if _workflow_manager is None:
        raise HTTPException(
            status_code=503,
            detail="Workflow manager not initialized"
        )
    return _workflow_manager


def get_adapter():
    """Dependency to get hardware adapter instance."""
    global _adapter
    if _adapter is None:
        raise HTTPException(
            status_code=503,
            detail="Hardware adapter not initialized"
        )
    return _adapter


def set_dependencies(workflow_manager, adapter):
    """Set global dependencies for the API."""
    global _workflow_manager, _adapter
    _workflow_manager = workflow_manager
    _adapter = adapter


@router.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.version,
        "status": "running",
        "agent_id": settings.agent_id,
    }


@router.post("/curtailment", response_model=SuccessResponse)
async def receive_curtailment(
    request: CurtailmentRequest,
    background_tasks: BackgroundTasks,
    workflow_manager=Depends(get_workflow_manager)
):
    """Receive curtailment command from Utility Agent.
    
    This endpoint receives curtailment instructions and triggers
    the LangGraph workflow to apply the curtailment.
    """
    logger.info(f"Received curtailment command: {request.target_output_kw}kW")
    
    try:
        # Create curtailment command
        curtailment = CurtailmentCommand(
            target_output_kw=request.target_output_kw,
            duration_minutes=request.duration_minutes,
            start_time=request.start_time,
            end_time=request.end_time,
            priority=request.priority,
            reason=request.reason,
            status=CurtailmentStatus.PENDING,
        )
        
        # Update workflow state with curtailment command
        thread_id = settings.agent_id
        updates = {
            "active_curtailment": curtailment,
        }
        
        success = await workflow_manager.update_state(thread_id, updates)
        
        if success:
            # Optionally trigger workflow interrupt for immediate processing
            if request.priority >= 8:  # High priority curtailment
                interrupt_data = {
                    "type": "high_priority_curtailment",
                    "curtailment_id": curtailment.command_id,
                    "target_output_kw": request.target_output_kw,
                }
                await workflow_manager.interrupt_workflow(thread_id, interrupt_data)
            
            return SuccessResponse(
                message=f"Curtailment command received: {request.target_output_kw}kW",
                data={
                    "curtailment_id": curtailment.command_id,
                    "target_output_kw": request.target_output_kw,
                    "status": curtailment.status.value,
                }
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to update workflow state with curtailment"
            )
            
    except Exception as e:
        logger.error(f"Error processing curtailment command: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process curtailment: {str(e)}"
        )


@router.get("/status", response_model=StatusResponse)
async def get_status(
    workflow_manager=Depends(get_workflow_manager),
    adapter=Depends(get_adapter)
):
    """Get current agent status."""
    logger.info("Status request received")
    
    try:
        # Get current workflow state
        thread_id = settings.agent_id
        state = await workflow_manager.get_state(thread_id)
        
        if not state:
            raise HTTPException(
                status_code=404,
                detail="Workflow state not found"
            )
        
        # Get adapter health
        adapter_health = await adapter.health_check()
        
        # Calculate utilization
        current_output = state.latest_solar_data.current_output_kw if state.latest_solar_data else 0
        utilization_percent = (current_output / settings.capacity_kw) * 100 if settings.capacity_kw > 0 else 0
        
        return StatusResponse(
            agent_id=state.agent_id,
            timestamp=datetime.utcnow(),
            mode=state.current_mode,
            is_online=adapter_health.get("is_online", False),
            current_output_kw=current_output,
            capacity_kw=settings.capacity_kw,
            utilization_percent=utilization_percent,
            uptime_seconds=state.get_uptime_seconds(),
            last_communication=datetime.utcnow(),
            workflow_step=state.workflow_step,
            workflow_iteration=state.workflow_iteration,
            latest_solar_data=state.latest_solar_data,
            active_curtailment=state.active_curtailment.dict() if state.active_curtailment else None,
            active_faults_count=len(state.active_faults),
            critical_faults_count=len([f for f in state.active_faults if f.is_critical]),
            maintenance_mode=state.maintenance_mode,
            pending_approval=state.pending_approval,
            approval_context=state.approval_context,
            error_count=state.error_count,
            communication_failures=getattr(state, 'communication_failures', 0),
        )
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get status: {str(e)}"
        )


@router.get("/heartbeat", response_model=HealthResponse)
async def heartbeat(
    workflow_manager=Depends(get_workflow_manager),
    adapter=Depends(get_adapter)
):
    """Periodic health check endpoint."""
    logger.debug("Heartbeat request received")
    
    try:
        # Check workflow manager health
        thread_id = settings.agent_id
        state = await workflow_manager.get_state(thread_id)
        workflow_status = "healthy" if state else "degraded"
        
        # Check adapter health
        adapter_health = await adapter.health_check()
        adapter_status = adapter_health.get("status", "unknown")
        
        # Determine overall health
        if workflow_status == "healthy" and adapter_status == "healthy":
            overall_status = "healthy"
        elif workflow_status == "degraded" or adapter_status == "degraded":
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        # Get component statuses
        components = {
            "workflow": workflow_status,
            "adapter": adapter_status,
            "api": "healthy",
        }
        
        return HealthResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            agent_id=settings.agent_id,
            version=settings.version,
            uptime_seconds=state.get_uptime_seconds() if state else 0,
            mode=state.current_mode if state else AgentMode.OFFLINE,
            components=components,
            adapter_status=adapter_status,
            workflow_status=workflow_status,
            last_error=state.last_error if state else None,
            error_count=state.error_count if state else 0,
        )
        
    except Exception as e:
        logger.error(f"Error in heartbeat: {e}")
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.utcnow(),
            agent_id=settings.agent_id,
            version=settings.version,
            uptime_seconds=0,
            mode=AgentMode.OFFLINE,
            components={"api": "error"},
            adapter_status="error",
            workflow_status="error",
            last_error=str(e),
            error_count=1,
        )


@router.post("/alerts", response_model=SuccessResponse)
async def send_alert(request: AlertRequest):
    """Send alert to external systems (placeholder for outbound alerts)."""
    logger.info(f"Alert sent: {request.alert_type.value} - {request.title}")
    
    # In a real implementation, this would forward the alert
    # to the Utility Agent or other monitoring systems
    
    return SuccessResponse(
        message=f"Alert sent: {request.title}",
        data={
            "alert_type": request.alert_type.value,
            "severity": request.severity,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


@router.post("/approval", response_model=SuccessResponse)
async def human_approval(
    request: HumanApprovalRequest,
    workflow_manager=Depends(get_workflow_manager)
):
    """Handle human-in-the-loop approval decisions."""
    logger.info(f"Human approval received: {request.decision}")
    
    try:
        # Update workflow state with approval decision
        thread_id = settings.agent_id
        updates = {
            "pending_approval": False,
            "operator_decision": request.decision,
            "approval_context": None,
        }
        
        success = await workflow_manager.update_state(thread_id, updates)
        
        if success:
            return SuccessResponse(
                message=f"Approval decision recorded: {request.decision}",
                data={
                    "decision": request.decision,
                    "comments": request.comments,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to update approval decision"
            )
            
    except Exception as e:
        logger.error(f"Error processing approval: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process approval: {str(e)}"
        )


@router.get("/faults", response_model=FaultStatusResponse)
async def get_faults(
    workflow_manager=Depends(get_workflow_manager),
    adapter=Depends(get_adapter)
):
    """Get current fault status."""
    logger.info("Fault status request received")
    
    try:
        # Get current faults from adapter
        current_faults = await adapter.get_fault_status()
        
        # Get workflow state for additional context
        thread_id = settings.agent_id
        state = await workflow_manager.get_state(thread_id)
        
        critical_faults = len([f for f in current_faults if f.is_critical])
        fault_mode = state.current_mode == AgentMode.FAULT if state else False
        
        return FaultStatusResponse(
            agent_id=settings.agent_id,
            timestamp=datetime.utcnow(),
            total_faults=len(current_faults),
            critical_faults=critical_faults,
            faults=current_faults,
            fault_mode=fault_mode,
        )
        
    except Exception as e:
        logger.error(f"Error getting fault status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get fault status: {str(e)}"
        )


@router.delete("/faults/{fault_id}", response_model=SuccessResponse)
async def clear_fault(
    fault_id: str,
    adapter=Depends(get_adapter)
):
    """Clear a specific fault."""
    logger.info(f"Clearing fault: {fault_id}")
    
    try:
        success = await adapter.clear_fault(fault_id)
        
        if success:
            return SuccessResponse(
                message=f"Fault {fault_id} cleared successfully",
                data={"fault_id": fault_id}
            )
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Fault {fault_id} not found or could not be cleared"
            )
            
    except Exception as e:
        logger.error(f"Error clearing fault: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear fault: {str(e)}"
        )


@router.post("/maintenance", response_model=SuccessResponse)
async def enter_maintenance_mode(
    workflow_manager=Depends(get_workflow_manager)
):
    """Enter maintenance mode."""
    logger.info("Entering maintenance mode")
    
    try:
        thread_id = settings.agent_id
        updates = {
            "maintenance_mode": True,
            "current_mode": AgentMode.MAINTENANCE,
        }
        
        success = await workflow_manager.update_state(thread_id, updates)
        
        if success:
            return SuccessResponse(
                message="Entered maintenance mode",
                data={"mode": AgentMode.MAINTENANCE.value}
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to enter maintenance mode"
            )
            
    except Exception as e:
        logger.error(f"Error entering maintenance mode: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to enter maintenance mode: {str(e)}"
        )


@router.delete("/maintenance", response_model=SuccessResponse)
async def exit_maintenance_mode(
    workflow_manager=Depends(get_workflow_manager)
):
    """Exit maintenance mode."""
    logger.info("Exiting maintenance mode")
    
    try:
        thread_id = settings.agent_id
        updates = {
            "maintenance_mode": False,
            "current_mode": AgentMode.NORMAL,
        }
        
        success = await workflow_manager.update_state(thread_id, updates)
        
        if success:
            return SuccessResponse(
                message="Exited maintenance mode",
                data={"mode": AgentMode.NORMAL.value}
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to exit maintenance mode"
            )
            
    except Exception as e:
        logger.error(f"Error exiting maintenance mode: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to exit maintenance mode: {str(e)}"
        )


@router.get("/adapter", response_model=AdapterInfoResponse)
async def get_adapter_info(adapter=Depends(get_adapter)):
    """Get hardware adapter information."""
    logger.info("Adapter info request received")
    
    try:
        device_info = await adapter.get_device_info()
        capabilities = await adapter.get_capabilities()
        health = await adapter.health_check()
        
        return AdapterInfoResponse(
            adapter_type=adapter.adapter_type,
            is_connected=adapter.is_connected,
            device_info=device_info,
            capabilities=capabilities,
            last_read_timestamp=getattr(adapter, 'last_read_time', None),
            error_count=health.get("error_count", 0),
            last_error=health.get("error", None),
        )
        
    except Exception as e:
        logger.error(f"Error getting adapter info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get adapter info: {str(e)}"
        )


@router.get("/metrics", response_model=PerformanceMetrics)
async def get_metrics(
    workflow_manager=Depends(get_workflow_manager)
):
    """Get performance metrics."""
    logger.info("Metrics request received")
    
    try:
        thread_id = settings.agent_id
        state = await workflow_manager.get_state(thread_id)
        
        if not state:
            raise HTTPException(status_code=404, detail="No metrics available")
        
        # Calculate basic metrics
        uptime_seconds = state.get_uptime_seconds()
        current_output = state.latest_solar_data.current_output_kw if state.latest_solar_data else 0
        
        # Placeholder metrics (in production, these would come from a time-series database)
        return PerformanceMetrics(
            agent_id=state.agent_id,
            timestamp=datetime.utcnow(),
            uptime_seconds=uptime_seconds,
            total_energy_generated_kwh=0.0,  # Would be calculated from historical data
            average_output_kw=current_output,
            peak_output_kw=settings.capacity_kw,
            efficiency_average=state.latest_solar_data.efficiency if state.latest_solar_data else 0.0,
            curtailments_applied=getattr(state, 'curtailments_applied', 0),
            alerts_sent=getattr(state, 'performance_alerts_count', 0) + getattr(state, 'fault_alerts_count', 0),
            faults_detected=len(state.active_faults),
            availability_percent=95.0,  # Placeholder
            communication_uptime_percent=98.0,  # Placeholder
            last_24h_generation_kwh=0.0,  # Placeholder
            last_24h_availability_percent=95.0,  # Placeholder
        )
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get metrics: {str(e)}"
        ) 