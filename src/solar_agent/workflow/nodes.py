"""LangGraph workflow nodes for Solar Agent operations."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from solar_agent.core.models import AgentMode, AlertType
from solar_agent.workflow.state import WorkflowState
from solar_agent.llm.gemini_provider import get_gemini_llm
from solar_agent.core.config import settings
from solar_agent.llm.factory import create_llm_provider
import re


logger = logging.getLogger(__name__)


async def read_solar_data(state: WorkflowState, adapter, **kwargs) -> Dict[str, Any]:
    """Read current solar panel data from hardware adapter."""
    logger.info(f"Reading solar data for agent {state.agent_id}")
    
    try:
        state.set_step("read_solar_data")
        solar_data = await adapter.read_solar_data()
        state.latest_solar_data = solar_data
        
        return {
            "latest_solar_data": solar_data,
            "last_update": datetime.utcnow(),
        }
    except NotImplementedError as nie:
        logger.error(f"NotImplementedError in read_solar_data: {nie}")
        return {"error": f"Not implemented: {nie}"}
    except Exception as e:
        logger.error(f"Error reading solar data: {e}")
        return {"error": str(e)}


async def generate_forecast(state: WorkflowState, **kwargs) -> Dict[str, Any]:
    """
    Generate solar power forecast using Gemini LLM (langchain-google-genai).
    The LLM is prompted with the latest solar data and returns a forecast value.
    """
    logger.info(f"Generating forecast for agent {state.agent_id}")
    
    try:
        state.set_step("generate_forecast")
        llm = get_gemini_llm()
        prompt = (
            f"Given current generation {getattr(state.latest_solar_data, 'generation_kw', 0):.2f} kW, "
            f"irradiance {getattr(state.latest_solar_data, 'irradiance', 0):.2f}, "
            f"temperature {getattr(state.latest_solar_data, 'temperature', 0):.2f}, "
            "predict the next hour's solar output in kW."
        )
        response = await llm.ainvoke(prompt)
        try:
            forecast_val = float(response.content.strip().split()[0])
        except Exception:
            forecast_val = getattr(state.latest_solar_data, 'generation_kw', 0)
        state.current_forecast = forecast_val
        return {
            "forecast_generated": True,
            "forecast_kw": forecast_val,
            "last_update": datetime.utcnow(),
        }
    except Exception as e:
        logger.error(f"Error generating forecast: {e}")
        return {"error": str(e)}


async def check_performance(state: WorkflowState, **kwargs) -> Dict[str, Any]:
    """Check actual performance against forecast."""
    logger.info(f"Checking performance for agent {state.agent_id}")
    
    try:
        state.set_step("check_performance")
        # Placeholder for performance checking logic
        
        return {
            "performance_ok": True,
            "performance_ratio": 0.95,
        }
    except Exception as e:
        logger.error(f"Error checking performance: {e}")
        return {"error": str(e)}


async def raise_underperformance_alert(state: WorkflowState, **kwargs) -> Dict[str, Any]:
    """Raise alert to Utility Agent about underperformance."""
    logger.info(f"Raising underperformance alert for agent {state.agent_id}")
    
    try:
        state.set_step("raise_underperformance_alert")
        # Placeholder for alert sending logic
        
        return {
            "alert_sent": True,
            "alert_type": AlertType.UNDERPERFORMANCE,
        }
    except Exception as e:
        logger.error(f"Error raising alert: {e}")
        return {"error": str(e)}


async def await_curtailment(state: WorkflowState, **kwargs) -> Dict[str, Any]:
    """Wait for curtailment instructions from Utility Agent."""
    logger.info(f"Awaiting curtailment instructions for agent {state.agent_id}")
    
    try:
        state.set_step("await_curtailment")
        await asyncio.sleep(1)  # Placeholder wait
        
        return {
            "curtailment_received": bool(state.active_curtailment),
        }
    except Exception as e:
        logger.error(f"Error waiting for curtailment: {e}")
        return {"error": str(e)}


async def apply_curtailment(state: WorkflowState, adapter, **kwargs) -> Dict[str, Any]:
    """Apply curtailment command to hardware."""
    logger.info(f"Applying curtailment for agent {state.agent_id}")
    
    try:
        state.set_step("apply_curtailment")
        
        if state.active_curtailment:
            success = await adapter.set_output_limit(
                state.active_curtailment.target_output_kw
            )
            if success:
                state.current_mode = AgentMode.CURTAILED
            
            return {
                "curtailment_applied": success,
                "current_mode": state.current_mode,
            }
        
        return {"curtailment_applied": False}
        
    except NotImplementedError as nie:
        logger.error(f"NotImplementedError in apply_curtailment: {nie}")
        return {"error": f"Not implemented: {nie}"}
    except Exception as e:
        logger.error(f"Error applying curtailment: {e}")
        return {"error": str(e)}


async def monitor_faults(state: WorkflowState, adapter, **kwargs) -> Dict[str, Any]:
    """Monitor hardware for faults and issues."""
    logger.info(f"Monitoring faults for agent {state.agent_id}")
    
    try:
        state.set_step("monitor_faults")
        faults = await adapter.get_fault_status()
        
        # Update state with current faults
        state.active_faults = faults
        
        has_critical_faults = any(f.is_critical for f in faults)
        if has_critical_faults:
            state.current_mode = AgentMode.FAULT
        
        return {
            "fault_count": len(faults),
            "has_critical_faults": has_critical_faults,
            "current_mode": state.current_mode,
        }
        
    except NotImplementedError as nie:
        logger.error(f"NotImplementedError in monitor_faults: {nie}")
        return {"error": f"Not implemented: {nie}"}
    except Exception as e:
        logger.error(f"Error monitoring faults: {e}")
        return {"error": str(e)}


async def raise_fault_alert(state: WorkflowState, **kwargs) -> Dict[str, Any]:
    """Raise fault alert to Utility Agent."""
    logger.info(f"Raising fault alert for agent {state.agent_id}")
    
    try:
        state.set_step("raise_fault_alert")
        # Placeholder for fault alert logic
        
        return {
            "alert_sent": True,
            "alert_type": AlertType.FAULT,
        }
    except NotImplementedError as nie:
        logger.error(f"NotImplementedError in raise_fault_alert: {nie}")
        return {"error": f"Not implemented: {nie}"}
    except Exception as e:
        logger.error(f"Error raising fault alert: {e}")
        return {"error": str(e)}


async def maintenance_mode(state: WorkflowState, **kwargs) -> Dict[str, Any]:
    """Handle firmware upgrade maintenance mode."""
    logger.info(f"Entering maintenance mode for agent {state.agent_id}")
    
    try:
        state.set_step("maintenance_mode")
        state.current_mode = AgentMode.MAINTENANCE
        state.maintenance_mode = True
        
        return {
            "maintenance_mode": True,
            "current_mode": state.current_mode,
        }
        
    except NotImplementedError as nie:
        logger.error(f"NotImplementedError in maintenance_mode: {nie}")
        return {"error": f"Not implemented: {nie}"}
    except Exception as e:
        logger.error(f"Error in maintenance mode: {e}")
        return {"error": str(e)}


PROMPT_TEMPLATES = {
    "explain": (
        "You are a solar grid agent explainer. Given the following context:\n"
        "- Agent ID: {agent_id}\n"
        "- Current mode: {mode}\n"
        "- Active faults: {faults}\n"
        "- Last curtailment: {curtailment}\n"
        "- User question: {input_text}\n\n"
        "Respond ONLY with valid JSON, no explanation or commentary. "
        "Do NOT include markdown, code blocks, or any text outside the JSON object.\n"
        "JSON schema:\n"
        "{{\n  \"reason\": <short explanation>,\n  \"confidence\": <0-1>,\n  \"recommended_action\": <if any>\n}}\n"
        "Repeat: Output ONLY valid JSON."
    ),
    "negotiate": (
        "You are a negotiation assistant for a solar agent. Context:\n"
        "- Agent ID: {agent_id}\n"
        "- Current mode: {mode}\n"
        "- Active faults: {faults}\n"
        "- Last curtailment: {curtailment}\n"
        "- Negotiation request: {input_text}\n\n"
        "Respond ONLY with valid JSON, no explanation or commentary. "
        "Do NOT include markdown, code blocks, or any text outside the JSON object.\n"
        "JSON schema:\n"
        "{{\n  \"position\": <agent's negotiation position>,\n  \"rationale\": <reasoning>,\n  \"confidence\": <0-1>\n}}\n"
        "Repeat: Output ONLY valid JSON."
    ),
    "interpret": (
        "You are an instruction interpreter for a solar agent. Context:\n"
        "- Agent ID: {agent_id}\n"
        "- Current mode: {mode}\n"
        "- Active faults: {faults}\n"
        "- Last curtailment: {curtailment}\n"
        "- Instruction: {input_text}\n\n"
        "Respond ONLY with valid JSON, no explanation or commentary. "
        "Do NOT include markdown, code blocks, or any text outside the JSON object.\n"
        "JSON schema:\n"
        "{{\n  \"interpretation\": <interpreted meaning>,\n  \"confidence\": <0-1>\n}}\n"
        "Repeat: Output ONLY valid JSON."
    ),
    "ask": (
        "You are a Q&A assistant for a solar agent. Context:\n"
        "- Agent ID: {agent_id}\n"
        "- Current mode: {mode}\n"
        "- Active faults: {faults}\n"
        "- Last curtailment: {curtailment}\n"
        "- Question: {input_text}\n\n"
        "Respond ONLY with valid JSON, no explanation or commentary. "
        "Do NOT include markdown, code blocks, or any text outside the JSON object.\n"
        "JSON schema:\n"
        "{{\n  \"answer\": <short answer>,\n  \"confidence\": <0-1>\n}}\n"
        "Repeat: Output ONLY valid JSON."
    ),
}

def get_context_from_state(state: Optional[WorkflowState]) -> dict:
    if not state:
        return {}
    return {
        "agent_id": getattr(state, "agent_id", None),
        "mode": getattr(state, "current_mode", None),
        "faults": [f.description for f in getattr(state, "active_faults", [])],
        "curtailment": getattr(state, "active_curtailment", None),
    }

def extract_json_from_text(text: str) -> str:
    # Try to extract the first JSON object from the text
    match = re.search(r'\{.*?\}', text, re.DOTALL)
    return match.group(0) if match else text

async def explain_action(input_text: str, provider: str = None, model: str = None, state: Optional[WorkflowState] = None) -> dict:
    llm_provider = provider or settings.llm_provider
    llm_model = model or settings.llm_model
    llm_api_key = settings.gemini_api_key if llm_provider == "gemini" else settings.llm_api_key
    llm = create_llm_provider(provider=llm_provider, model=llm_model, api_key=llm_api_key)
    context = get_context_from_state(state)
    prompt = PROMPT_TEMPLATES["explain"].format(
        agent_id=context.get("agent_id", "unknown"),
        mode=context.get("mode", "unknown"),
        faults=", ".join(context.get("faults", [])) or "none",
        curtailment=str(context.get("curtailment", "none")),
        input_text=input_text
    )
    schema = {
        "reason": {"type": "string", "description": "Short explanation"},
        "confidence": {"type": "number", "description": "Confidence (0-1)"},
        "recommended_action": {"type": "string", "description": "Recommended action, if any"}
    }
    try:
        response = await llm.generate_structured(prompt=prompt, schema=schema)
        return response
    except Exception as e:
        logger.error(f"LLM explain_action failed: {e}")
        # Fallback: try to extract JSON from the raw LLM response
        try:
            raw_response = await llm.generate(prompt)
            json_str = extract_json_from_text(raw_response.content)
            import json
            return json.loads(json_str)
        except Exception as e2:
            logger.error(f"Fallback JSON extraction failed: {e2}")
            return {"error": f"Invalid JSON response from LLM: {e2}"}

async def negotiate_action(input_text: str, provider: str = None, model: str = None, state: Optional[WorkflowState] = None) -> dict:
    llm_provider = provider or settings.llm_provider
    llm_model = model or settings.llm_model
    llm_api_key = settings.gemini_api_key if llm_provider == "gemini" else settings.llm_api_key
    llm = create_llm_provider(provider=llm_provider, model=llm_model, api_key=llm_api_key)
    context = get_context_from_state(state)
    prompt = PROMPT_TEMPLATES["negotiate"].format(
        agent_id=context.get("agent_id", "unknown"),
        mode=context.get("mode", "unknown"),
        faults=", ".join(context.get("faults", [])) or "none",
        curtailment=str(context.get("curtailment", "none")),
        input_text=input_text
    )
    schema = {
        "position": {"type": "string", "description": "Agent's negotiation position"},
        "rationale": {"type": "string", "description": "Reasoning"},
        "confidence": {"type": "number", "description": "Confidence (0-1)"}
    }
    try:
        response = await llm.generate_structured(prompt=prompt, schema=schema)
        return response
    except Exception as e:
        logger.error(f"LLM negotiate_action failed: {e}")
        try:
            raw_response = await llm.generate(prompt)
            json_str = extract_json_from_text(raw_response.content)
            import json
            return json.loads(json_str)
        except Exception as e2:
            logger.error(f"Fallback JSON extraction failed: {e2}")
            return {"error": f"Invalid JSON response from LLM: {e2}"}

async def interpret_instruction(input_text: str, provider: str = None, model: str = None, state: Optional[WorkflowState] = None) -> dict:
    llm_provider = provider or settings.llm_provider
    llm_model = model or settings.llm_model
    llm_api_key = settings.gemini_api_key if llm_provider == "gemini" else settings.llm_api_key
    llm = create_llm_provider(provider=llm_provider, model=llm_model, api_key=llm_api_key)
    context = get_context_from_state(state)
    prompt = PROMPT_TEMPLATES["interpret"].format(
        agent_id=context.get("agent_id", "unknown"),
        mode=context.get("mode", "unknown"),
        faults=", ".join(context.get("faults", [])) or "none",
        curtailment=str(context.get("curtailment", "none")),
        input_text=input_text
    )
    schema = {
        "interpretation": {"type": "string", "description": "Interpreted meaning"},
        "confidence": {"type": "number", "description": "Confidence (0-1)"}
    }
    try:
        response = await llm.generate_structured(prompt=prompt, schema=schema)
        return response
    except Exception as e:
        logger.error(f"LLM interpret_instruction failed: {e}")
        try:
            raw_response = await llm.generate(prompt)
            json_str = extract_json_from_text(raw_response.content)
            import json
            return json.loads(json_str)
        except Exception as e2:
            logger.error(f"Fallback JSON extraction failed: {e2}")
            return {"error": f"Invalid JSON response from LLM: {e2}"}

async def answer_question(input_text: str, provider: str = None, model: str = None, state: Optional[WorkflowState] = None) -> dict:
    llm_provider = provider or settings.llm_provider
    llm_model = model or settings.llm_model
    llm_api_key = settings.gemini_api_key if llm_provider == "gemini" else settings.llm_api_key
    llm = create_llm_provider(provider=llm_provider, model=llm_model, api_key=llm_api_key)
    context = get_context_from_state(state)
    prompt = PROMPT_TEMPLATES["ask"].format(
        agent_id=context.get("agent_id", "unknown"),
        mode=context.get("mode", "unknown"),
        faults=", ".join(context.get("faults", [])) or "none",
        curtailment=str(context.get("curtailment", "none")),
        input_text=input_text
    )
    schema = {
        "answer": {"type": "string", "description": "Short answer"},
        "confidence": {"type": "number", "description": "Confidence (0-1)"}
    }
    try:
        response = await llm.generate_structured(prompt=prompt, schema=schema)
        return response
    except Exception as e:
        logger.error(f"LLM answer_question failed: {e}")
        try:
            raw_response = await llm.generate(prompt)
            json_str = extract_json_from_text(raw_response.content)
            import json
            return json.loads(json_str)
        except Exception as e2:
            logger.error(f"Fallback JSON extraction failed: {e2}")
            return {"error": f"Invalid JSON response from LLM: {e2}"} 