# src/agents/household/main.py
import httpx
import json
import asyncio
import traceback
import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.encoders import jsonable_encoder

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from shared.models import BecknAck, BecknContext, EnergyOffer, AgentProfile, EnergyContract
from agents.agent_graph import *
from shared.config import settings

# --- Agent Configuration (from environment) ---
AGENT_ID = os.getenv("AGENT_ID", "household-agent-01")
AGENT_OWN_URL = os.getenv("AGENT_OWN_URL", "http://localhost:8001")
INITIAL_SOC_PERCENT = float(os.getenv("INITIAL_SOC", "15")) # Read from env
MAX_CAPACITY_KWH = 15.0

INITIAL_PROFILE = AgentProfile(
    agent_id=AGENT_ID,
    agent_type="household",
    max_capacity_kwh=MAX_CAPACITY_KWH,
    current_energy_storage_kwh=(INITIAL_SOC_PERCENT / 100.0) * MAX_CAPACITY_KWH
)

memory = MemorySaver()
workflow = StateGraph(P2PAgentState)
def entrypoint_node(state: P2PAgentState) -> dict: return {}
workflow.add_node("entrypoint", entrypoint_node)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("initiate_search", initiate_search_node)
workflow.add_node("evaluate_offers", evaluate_offers_node)
workflow.add_node("send_select", send_select_node)
workflow.add_node("send_init", send_init_node)
workflow.add_node("send_confirm", send_confirm_node)
workflow.add_node("process_bap_completion", process_bap_completion_node)
workflow.add_node("formulate_offer", formulate_offer_node)
workflow.add_node("process_selection", process_selection_node)
workflow.add_node("process_init", process_init_node)
workflow.add_node("process_confirmation", process_confirmation_node)
workflow.set_entry_point("entrypoint")
workflow.add_conditional_edges("entrypoint", route_trigger, {
    "supervisor": "supervisor",
    "formulate_offer": "formulate_offer",
    "process_selection": "process_selection",
    "process_init": "process_init",
    "process_confirmation": "process_confirmation",
    "evaluate_offers": "evaluate_offers",
    "send_init": "send_init",
    "send_confirm": "send_confirm",
    "process_bap_completion": "process_bap_completion",
    "initiate_search": "initiate_search",
    "__end__": END
})
workflow.add_conditional_edges("supervisor", route_from_supervisor, {
    "initiate_search": "initiate_search",
    "__end__": END
})
workflow.add_edge("initiate_search", END)
workflow.add_conditional_edges("evaluate_offers", route_after_evaluation, {
    "send_select": "send_select",
    "__end__": END
})
workflow.add_edge("send_select", END)
workflow.add_edge("send_init", END)
workflow.add_edge("send_confirm", END)
workflow.add_edge("process_bap_completion", END)
workflow.add_edge("formulate_offer", END)
workflow.add_edge("process_selection", END)
workflow.add_edge("process_init", END)
workflow.add_edge("process_confirmation", END)
agent_app_graph = workflow.compile(checkpointer=memory)

async def invoke_and_dispatch(input_payload: dict, config: dict):
    async for event in agent_app_graph.astream(input_payload, config): pass
    final_state = agent_app_graph.get_state(config)
    if request_to_send := final_state.values.get("outgoing_request"):
        agent_app_graph.update_state(config, {"outgoing_request": None})
        url, payload = request_to_send["url"], request_to_send["payload"]
        print(f"--- DISPATCHING HTTP POST to {url} ---")
        async with httpx.AsyncClient() as client:
            try:
                await client.post(url, json=jsonable_encoder(payload), timeout=10.0)
            except httpx.RequestError as e:
                print(f"--- DISPATCH FAILED for {url}: {e} ---")
    
    # If this was a transaction thread, merge profile updates back to simulation state
    if config["configurable"]["thread_id"] != f"simulation_thread_{AGENT_ID}":
        sim_config = {"configurable": {"thread_id": f"simulation_thread_{AGENT_ID}"}}
        if final_state and "profile" in final_state.values:
            updated_profile = final_state.values["profile"]
            agent_app_graph.update_state(sim_config, {"profile": updated_profile})
            print(f"--- MERGED profile update to simulation state: {updated_profile.current_energy_storage_kwh:.2f} kWh ---")

async def agent_simulation_loop():
    thread_id = f"simulation_thread_{AGENT_ID}"
    config = {"configurable": {"thread_id": thread_id}}
    
    # Initialize the agent's state from environment variables
    agent_app_graph.update_state(config, {"profile": INITIAL_PROFILE, "agent_url": AGENT_OWN_URL})
    
    print(f"--- {AGENT_ID} (SoC: {INITIAL_SOC_PERCENT}%) Simulation Loop starting in 5 seconds... ---")
    await asyncio.sleep(5)

    is_seller = INITIAL_SOC_PERCENT > 50

    while True:
        try:
            print(f"\n--- Running Cycle for {AGENT_ID} ---")
            
            # 1. Apply the new energy consumption/generation model
            current_state = agent_app_graph.get_state(config)
            if not current_state:
                print(f"--- WARN in {AGENT_ID}: State not found, skipping cycle. ---")
                await asyncio.sleep(20)
                continue
                
            profile = current_state.values['profile']
            
            if is_seller:
                # Sellers generate a small amount of energy
                energy_change = 0.02
            else:
                # Buyers consume a small amount of energy
                energy_change = -0.03
            
            profile.current_energy_storage_kwh = max(0, min(profile.max_capacity_kwh, profile.current_energy_storage_kwh + energy_change))
            agent_app_graph.update_state(config, {"profile": profile})
            
            # 2. Invoke the graph's decision-making cycle with the updated profile
            await invoke_and_dispatch({"trigger": "simulation_cycle"}, config)
            
            await asyncio.sleep(20)
        except Exception as e:
            print(f"--- ERROR in {AGENT_ID} loop: {e} ---"); traceback.print_exc(); await asyncio.sleep(20)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient() as client:
        await client.post(f"{settings.BECKN_GATEWAY_URL}/register", json={"bpp_uri": AGENT_OWN_URL})
    task = asyncio.create_task(agent_simulation_loop())
    yield; task.cancel()
app = FastAPI(title=f"{AGENT_ID}", lifespan=lifespan)

@app.get("/profile")
async def get_profile():
    """Get the current agent profile."""
    thread_id = f"simulation_thread_{AGENT_ID}"
    config = {"configurable": {"thread_id": thread_id}}
    state = agent_app_graph.get_state(config)
    if state:
        return state.values.get("profile")
    return INITIAL_PROFILE

@app.post("/a2a")
async def handle_a2a_task(request: Request, background_tasks: BackgroundTasks):
    """Handle A2A protocol tasks."""
    payload = await request.json()
    task_params = payload.get("params", {}).get("message", {}).get("parts", [{}])[0].get("data")
    skill_id = payload.get("params", {}).get("message", {}).get("skillId")
    print(f"\n--- {AGENT_ID} Received A2A skill call: {skill_id} ---")
    
    sim_thread_id = f"simulation_thread_{AGENT_ID}"
    config = {"configurable": {"thread_id": sim_thread_id}}
    
    if skill_id == "get_soc_data":
        # This is a direct data request, handle it synchronously and return data
        current_state = agent_app_graph.get_state(config)
        profile = current_state.values.get("profile") if current_state else INITIAL_PROFILE
        response_data = {
            "agent_id": profile.agent_id,
            "soc_percent": (profile.current_energy_storage_kwh / profile.max_capacity_kwh) * 100,
            "generation_kw": profile.generation_rate_kw
        }
        return {"jsonrpc": "2.0", "result": response_data, "id": payload.get("id")}

    elif skill_id == "curtail_generation":
        # Curtailment is a command, run it in the background
        input_payload = {"trigger": "incoming_curtailment", "profile": agent_app_graph.get_state(config).values['profile'], "active_transaction_context": {"a2a_params": task_params}}
        background_tasks.add_task(invoke_and_dispatch, input_payload, {"configurable": {"thread_id": f"a2a-task-{time.time()}"}})
        return {"jsonrpc": "2.0", "result": {"status": "received"}, "id": payload.get("id")}
    
    return {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": payload.get("id")}

@app.post("/{action:path}")
async def handle_beckn_request(action: str, request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()
    context = BecknContext.parse_obj(payload.get("context"))
    config = {"configurable": {"thread_id": context.transaction_id}}
    print(f"\n--- {AGENT_ID} Received /{action} for TxID: {context.transaction_id[:8]} ---")
    
    input_payload = {"trigger": f"incoming_{action}"}
    
    if action == "on_search":
        items = payload.get("message", {}).get("catalog", {}).get("items", [])
        input_payload["received_offers"] = [EnergyOffer.parse_obj(item) for item in items]
    elif action == "on_confirm":
        input_payload["final_contract"] = EnergyContract.parse_obj(payload.get("message", {}).get("order", {}))

    # Always get the current profile from simulation state and include it
    sim_config = {"configurable": {"thread_id": f"simulation_thread_{AGENT_ID}"}}
    sim_state = agent_app_graph.get_state(sim_config)
    profile = sim_state.values.get("profile", INITIAL_PROFILE) if sim_state else INITIAL_PROFILE
    
    # Include profile and context for all incoming requests
    input_payload.update({
        "profile": profile, 
        "active_transaction_context": context
    })

    background_tasks.add_task(invoke_and_dispatch, input_payload, config)
    return BecknAck()