# src/agents/solar/main.py
import httpx
import json
import asyncio
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.encoders import jsonable_encoder

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from shared.models import BecknAck, BecknContext, EnergyOffer, AgentProfile, EnergyContract
from agents.agent_graph import *
from shared.config import settings

AGENT_ID = "solar-agent-01"
AGENT_BASE_URL = settings.SOLAR_AGENT_BASE_URL
INITIAL_PROFILE = AgentProfile(agent_id=AGENT_ID, agent_type="solar", max_capacity_kwh=15.0, current_energy_storage_kwh=2.0)

memory = MemorySaver()
workflow = StateGraph(P2PAgentState)
def entrypoint_node(state: P2PAgentState) -> dict: return {}
workflow.add_node("entrypoint", entrypoint_node)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("initiate_search", initiate_search_node)
workflow.add_node("evaluate_offers", evaluate_offers_node)
workflow.add_node("send_select", send_select_node)
workflow.add_node("send_confirm", send_confirm_node)
workflow.add_node("process_bap_completion", process_bap_completion_node)
workflow.add_node("formulate_offer", formulate_offer_node)
workflow.add_node("process_selection", process_selection_node)
workflow.add_node("process_confirmation", process_confirmation_node)
workflow.set_entry_point("entrypoint")
workflow.add_conditional_edges("entrypoint", route_trigger)
workflow.add_conditional_edges("supervisor", route_from_supervisor)
workflow.add_edge("initiate_search", END)
workflow.add_conditional_edges("evaluate_offers", route_after_evaluation)
workflow.add_edge("send_select", END)
workflow.add_edge("send_confirm", END)
workflow.add_edge("process_bap_completion", END)
workflow.add_edge("formulate_offer", END)
workflow.add_edge("process_selection", END)
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

async def agent_simulation_loop():
    thread_id = "simulation_thread_solar"
    config = {"configurable": {"thread_id": thread_id}}
    agent_app_graph.update_state(config, {"profile": INITIAL_PROFILE})
    
    # DEFINITIVE FIX: Add a startup delay to prevent race condition
    print("--- Solar Agent Simulation Loop starting in 5 seconds... ---")
    await asyncio.sleep(5)

    while True:
        try:
            print(f"\n--- Running Solar Agent Cycle (Next cycle in 20s) ---")
            await invoke_and_dispatch({"trigger": "simulation_cycle"}, config)
            current_state = agent_app_graph.get_state(config)
            if current_state:
                profile = current_state.values['profile']
                profile.current_energy_storage_kwh = min(profile.max_capacity_kwh, profile.current_energy_storage_kwh + 0.5)
                agent_app_graph.update_state(config, {"profile": profile})
            await asyncio.sleep(20)
        except Exception as e:
            print(f"--- ERROR in solar simulation loop: {e} ---"); traceback.print_exc(); await asyncio.sleep(20)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient() as client:
        await client.post(f"{settings.BECKN_GATEWAY_URL}/register", json={"bpp_uri": AGENT_BASE_URL})
    task = asyncio.create_task(agent_simulation_loop())
    yield; task.cancel()
app = FastAPI(title="Solar Agent", lifespan=lifespan)

@app.post("/{action:path}")
async def handle_beckn_request(action: str, request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()
    context = BecknContext.parse_obj(payload.get("context"))
    config = {"configurable": {"thread_id": context.transaction_id}}
    print(f"\n--- SOLAR AGENT Received /{action} for TxID: {context.transaction_id[:8]} ---")
    
    input_payload = {"trigger": f"incoming_{action}"}
    
    if action == "on_search":
        items = payload.get("message", {}).get("catalog", {}).get("items", [])
        input_payload["received_offers"] = [EnergyOffer.parse_obj(item) for item in items]
    elif action == "on_confirm":
        input_payload["final_contract"] = EnergyContract.parse_obj(payload.get("message", {}).get("order", {}))

    if action in ["search", "select", "confirm"]:
        sim_state = agent_app_graph.get_state({"configurable": {"thread_id": "simulation_thread_solar"}})
        profile = sim_state.values.get("profile", INITIAL_PROFILE)
        input_payload.update({"profile": profile, "active_transaction_context": context})

    background_tasks.add_task(invoke_and_dispatch, input_payload, config)
    return BecknAck()



# # src/agents/solar/main.py
# import httpx
# import json
# import asyncio
# from contextlib import asynccontextmanager
# from fastapi import FastAPI, Request, BackgroundTasks
# from fastapi.staticfiles import StaticFiles

# from langgraph.graph import StateGraph, END
# from langgraph.checkpoint.sqlite import SqliteSaver

# from shared.models import BecknAck, BecknContext, EnergyOffer, AgentProfile
# from agents.agent_graph import (
#     P2PAgentState,
#     supervisor_node,
#     initiate_search_node,
#     evaluate_offers_node,
#     formulate_offer_node,
#     route_from_supervisor,
# )
# from shared.config import settings

# # --- Agent Configuration & State ---
# AGENT_ID = "solar-agent-01"
# AGENT_BASE_URL = settings.SOLAR_AGENT_BASE_URL
# INITIAL_PROFILE = AgentProfile(
#     agent_id=AGENT_ID, agent_type="solar", max_capacity_kwh=15.0, current_energy_storage_kwh=2.0
# )
# graph_app_holder = {}

# # --- LangGraph Setup ---
# memory = SqliteSaver.from_conn_string(":memory:")
# workflow = StateGraph(P2PAgentState)

# workflow.add_node("supervisor", supervisor_node)
# workflow.add_node("initiate_search", initiate_search_node)
# workflow.add_node("evaluate_offers", evaluate_offers_node)
# workflow.add_node("formulate_offer", formulate_offer_node)

# workflow.set_entry_point("supervisor")
# workflow.add_conditional_edges("supervisor", route_from_supervisor, {
#     "initiate_search": "initiate_search", "__end__": END
# })
# workflow.add_edge("initiate_search", END)
# workflow.add_edge("evaluate_offers", END)
# workflow.add_edge("formulate_offer", END)

# agent_app_graph = workflow.compile(checkpointer=memory)
# graph_app_holder['app'] = agent_app_graph

# # --- Agent Simulation Loop ---
# async def agent_simulation_loop():
#     """Runs the agent's decision cycle periodically."""
#     thread_id = "simulation_thread"
#     config = {"configurable": {"thread_id": thread_id}}
    
#     # Check if state exists, if not, initialize it
#     current_state = agent_app_graph.get_state(config)
#     if not current_state:
#         print("Initializing new simulation state.")
#         await agent_app_graph.update_state(config, {"profile": INITIAL_PROFILE, "conversation_history": []})
#     else:
#         print("Resuming from existing simulation state.")

#     while True:
#         await asyncio.sleep(20)
#         print("\n\n--- Running Agent Simulation Cycle ---")
#         await agent_app_graph.ainvoke(None, config)
        
#         current_state = agent_app_graph.get_state(config)
#         profile = current_state.values['profile']
#         profile.current_energy_storage_kwh = min(profile.max_capacity_kwh, profile.current_energy_storage_kwh + 0.5)
#         await agent_app_graph.update_state(config, {"profile": profile})

# # --- FastAPI Application ---
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     async with httpx.AsyncClient() as client:
#         try:
#             print(f"Registering Solar Agent with Gateway at {settings.BECKN_GATEWAY_URL}")
#             await client.post(f"{settings.BECKN_GATEWAY_URL}/register", json={"bpp_uri": AGENT_BASE_URL})
#         except httpx.RequestError as e:
#             print(f"Could not register with gateway: {e}")
#     task = asyncio.create_task(agent_simulation_loop())
#     yield
#     task.cancel()

# app = FastAPI(title="Solar Agent", lifespan=lifespan)
# app.mount("/static", StaticFiles(directory="static"), name="static")

# # --- Protocol Endpoints ---
# @app.get("/.well-known/agent.json")
# async def get_agent_card():
#     with open("static/solar/agent.json", "r") as f:
#         return json.load(f)

# @app.post("/search")
# async def on_search(request: Request, background_tasks: BackgroundTasks):
#     payload = await request.json()
#     context = BecknContext.parse_obj(payload.get("context"))
#     print(f"\n---BPP: Received search request (TxID: {context.transaction_id[:8]})---")
#     config = {"configurable": {"thread_id": context.transaction_id}}
    
#     # Initialize this transaction thread with the agent's current profile and the incoming context
#     sim_state = agent_app_graph.get_state({"configurable": {"thread_id": "simulation_thread"}})
#     current_profile = sim_state.values.get("profile", INITIAL_PROFILE)
#     await agent_app_graph.update_state(config, {"profile": current_profile, "active_transaction_context": context})
    
#     # Trigger the 'formulate_offer' node specifically for this transaction thread
#     background_tasks.add_task(agent_app_graph.ainvoke, {"supervisor_decision": "act_as_bpp"}, config, entry_point="formulate_offer")
#     return BecknAck()

# @app.post("/on_search")
# async def on_search_callback(request: Request, background_tasks: BackgroundTasks):
#     payload = await request.json()
#     context = BecknContext.parse_obj(payload.get("context"))
#     print(f"\n---BAP: Received on_search callback (TxID: {context.transaction_id[:8]})---")
#     config = {"configurable": {"thread_id": context.transaction_id}}
    
#     items = payload.get("message", {}).get("catalog", {}).get("items", [])
#     offers = [EnergyOffer.parse_obj(item) for item in items]
    
#     await agent_app_graph.update_state(config, {"received_offers": offers})
    
#     # Trigger the 'evaluate_offers' node for this transaction thread
#     background_tasks.add_task(agent_app_graph.ainvoke, None, config, entry_point="evaluate_offers")
#     return BecknAck()

# @app.get("/health")
# def health_check():
#     return {"status": "ok", "agent_id": AGENT_ID}