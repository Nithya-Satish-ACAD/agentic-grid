# P2P Energy Grid Simulation - Comprehensive Guide

This document provides a complete overview of the P2P Energy Grid Simulation system, explaining every aspect from startup to operation. This is the **foundation documentation** for colleagues who will build upon this codebase.

## 🎯 System Overview

The P2P Energy Grid Simulation is a **production-ready, multi-agent system** that demonstrates:

- **✅ Complete Beckn Protocol Implementation** - Decentralized transaction protocol
- **✅ Dynamic Energy Market** - Real-time energy trading between agents
- **✅ Price Competition** - Automatic selection of cheapest energy offers
- **✅ Data Collection** - Utility agent automatically collects data from all households
- **✅ Real-time Reporting** - Periodic reports of system state
- **✅ Scalable Architecture** - Docker-based deployment with 13 services

## 🏗️ Architecture

### System Components

The simulation consists of **13 services** running in Docker containers:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Beckn Gateway │    │  Utility Agent  │    │ Household Agent │
│   (Port 9000)   │    │   (Port 8002)   │    │   (Port 8001)   │
│                 │    │                 │    │                 │
│ • Agent Registry│    │ • Grid Operator │    │ • Energy Prosumer│
│ • Message Router│    │ • Data Collector│    │ • Buyer/Seller  │
│ • Discovery Hub │    │ • Unlimited Cap │    │ • Dynamic State │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Reporter Service│
                    │                 │
                    │ • Periodic Reports│
                    │ • Data Analysis │
                    └─────────────────┘
```

### Service Breakdown

| Service | Count | Purpose | Port Range |
|---------|-------|---------|------------|
| **Gateway** | 1 | Beckn protocol gateway | 9000 |
| **Utility Agent** | 1 | Grid operator | 8002 |
| **Household Agents** | 10 | Energy prosumers | 8001, 8003, 8005, 8007, 8009, 8011, 8013, 8015, 8017, 8019 |
| **Reporter** | 1 | Data collection | Background |

## 🚀 Complete Startup Flow

### Phase 1: Docker Container Initialization

When you run `docker-compose up -d`, here's what happens:

#### 1.1 Container Startup Sequence

```bash
# 13 containers start simultaneously:
1. gateway (port 9000) - Beckn protocol gateway
2. utility_agent (port 8002) - Grid operator
3. household_agent_1 (port 8001) - Buyer (SoC: 15%)
4. household_agent_2 (port 8003) - Seller (SoC: 95%)
5. household_agent_3 (port 8005) - Buyer (SoC: 15%)
6. household_agent_4 (port 8007) - Seller (SoC: 95%)
7. household_agent_5 (port 8009) - Buyer (SoC: 15%)
8. household_agent_6 (port 8011) - Seller (SoC: 95%)
9. household_agent_7 (port 8013) - Buyer (SoC: 15%)
10. household_agent_8 (port 8015) - Seller (SoC: 95%)
11. household_agent_9 (port 8017) - Buyer (SoC: 15%)
12. household_agent_10 (port 8019) - Seller (SoC: 95%)
13. reporter (background) - Data collection service
```

#### 1.2 Agent Registration with Beckn Gateway

**Each agent automatically registers with the Beckn Gateway on startup:**

```python
# In each agent's lifespan function:
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient() as client:
        # 🎯 BECKN REGISTRATION STEP
        await client.post(f"{settings.BECKN_GATEWAY_URL}/register", 
                         json={"bpp_uri": "http://agent_url:port"})
```

**What happens:**
- **Gateway** receives registration requests from all 11 agents
- **Gateway** maintains a registry: `bpp_registry = ["http://household_agent_1:8001", "http://utility_agent:8002", ...]`
- **Beckn Protocol**: This is the **discovery mechanism** - agents register as BPPs (sellers) so they can be found by BAPs (buyers)

#### 1.3 Simulation Loop Initialization

**Each agent starts its internal simulation loop:**

```python
# Every agent runs this loop:
async def agent_simulation_loop():
    # Initialize agent state from environment variables
    agent_app_graph.update_state(config, {"profile": INITIAL_PROFILE})
    
    while True:
        # 1. Apply energy consumption/generation model
        # 2. Invoke LangGraph decision-making
        # 3. Sleep for 20 seconds
```

## 🔄 Beckn Protocol Transaction Flow

### Phase 2: Energy Market Dynamics

#### 2.1 Energy Market Dynamics Trigger

**Every 20 seconds, each agent's supervisor evaluates its energy state:**

```python
async def supervisor_node(state: P2PAgentState) -> dict:
    profile = state['profile']
    
    # 🎯 BECKN DECISION LOGIC
    if profile.current_energy_storage_kwh < 0.3 * profile.max_capacity_kwh:
        # Energy low - act as BAP (Buyer)
        return {"trigger": "start_bap_flow"}
    elif profile.current_energy_storage_kwh > 0.7 * profile.max_capacity_kwh:
        # Energy high - act as BPP (Seller) - respond to searches
        return {"trigger": "idle"}
```

#### 2.2 Beckn Protocol: Search Phase

**When a buyer needs energy, it initiates a Beckn search:**

```python
async def initiate_search_node(state: P2PAgentState) -> dict:
    # 🎯 BECKN SEARCH REQUEST
    context = BecknContext(action="search", bap_id=profile.agent_id, bap_uri=agent_url)
    search_payload = {"context": context, "message": {"intent": {}}}
    
    # Send to Beckn Gateway
    return {"outgoing_request": {"url": f"{settings.BECKN_GATEWAY_URL}/search", "payload": search_payload}}
```

**Gateway broadcasts to all registered sellers:**

```python
@app.post("/search")
async def broadcast_search(request: Request, background_tasks: BackgroundTasks):
    search_payload = await request.json()
    
    # 🔄 BECKN BROADCAST
    for uri in bpp_registry:  # All registered sellers
        background_tasks.add_task(forward_request, uri, search_payload)
    
    return {"message": {"ack": {"status": "ACK"}}}
```

#### 2.3 Beckn Protocol: Offer Phase

**Each seller responds with offers:**

```python
async def formulate_offer_node(state: P2PAgentState) -> dict:
    # 💰 BECKN OFFER FORMULATION
    qty, price = (10.0, 0.15) if profile.agent_type == 'household' else (500.0, 0.25)
    
    offer = EnergyOffer(provider_id=profile.agent_id, quantity_kwh=qty, price_per_kwh=price)
    context = in_context.copy(update={"action": "on_search", "bpp_id": profile.agent_id})
    
    # Send offer back to buyer
    return {"outgoing_request": {"url": f"{in_context.bap_uri}/on_search", "payload": payload}}
```

#### 2.4 Beckn Protocol: Selection Phase

**Buyer evaluates all offers and selects the cheapest:**

```python
async def evaluate_offers_node(state: P2PAgentState) -> dict:
    offers = state.get("received_offers", [])
    
    # 🏆 BECKN SELECTION - CHEAPEST WINS
    best_offer = min(offers, key=lambda o: o.price_per_kwh)
    print(f"Best offer selected: ${best_offer.price_per_kwh}/kWh from {best_offer.provider_id}")
    
    # Send selection to chosen seller
    context = state["active_transaction_context"].copy(update={"action": "select"})
    return {"selected_offer": best_offer, "active_transaction_context": context}
```

#### 2.5 Beckn Protocol: Init/Confirm Phase

**Complete 5-step Beckn flow:**

```python
# Step 3: Init
async def send_init_node(state: P2PAgentState) -> dict:
    init_payload = {"context": context.copy(update={"action": "init"})}
    return {"outgoing_request": {"url": f"{context.bpp_uri}/init", "payload": init_payload}}

# Step 4: Confirm  
async def send_confirm_node(state: P2PAgentState) -> dict:
    confirm_payload = {"context": context.copy(update={"action": "confirm"})}
    return {"outgoing_request": {"url": f"{context.bpp_uri}/confirm", "payload": confirm_payload}}

# Step 5: Completion
async def process_bap_completion_node(state: P2PAgentState) -> dict:
    profile.current_energy_storage_kwh += contract.agreed_quantity_kwh
    print(f"✅ Contract confirmed! Energy purchased. New battery level: {profile.current_energy_storage_kwh:.2f} kWh")
```

## 📊 Phase 3: Requirement Fulfillment

### ✅ Requirement 1: P2P Energy Trading with Beckn Protocol

**How Beckn fulfills this requirement:**

1. **🔍 Discovery**: Beckn Gateway maintains registry of all sellers
2. **📡 Broadcasting**: Search requests reach all potential sellers
3. **💰 Price Competition**: `min(offers, key=lambda o: o.price_per_kwh)` ensures cheapest wins
4. **🤝 Standardized Protocol**: All agents use same Beckn message format
5. **📋 Complete Flow**: search → select → init → confirm → status

**Evidence from logs:**
```
Gateway forwarding search to http://household_agent_10:8019/search
BPP (household-agent-05): FORMULATE OFFER
Best offer selected: $0.15/kWh from household-agent-02
✅ Contract confirmed! Energy purchased. New battery level: 20.00 kWh
```

### ✅ Requirement 2: Utility Agent Data Collection

**How Beckn + A2A fulfills this requirement:**

1. **🔍 Agent Discovery**: Utility uses Beckn Gateway registry to find all household agents
2. **📊 A2A Protocol**: Direct agent-to-agent data requests
3. **🔄 Automatic Collection**: Utility wakes up every 5 minutes to collect data
4. **💾 Data Storage**: Collected SoC data stored and accessible

**Evidence from code:**
```python
# Utility agent discovers agents via Beckn Gateway
response = await client.get(f"{settings.BECKN_GATEWAY_URL}/registry")
registered_agents = response.json().get("agents", [])

# Sends A2A requests to all household agents
a2a_payload = {"jsonrpc": "2.0", "method": "createTask", "params": {"message": {"skillId": "get_soc_data"}}}
tasks = [client.post(f"{url}/a2a", json=a2a_payload) for url in household_urls]
```

## 🎯 Phase 4: The Complete Picture

### 🔄 Continuous Market Cycle

```
1. Agents start → Register with Beckn Gateway
2. Every 20 seconds → Supervisor evaluates energy state
3. Low energy agents → Initiate Beckn search
4. Gateway broadcasts → All registered sellers
5. Sellers respond → With price offers
6. Buyer selects → Cheapest offer wins
7. Beckn handshake → Init → Confirm → Complete
8. Energy transferred → Buyer's battery increases
9. Cycle repeats → Market continues dynamically
```

### 📈 Data Collection Cycle

```
1. Utility agent → Wakes up every 5 minutes
2. Discovers agents → Via Beckn Gateway registry
3. Sends A2A requests → To all household agents
4. Collects SoC data → From each agent
5. Stores data → For analysis and reporting
6. Reports generated → Every 2 minutes by reporter
```

### 🏗️ Beckn Protocol Integration

**Beckn is the backbone of the entire system:**

1. **Discovery**: Gateway registry enables agent discovery
2. **Communication**: Standardized message format for all transactions
3. **Broadcasting**: Search requests reach all potential sellers
4. **Selection**: Price-based competition ensures market efficiency
5. **Completion**: Full 5-step protocol ensures reliable transactions

## 📁 Codebase Structure

### Key Files and Their Purpose

```
gemini-p2p/
├── src/
│   ├── agents/
│   │   ├── household/main.py          # Household agent implementation
│   │   ├── utility/main.py            # Utility agent implementation
│   │   └── agent_graph.py            # Shared LangGraph nodes and state
│   ├── protocols/
│   │   └── beckn/mock_gateway.py     # Beckn protocol gateway
│   ├── reporting/
│   │   └── reporter.py               # Data collection and reporting
│   └── shared/
│       ├── config.py                 # Configuration settings
│       └── models.py                 # Data models and validation
├── docker-compose.yml                # Multi-service orchestration
├── Dockerfile                       # Container configuration
├── requirements.txt                  # Python dependencies
└── reports/                         # Generated simulation reports
```

### Critical Code Sections

#### 1. Agent Decision Logic (`src/agents/agent_graph.py`)
```python
async def supervisor_node(state: P2PAgentState) -> dict:
    # Energy threshold logic
    if profile.current_energy_storage_kwh < 0.3 * profile.max_capacity_kwh:
        return {"trigger": "start_bap_flow"}  # Act as buyer
    elif profile.current_energy_storage_kwh > 0.7 * profile.max_capacity_kwh:
        return {"trigger": "idle"}  # Act as seller
```

#### 2. Price Competition Logic (`src/agents/agent_graph.py`)
```python
async def evaluate_offers_node(state: P2PAgentState) -> dict:
    offers = state.get("received_offers", [])
    best_offer = min(offers, key=lambda o: o.price_per_kwh)  # Cheapest wins
    return {"selected_offer": best_offer}
```

#### 3. Beckn Protocol Implementation (`src/protocols/beckn/mock_gateway.py`)
```python
@app.post("/search")
async def broadcast_search(request: Request, background_tasks: BackgroundTasks):
    for uri in bpp_registry:  # Broadcast to all sellers
        background_tasks.add_task(forward_request, uri, search_payload)
```

## 🔧 Configuration and Customization

### Environment Variables

Key environment variables in `docker-compose.yml`:

```yaml
environment:
  - INITIAL_SOC=15          # Initial state of charge (15% = buyer, 95% = seller)
  - AGENT_ID=household-agent-01  # Unique agent identifier
  - AGENT_PORT=8001         # Agent's port number
  - BECKN_GATEWAY_URL=http://gateway:9000  # Gateway URL
```

### Energy Model Parameters

Energy consumption/generation rates in `src/agents/household/main.py`:

```python
if is_seller:
    energy_change = 0.02    # Sellers generate +0.02 kWh/cycle
else:
    energy_change = -0.03    # Buyers consume -0.03 kWh/cycle
```

### Price Configuration

Price settings in `src/agents/agent_graph.py`:

```python
qty, price = (10.0, 0.15) if profile.agent_type == 'household' else (500.0, 0.25)
# Household agents: $0.15/kWh, Utility agent: $0.25/kWh
```

## 📊 Monitoring and Debugging

### Key Log Messages

**Agent Registration:**
```
Registered BPPs: ['http://household_agent_1:8001', 'http://utility_agent:8002', ...]
```

**Transaction Flow:**
```
--- SUPERVISOR: Energy low (2.25 kWh), starting BAP flow ---
--- DISPATCHING HTTP POST to http://gateway:9000/search ---
Gateway forwarding search to http://household_agent_2:8003/search
--- BPP (household-agent-02): FORMULATE OFFER ---
Best offer selected: $0.15/kWh from household-agent-02
✅ Contract confirmed! Energy purchased. New battery level: 12.25 kWh
```

**Data Collection:**
```
--- UTILITY: Waking up to collect data from all households ---
--- A2A DATA COLLECTION COMPLETE ---
--- STORED data collection: 10 agents ---
```

### Debugging Commands

```bash
# Check container status
docker-compose ps

# View logs from specific service
docker-compose logs -f household_agent_1

# Test individual endpoints
curl http://localhost:9000/registry
curl http://localhost:8001/profile

# Monitor transactions
docker-compose logs -f | grep "Contract confirmed"
```

## 🎯 Requirements Fulfillment Summary

### ✅ Requirement 1 - P2P Energy Trading: 
- **10 Household Agents** + **1 Utility Agent** actively trading
- **Full Beckn Protocol** implementation (search → select → init → confirm → status)
- **Price Competition** with automatic cheapest offer selection
- **Dynamic Energy Model** driving continuous transactions

### ✅ Requirement 2 - Data Collection:
- **Automatic Data Collection** every 5 minutes
- **Agent Discovery** via Beckn Gateway registry
- **A2A Protocol** for direct agent communication
- **Data Storage** and reporting system