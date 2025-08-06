# src/agents/agent_graph.py
import httpx
import random
from typing import List, Optional, Literal, Annotated
from typing_extensions import TypedDict
import operator
from datetime import datetime, timezone, timedelta

from fastapi.encoders import jsonable_encoder

from shared.models import EnergyOffer, AgentProfile, BecknContext, BecknOrder, BecknItem, EnergyContract
from shared.config import settings

class P2PAgentState(TypedDict):
    trigger: Optional[str]
    profile: AgentProfile
    active_transaction_id: Optional[str]
    active_transaction_context: Optional[BecknContext]
    received_offers: Annotated[list, operator.add]
    selected_offer: Optional[EnergyOffer]
    final_contract: Optional[EnergyContract]
    outgoing_request: Optional[dict]

# --- Graph Structure ---
def route_trigger(state: P2PAgentState) -> str:
    trigger = state.get("trigger")
    print(f"--- ROUTING from trigger: {trigger} ---")
    if trigger == "simulation_cycle": return "supervisor"
    if trigger == "incoming_search": return "formulate_offer"
    if trigger == "incoming_select": return "process_selection"
    if trigger == "incoming_init": return "process_init"
    if trigger == "incoming_confirm": return "process_confirmation"
    if trigger == "incoming_on_search": return "evaluate_offers"
    if trigger == "incoming_on_select": return "send_init"
    if trigger == "incoming_on_init": return "send_confirm"
    if trigger == "incoming_on_confirm": return "process_bap_completion"
    return "__end__"

def route_from_supervisor(state: P2PAgentState) -> str:
    if state.get("trigger") == "start_bap_flow":
        print("--- SUPERVISOR DECISION: Route to INITIATE SEARCH ---")
        return "initiate_search"
    print("--- SUPERVISOR DECISION: Route to END (Idle) ---")
    return "__end__"

def route_after_evaluation(state: P2PAgentState) -> str:
    if state.get("trigger") == "selection_made":
        print("--- EVALUATION DECISION: Route to SEND SELECT ---")
        return "send_select"
    print("--- EVALUATION DECISION: Route to END (No offers) ---")
    return "__end__"


# --- Graph Nodes (No more httpx!) ---
async def supervisor_node(state: P2PAgentState) -> dict:
    profile = state['profile']
    print(f"--- SUPERVISOR ({profile.agent_id}) | Energy: {profile.current_energy_storage_kwh:.2f} kWh ---")
    
    # Clear stuck transactions after a reasonable time (simplified logic)
    if state.get("active_transaction_id") and state.get("trigger") == "simulation_cycle":
        print(f"--- SUPERVISOR: Clearing stuck transaction ---")
        return {
            "active_transaction_id": None, 
            "active_transaction_context": None, 
            "selected_offer": None,
            "final_contract": None,
            "received_offers": [],
            "trigger": "idle"
        }
    
    # For household agents, trigger buying when energy is low
    if profile.agent_type == 'household' and profile.current_energy_storage_kwh < 0.3 * profile.max_capacity_kwh:
        if state.get("active_transaction_id"): 
            print(f"--- SUPERVISOR: Already in transaction, staying idle ---")
            return {"trigger": "idle"}
        print(f"--- SUPERVISOR: Energy low ({profile.current_energy_storage_kwh:.2f} kWh), starting BAP flow ---")
        return {"trigger": "start_bap_flow"}
    
    # For household agents with high energy, they can act as sellers
    elif profile.agent_type == 'household' and profile.current_energy_storage_kwh > 0.7 * profile.max_capacity_kwh:
        print(f"--- SUPERVISOR: Energy high ({profile.current_energy_storage_kwh:.2f} kWh), ready to sell ---")
        return {"trigger": "idle"}  # Will respond to search requests
    
    return {"trigger": "idle"}

async def initiate_search_node(state: P2PAgentState) -> dict:
    print(f"--- BAP ({state['profile'].agent_id}): INITIATE SEARCH ---")
    profile = state["profile"]
    # Use the agent's own URL instead of hardcoded settings
    # Map agent ID to container name and port
    agent_num = profile.agent_id.split('-')[-1]
    port = 8001 + (int(agent_num) - 1) * 2
    agent_url = f"http://household_agent_{int(agent_num)}:{port}"
    context = BecknContext(action="search", bap_id=profile.agent_id, bap_uri=agent_url)
    search_payload = {"context": context, "message": {"intent": {}}}
    return {
        "active_transaction_id": context.transaction_id,
        "active_transaction_context": context,
        "outgoing_request": {"url": f"{settings.BECKN_GATEWAY_URL}/search", "payload": search_payload}
    }

async def evaluate_offers_node(state: P2PAgentState) -> dict:
    # Ensure profile is available - if not, get it from simulation state
    if 'profile' not in state:
        print(f"--- WARNING: Profile not found in state, skipping evaluation ---")
        return {"trigger": "search_failed"}
    
    print(f"--- BAP ({state['profile'].agent_id}): EVALUATE OFFERS ---")
    offers = state.get("received_offers", [])
    if not offers: return {"trigger": "search_failed"}
    best_offer = min(offers, key=lambda o: o.price_per_kwh)
    print(f"Best offer selected: ${best_offer.price_per_kwh}/kWh from {best_offer.provider_id}")
    
    # Use container URLs consistently
    if best_offer.provider_id.startswith('utility'):
        bpp_uri = "http://utility_agent:8002"
    else:
        # Extract agent number and construct container URL
        agent_num = best_offer.provider_id.split('-')[-1]
        port = 8001 + (int(agent_num) - 1) * 2
        bpp_uri = f"http://household_agent_{int(agent_num)}:{port}"
    
    context = state["active_transaction_context"].copy(update={"action": "select", "bpp_id": best_offer.provider_id, "bpp_uri": bpp_uri})
    return {"selected_offer": best_offer, "active_transaction_context": context, "trigger": "selection_made"}

async def send_select_node(state: P2PAgentState) -> dict:
    print(f"--- BAP ({state['profile'].agent_id}): SENDING SELECT ---")
    context, offer = state["active_transaction_context"], state["selected_offer"]
    select_payload = {"context": context, "message": {"order": {"provider": {"id": offer.provider_id}, "items": [{"id": offer.offer_id}]}}}
    return {"outgoing_request": {"url": f"{context.bpp_uri}/select", "payload": select_payload}}

async def send_confirm_node(state: P2PAgentState) -> dict:
    print(f"--- BAP ({state['profile'].agent_id}): SENDING CONFIRM ---")
    context, offer = state["active_transaction_context"], state.get("selected_offer")
    
    # Check if offer exists
    if not offer:
        print(f"--- WARNING: No selected offer found, skipping confirm ---")
        return {"trigger": "transaction_failed"}
    
    confirm_payload = {"context": context.copy(update={"action": "confirm"}), "message": {"order": BecknOrder(provider={"id": offer.provider_id}, items=[BecknItem(id=offer.offer_id)])}}
    return {"outgoing_request": {"url": f"{context.bpp_uri}/confirm", "payload": confirm_payload}}

async def process_bap_completion_node(state: P2PAgentState) -> dict:
    print(f"--- BAP ({state['profile'].agent_id}): COMPLETING TRANSACTION ---")
    contract, profile = state["final_contract"], state["profile"]
    profile.current_energy_storage_kwh += contract.agreed_quantity_kwh
    print(f"✅ Contract confirmed! Energy purchased. New battery level: {profile.current_energy_storage_kwh:.2f} kWh")
    # Clear transaction state completely
    return {
        "profile": profile, 
        "active_transaction_id": None, 
        "active_transaction_context": None,
        "selected_offer": None,
        "final_contract": None,
        "received_offers": []
    }

async def send_init_node(state: P2PAgentState) -> dict:
    print(f"--- BAP ({state['profile'].agent_id}): SENDING INIT ---")
    context, offer = state["active_transaction_context"], state.get("selected_offer")
    
    # Check if offer exists
    if not offer:
        print(f"--- WARNING: No selected offer found, skipping init ---")
        return {"trigger": "transaction_failed"}
    
    init_payload = {"context": context.copy(update={"action": "init"}).dict(), "message": {"order": {"provider": {"id": offer.provider_id}, "items": [{"id": offer.offer_id}]}}}
    return {"outgoing_request": {"url": f"{context.bpp_uri}/init", "payload": init_payload}}

async def process_init_node(state: P2PAgentState) -> dict:
    print(f"--- BPP ({state['profile'].agent_id}): PROCESSING INIT ---")
    context = state["active_transaction_context"].copy(update={"action": "on_init"})
    # BPP returns the final quote in the on_init response
    payload = {"context": context.dict(), "message": {"order": {"quote": {"price": {"currency": "USD", "value": "2.50"}}}}}
    return {"outgoing_request": {"url": f"{context.bap_uri}/on_init", "payload": payload}}

async def formulate_offer_node(state: P2PAgentState) -> dict:
    print(f"--- BPP ({state['profile'].agent_id}): FORMULATE OFFER ---")

    # Simulate random availability
    if random.random() < 0.3: # 30% chance the agent is "offline" or busy
        print(f"Agent {state['profile'].agent_id} is unavailable to make an offer this time.")
        return {}

    profile, in_context = state["profile"], state["active_transaction_context"]
    if profile.agent_type == 'household' and profile.current_energy_storage_kwh < 0.6 * profile.max_capacity_kwh: 
        print(f"Household Agent {profile.agent_id} has insufficient surplus energy ({profile.current_energy_storage_kwh:.2f} kWh). Not making an offer.")
        return {}
    
    qty, price = (10.0, 0.15) if profile.agent_type == 'household' else (500.0, 0.25)
    
    # Use container URLs consistently
    if profile.agent_type == 'household':
        agent_num = profile.agent_id.split('-')[-1]
        port = 8001 + (int(agent_num) - 1) * 2
        bpp_uri = f"http://household_agent_{int(agent_num)}:{port}"
    else:
        bpp_uri = "http://utility_agent:8002"
    
    offer = EnergyOffer(provider_id=profile.agent_id, quantity_kwh=qty, price_per_kwh=price, valid_until=datetime.now(timezone.utc) + timedelta(seconds=60))
    context = in_context.copy(update={"action": "on_search", "bpp_id": profile.agent_id, "bpp_uri": bpp_uri})
    payload = {"context": context, "message": {"catalog": {"items": [offer]}}}
    return {"outgoing_request": {"url": f"{in_context.bap_uri}/on_search", "payload": payload}}

async def process_selection_node(state: P2PAgentState) -> dict:
    print(f"--- BPP ({state['profile'].agent_id}): PROCESSING SELECTION ---")
    context = state["active_transaction_context"].copy(update={"action": "on_select"})
    payload = {"context": context, "message": {"order": {}}}
    return {"outgoing_request": {"url": f"{context.bap_uri}/on_select", "payload": payload}}

async def process_confirmation_node(state: P2PAgentState) -> dict:
    print(f"--- BPP ({state['profile'].agent_id}): PROCESSING CONFIRMATION ---")
    context, profile = state["active_transaction_context"], state["profile"]
    qty, price = (10.0, 0.15) if profile.agent_type == 'household' else (10.0, 0.25)
    offer_stub = EnergyOffer(provider_id=profile.agent_id, quantity_kwh=qty, price_per_kwh=price, valid_until=datetime.now(timezone.utc) + timedelta(seconds=10))
    contract = EnergyContract(bap_agent_id=context.bap_id, bpp_agent_id=profile.agent_id, agreed_quantity_kwh=qty, agreed_price_per_kwh=price, original_offer=offer_stub, fulfillment_start_time=datetime.now(timezone.utc) + timedelta(seconds=5))
    profile.current_energy_storage_kwh -= contract.agreed_quantity_kwh
    payload = {"context": context.copy(update={"action": "on_confirm"}), "message": {"order": contract}}
    print(f"✅ Contract finalized. Energy sold. New level: {profile.current_energy_storage_kwh:.2f}")
    # Clear transaction state after completion
    return {
        "profile": profile, 
        "outgoing_request": {"url": f"{context.bap_uri}/on_confirm", "payload": payload},
        "active_transaction_id": None,
        "active_transaction_context": None,
        "selected_offer": None,
        "final_contract": None
    }




# # src/agents/agent_graph.py
# import httpx
# from typing import List, Optional, Literal, Annotated
# from typing_extensions import TypedDict
# import operator
# from datetime import datetime, timedelta # Corrected import

# # Import models and config
# from shared.models import EnergyRequest, EnergyOffer, EnergyContract, AgentProfile, BecknContext
# from shared.config import settings
# from langchain_core.messages import BaseMessage, AIMessage

# class P2PAgentState(TypedDict):
#     """Represents the full state of a P2P agent."""
#     profile: AgentProfile
#     active_transaction_id: Optional[str]
#     active_transaction_context: Optional[BecknContext]
#     energy_request: Optional[EnergyRequest]
#     received_offers: Annotated[list, operator.add]
#     selected_offer: Optional[EnergyOffer]
#     final_contract: Optional[EnergyContract]
#     conversation_history: Annotated[list[BaseMessage], operator.add]
#     supervisor_decision: Literal["act_as_bap", "act_as_bpp", "idle", "error"]
#     flow_state: Optional[str]
#     ui_message: Optional[str]

# # --- Graph Nodes ---
# async def supervisor_node(state: P2PAgentState) -> dict:
#     """Decides the agent's next major action based on its profile."""
#     print("\n---SUPERVISOR---")
#     profile = state['profile']
#     if profile.current_energy_storage_kwh < 0.2 * profile.max_capacity_kwh:
#         decision = "act_as_bap"
#         print(f"Decision: Low energy ({profile.current_energy_storage_kwh:.2f} kWh). Acting as BAP (Buyer).")
#     elif profile.current_energy_storage_kwh > 0.8 * profile.max_capacity_kwh:
#         decision = "act_as_bpp"
#         print(f"Decision: High energy ({profile.current_energy_storage_kwh:.2f} kWh). Acting as BPP (Seller).")
#     else:
#         decision = "idle"
#         print(f"Decision: Energy stable ({profile.current_energy_storage_kwh:.2f} kWh). Idling.")
    
#     return {"supervisor_decision": decision, "flow_state": "start"}

# # --- BAP (Buyer) Workflow Nodes ---
# async def initiate_search_node(state: P2PAgentState) -> dict:
#     """Constructs and sends a UEI /search request to the gateway."""
#     print("---BAP: INITIATE SEARCH---")
#     profile = state["profile"]
#     context = BecknContext(action="search", bap_id=profile.agent_id, bap_uri=f"http://localhost:8001")
#     search_message = {"intent": {"item": {"descriptor": {"name": "renewable_energy"}}}}
#     search_payload = {"context": context.dict(), "message": search_message}
    
#     try:
#         async with httpx.AsyncClient() as client:
#             print(f"BAP sending search to gateway: {settings.BECKN_GATEWAY_URL}/search")
#             await client.post(f"{settings.BECKN_GATEWAY_URL}/search", json=search_payload)
        
#         return {
#             "active_transaction_id": context.transaction_id,
#             "active_transaction_context": context,
#             "flow_state": "awaiting_offers",
#             "ui_message": f"Search sent. TxID: {context.transaction_id[:8]}",
#             "conversation_history": [AIMessage(f"I have initiated a search for energy (TxID: {context.transaction_id}).")],
#             "received_offers": [] # Initialize as empty list
#         }
#     except httpx.RequestError as e:
#         print(f"BAP Error: Could not send search request: {e}")
#         return {"flow_state": "error", "ui_message": "Error: Could not contact gateway."}

# async def evaluate_offers_node(state: P2PAgentState) -> dict:
#     """Evaluates received offers and selects the best one."""
#     print("---BAP: EVALUATE OFFERS---")
#     offers = state.get("received_offers", [])
#     if not offers:
#         print("No offers received.")
#         return {"flow_state": "search_failed", "ui_message": "Search complete. No offers."}
    
#     best_offer = min(offers, key=lambda o: o.price_per_kwh)
#     print(f"Best offer selected: {best_offer.offer_id} from {best_offer.provider_id} at ${best_offer.price_per_kwh}/kWh")
#     return {"selected_offer": best_offer, "flow_state": "selection_made", "ui_message": f"Selected offer from {best_offer.provider_id[:8]}."}

# # --- BPP (Seller) Workflow Nodes ---
# async def formulate_offer_node(state: P2PAgentState) -> dict:
#     """Triggered by an incoming /search, formulates and sends an offer."""
#     print("---BPP: FORMULATE OFFER---")
#     bpp_profile = state["profile"]
#     incoming_context = state["active_transaction_context"]
    
#     surplus_kwh = bpp_profile.current_energy_storage_kwh - (0.5 * bpp_profile.max_capacity_kwh)
#     if surplus_kwh <= 1.0:
#         print("Not enough surplus energy to make an offer.")
#         return {"ui_message": "Ignoring search, not enough surplus."}
        
#     offer = EnergyOffer(
#         provider_id=bpp_profile.agent_id,
#         quantity_kwh=round(surplus_kwh, 2),
#         price_per_kwh=0.15,
#         valid_until=incoming_context.timestamp + timedelta(seconds=int(incoming_context.ttl)) # Corrected timedelta
#     )
    
#     context = incoming_context.copy(update={"action": "on_search", "bpp_id": bpp_profile.agent_id, "bpp_uri": "http://localhost:8001"})
#     message = {"catalog": {"items": [offer.dict()]}}
#     on_search_payload = {"context": context.dict(), "message": message}
#     bap_uri = incoming_context.bap_uri
#     if not bap_uri:
#         print("BPP Error: BAP URI not found in search context.")
#         return {"flow_state": "error", "ui_message": "Error: Cannot respond, BAP URI is missing."}
        
#     try:
#         async with httpx.AsyncClient() as client:
#             print(f"BPP sending offer to {bap_uri}/on_search")
#             await client.post(f"{bap_uri}/on_search", json=on_search_payload)
#         return {"ui_message": f"Offer sent to {bap_uri}. TxID: {context.transaction_id[:8]}"}
#     except httpx.RequestError as e:
#         print(f"BPP Error: Could not send offer: {e}")
#         return {"flow_state": "error", "ui_message": "Error: Failed to send offer."}

# # --- Conditional Edges ---
# def route_from_supervisor(state: P2PAgentState) -> Literal["initiate_search", "__end__"]:
#     """Routes execution based on the supervisor's decision."""
#     # BPP logic is reactive, so supervisor only pro-actively starts BAP flow
#     if state.get("supervisor_decision") == "act_as_bap":
#         return "initiate_search"
#     return "__end__"

# def route_after_search(state: P2PAgentState) -> Literal["evaluate_offers", "search_timeout"]:
#     """This function is for a more advanced graph. We will not use it yet."""
#     if state.get("received_offers"):
#         return "evaluate_offers"
#     return "search_timeout"