# src/agents/utility/main.py
import httpx
import json
import asyncio
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from shared.models import BecknAck, BecknContext, AgentProfile
from agents.agent_graph import *
from shared.config import settings

AGENT_ID = "utility-agent-01"
AGENT_BASE_URL = "http://utility_agent:8002"
INITIAL_PROFILE = AgentProfile(agent_id=AGENT_ID, agent_type="utility", max_capacity_kwh=999999, current_energy_storage_kwh=999999)

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
    """Invokes the graph and dispatches any outgoing requests."""
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
    if config["configurable"]["thread_id"] != "simulation_thread_utility":
        sim_config = {"configurable": {"thread_id": "simulation_thread_utility"}}
        if final_state and "profile" in final_state.values:
            updated_profile = final_state.values["profile"]
            agent_app_graph.update_state(sim_config, {"profile": updated_profile})
            print(f"--- MERGED profile update to simulation state: {updated_profile.current_energy_storage_kwh:.2f} kWh ---")

async def agent_simulation_loop():
    thread_id = "simulation_thread_utility"
    config = {"configurable": {"thread_id": thread_id}}
    agent_app_graph.update_state(config, {"profile": INITIAL_PROFILE})
    print("--- Utility Agent Initialized ---")
    
    data_collection_counter = 0
    while True:
        data_collection_counter += 1
        
        # Every 5 cycles (5 minutes), trigger data collection
        if data_collection_counter % 5 == 0:
            print("--- UTILITY: Waking up to collect data from all households ---")
            try:
                await trigger_data_request(BackgroundTasks())
                print("--- UTILITY: Data collection completed ---")
            except Exception as e:
                print(f"--- UTILITY: Data collection failed: {e} ---")
        
        await asyncio.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient() as client:
        await client.post(f"{settings.BECKN_GATEWAY_URL}/register", json={"bpp_uri": "http://utility_agent:8002"})
    task = asyncio.create_task(agent_simulation_loop())
    yield; task.cancel()
app = FastAPI(title="Utility Agent", lifespan=lifespan)

@app.get("/profile")
async def get_profile():
    """Get the current agent profile."""
    thread_id = "simulation_thread_utility"
    config = {"configurable": {"thread_id": thread_id}}
    state = agent_app_graph.get_state(config)
    if state:
        return state.values.get("profile")
    return INITIAL_PROFILE

collected_data = []

@app.post("/admin/request-data")
async def trigger_data_request(background_tasks: BackgroundTasks):
    """Admin endpoint to trigger a data request to all known household agents."""
    print("\n--- ADMIN: Triggering A2A data request to all households ---")

    async def discover_and_request_data():
        print("Starting discover_and_request_data function")
        try:
            # 1. Discover agents from the gateway
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{settings.BECKN_GATEWAY_URL}/registry")
                response.raise_for_status()
                registered_agents = response.json().get("agents", [])
                print(f"Discovered agents: {registered_agents}")
                
                # Use container names directly since we're inside Docker network
                household_urls = [url for url in registered_agents if "household" in url]
                print(f"Household URLs (container): {household_urls}")
            
            # 2. Formulate A2A task
            a2a_payload = {"jsonrpc": "2.0", "method": "createTask", "id": int(time.time()), "params": {"message": {"skillId": "get_soc_data"}}}
            
            # 3. Send task to all discovered household agents
            async with httpx.AsyncClient() as client:
                tasks = [client.post(f"{url}/a2a", json=a2a_payload) for url in household_urls]
                responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 4. Store collected data
            global collected_data
            timestamp = datetime.now().isoformat()
            data_entry = {
                "timestamp": timestamp,
                "collected_data": []
            }
            
            print("--- A2A DATA COLLECTION COMPLETE ---")
            for i, res in enumerate(responses):
                if isinstance(res, httpx.Response):
                    response_data = res.json()
                    print(f"Response from {household_urls[i]}: {response_data}")
                    if "result" in response_data:
                        data_entry["collected_data"].append({
                            "agent_url": household_urls[i],
                            "data": response_data["result"]
                        })
                else:
                    print(f"Error from {household_urls[i]}: {res}")
            
            # Store the collected data
            collected_data.append(data_entry)
            print(f"--- STORED data collection: {len(data_entry['collected_data'])} agents ---")

        except httpx.RequestError as e:
            print(f"Failed to discover or request data: {e}")

    try:
        # Run the function directly instead of as background task
        await discover_and_request_data()
        print("Data request completed successfully")
        return {"status": "Data request completed."}
    except Exception as e:
        print(f"Error in data request: {e}")
        return {"error": str(e)}

@app.get("/admin/collected-data")
async def get_collected_data():
    """Get all collected A2A data."""
    return {"collected_data": collected_data}

@app.post("/{action:path}")
async def handle_beckn_request(action: str, request: Request, background_tasks: BackgroundTasks):
    try:
        payload = await request.json()
        context = BecknContext.parse_obj(payload.get("context"))
        config = {"configurable": {"thread_id": context.transaction_id}}
        print(f"\n--- UTILITY AGENT Received /{action} for TxID: {context.transaction_id[:8]} ---")
        
        # Always get the current profile from simulation state
        sim_config = {"configurable": {"thread_id": "simulation_thread_utility"}}
        sim_state = agent_app_graph.get_state(sim_config)
        profile = sim_state.values.get("profile", INITIAL_PROFILE) if sim_state else INITIAL_PROFILE
        
        input_payload = {"trigger": f"incoming_{action}", "profile": profile, "active_transaction_context": context}
        
        # Handle specific actions
        if action == "on_search":
            items = payload.get("message", {}).get("catalog", {}).get("items", [])
            input_payload["received_offers"] = [EnergyOffer.parse_obj(item) for item in items]
        elif action == "on_confirm":
            input_payload["final_contract"] = EnergyContract.parse_obj(payload.get("message", {}).get("order", {}))
        
        background_tasks.add_task(invoke_and_dispatch, input_payload, config)
        return BecknAck()
    except Exception as e:
        print(f"Error processing request: {e}")
        return {"error": str(e)}



# # src/agents/utility/main.py
# import httpx
# import json
# import asyncio
# from contextlib import asynccontextmanager
# from fastapi import FastAPI, Request, BackgroundTasks
# from fastapi.staticfiles import StaticFiles

# from langgraph.graph import StateGraph, END
# from langgraph.checkpoint.sqlite import SqliteSaver

# # Import the same graph logic and models
# from shared.models import BecknAck, BecknContext, EnergyOffer, AgentProfile
# from agents.agent_graph import P2PAgentState, supervisor_node, initiate_search_node, evaluate_offers_node, formulate_offer_node, route_from_supervisor
# from shared.config import settings

# # --- Agent Configuration & State ---
# AGENT_ID = "utility-agent-01"
# AGENT_BASE_URL = settings.UTILITY_AGENT_BASE_URL
# # The Utility Agent has a very large capacity, representing the grid
# INITIAL_PROFILE = AgentProfile(
#     agent_id=AGENT_ID, agent_type="utility", max_capacity_kwh=999999, current_energy_storage_kwh=999999
# )
# graph_app_holder = {}

# # --- LangGraph Setup (Identical to Solar Agent) ---
# memory = SqliteSaver.from_conn_string(":memory:")
# workflow = StateGraph(P2PAgentState)

# workflow.add_node("supervisor", supervisor_node)
# workflow.add_node("initiate_search", initiate_search_node)
# workflow.add_node("evaluate_offers", evaluate_offers_node)
# workflow.add_node("formulate_offer", formulate_offer_node)

# workflow.set_entry_point("supervisor")
# workflow.add_conditional_edges("supervisor", route_from_supervisor, {"initiate_search": "initiate_search", "__end__": END})
# workflow.add_edge("initiate_search", END)
# workflow.add_edge("evaluate_offers", END)
# workflow.add_edge("formulate_offer", END)

# agent_app_graph = workflow.compile(checkpointer=memory)
# graph_app_holder['app'] = agent_app_graph

# # --- Agent Simulation Loop (Utility's logic is simpler) ---
# async def agent_simulation_loop():
#     """Utility agent is mostly reactive, so its loop is minimal."""
#     thread_id = "simulation_thread"
#     config = {"configurable": {"thread_id": thread_id}}
#     await agent_app_graph.update_state(config, {"profile": INITIAL_PROFILE, "conversation_history": []})
    
#     while True:
#         # The utility agent doesn't proactively buy/sell based on its own state
#         # It primarily reacts to requests from other agents.
#         # We could add logic here to simulate grid strain events later.
#         await asyncio.sleep(60)
#         print("\n--- Utility Agent: Monitoring... ---")

# # --- FastAPI Application ---
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Register with Gateway on startup
#     async with httpx.AsyncClient() as client:
#         try:
#             print(f"Registering Utility Agent with Gateway at {settings.BECKN_GATEWAY_URL}")
#             await client.post(f"{settings.BECKN_GATEWAY_URL}/register", json={"bpp_uri": AGENT_BASE_URL})
#         except httpx.RequestError as e:
#             print(f"Could not register with gateway: {e}")
#     task = asyncio.create_task(agent_simulation_loop())
#     yield
#     task.cancel()

# app = FastAPI(title="Utility Agent", lifespan=lifespan)
# app.mount("/static", StaticFiles(directory="static"), name="static")

# # --- Protocol Endpoints (Identical structure to Solar Agent) ---
# @app.get("/.well-known/agent.json")
# async def get_agent_card():
#     with open("static/utility/agent.json", "r") as f:
#         return json.load(f)

# @app.post("/search")
# async def on_search(request: Request, background_tasks: BackgroundTasks):
#     payload = await request.json()
#     context = BecknContext.parse_obj(payload.get("context"))
#     print(f"\n---UTILITY-BPP: Received search request (TxID: {context.transaction_id[:8]})---")
#     config = {"configurable": {"thread_id": context.transaction_id}}
    
#     sim_state = agent_app_graph.get_state({"configurable": {"thread_id": "simulation_thread"}})
#     current_profile = sim_state.values.get("profile", INITIAL_PROFILE)
#     await agent_app_graph.update_state(config, {"profile": current_profile, "active_transaction_context": context})
    
#     background_tasks.add_task(agent_app_graph.ainvoke, {"supervisor_decision": "act_as_bpp"}, config, entry_point="formulate_offer")
#     return BecknAck()

# @app.post("/on_search")
# async def on_search_callback(request: Request, background_tasks: BackgroundTasks):
#     payload = await request.json()
#     context = BecknContext.parse_obj(payload.get("context"))
#     print(f"\n---UTILITY-BAP: Received on_search callback (TxID: {context.transaction_id[:8]})---")
#     # Logic to handle offers when Utility acts as a BAP
#     return BecknAck()

# @app.get("/health")
# def health_check():
#     return {"status": "ok", "agent_id": AGENT_ID}