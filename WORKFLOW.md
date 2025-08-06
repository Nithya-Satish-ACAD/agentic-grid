# P2P Energy Grid Transaction Workflow

This document traces a complete P2P energy transaction in the multi-agent system, showing how the Beckn Gateway and autonomous agents interact.

## System Overview

The simulation consists of:
- **1 Beckn Gateway** - Protocol gateway for agent discovery and message routing
- **1 Utility Agent** - Grid operator with unlimited capacity ($0.25/kWh)
- **10 Household Agents** - Individual energy prosumers ($0.15/kWh)
- **1 Reporter Service** - Generates periodic reports every 2 minutes

### Agent Configuration

| Agent | Initial SoC | Role | Energy Model | Price |
|-------|-------------|------|--------------|-------|
| household-agent-01 | 15% | Buyer | Consumes -0.03 kWh/cycle | $0.15/kWh |
| household-agent-02 | 95% | Seller | Generates +0.02 kWh/cycle | $0.15/kWh |
| household-agent-03 | 15% | Buyer | Consumes -0.03 kWh/cycle | $0.15/kWh |
| household-agent-04 | 95% | Seller | Generates +0.02 kWh/cycle | $0.15/kWh |
| household-agent-05 | 15% | Buyer | Consumes -0.03 kWh/cycle | $0.15/kWh |
| household-agent-06 | 95% | Seller | Generates +0.02 kWh/cycle | $0.15/kWh |
| household-agent-07 | 15% | Buyer | Consumes -0.03 kWh/cycle | $0.15/kWh |
| household-agent-08 | 95% | Seller | Generates +0.02 kWh/cycle | $0.15/kWh |
| household-agent-09 | 15% | Buyer | Consumes -0.03 kWh/cycle | $0.15/kWh |
| household-agent-10 | 95% | Seller | Generates +0.02 kWh/cycle | $0.15/kWh |
| utility-agent-01 | 999,999 kWh | Grid Operator | Unlimited capacity | $0.25/kWh |

## Example Transaction: Household Agent Buys Energy

### Scenario

- **Buyer**: `household-agent-01` starts with low battery (2.25 kWh out of 15.0 kWh)
- **Sellers**: Multiple household agents and utility agent are online with surplus energy
- **Gateway**: All agents have successfully registered as BPPs (sellers)

---

## Step-by-Step Beckn Protocol Flow

### Step 1: Decision to Buy (Household Agent)

- **Trigger**: The agent's internal `agent_simulation_loop` runs its 20-second cycle
- **Action**: The `supervisor_node` in its LangGraph brain checks its profile
- **Decision**: Since `2.25 kWh` is less than the 30% threshold (`4.5 kWh`), it decides to act as a **BAP (Buyer)**
- **Result**: The graph's state is updated, and the flow is routed to the `initiate_search` node

**Log**: `--- SUPERVISOR: Energy low (2.25 kWh), starting BAP flow ---`

### Step 2: Search Request (Household Agent → Gateway)

- **Trigger**: The `initiate_search_node` is executed
- **Action**: The node constructs a Beckn `/search` request payload with the agent's context
- **Dispatch**: The agent's `invoke_and_dispatch` function sends this as an HTTP POST request to the Gateway's `/search` endpoint

**Log**: `--- DISPATCHING HTTP POST to http://gateway:9000/search ---`

**Payload**:
```json
{
  "context": {
    "domain": "ONIX:energy",
    "action": "search",
    "bap_id": "household-agent-01",
    "bap_uri": "http://household_agent_1:8001",
    "transaction_id": "abc123-def456"
  },
  "message": {
    "intent": {}
  }
}
```

### Step 3: Broadcast (Gateway → All Sellers)

- **Trigger**: The Gateway receives the `/search` request
- **Action**: It immediately returns an `ACK` response to the buyer
- **Background**: It looks up its registry and finds all registered sellers
- **Broadcast**: It forwards the original search payload to all potential sellers

**Log**: 
```
Gateway received search request: abc123-def456
Gateway forwarding search to http://household_agent_2:8003/search
Gateway forwarding search to http://household_agent_4:8007/search
Gateway forwarding search to http://household_agent_6:8011/search
Gateway forwarding search to http://household_agent_8:8015/search
Gateway forwarding search to http://household_agent_10:8019/search
Gateway forwarding search to http://utility_agent:8002/search
```

### Step 4: Formulating Offers (Multiple Sellers)

**Household Agent 2 (as BPP)**:
- **Trigger**: Receives the forwarded `/search` request
- **Action**: Its `formulate_offer_node` runs
- **Decision**: Since its battery is high (95% SoC), it has surplus energy to sell
- **Offer**: Creates an `EnergyOffer` for 10.0 kWh at $0.15/kWh
- **Dispatch**: Sends `/on_search` callback to the buyer

**Log**: 
```
--- BPP (household-agent-02): FORMULATE OFFER ---
--- DISPATCHING HTTP POST to http://household_agent_1:8001/on_search ---
```

**Utility Agent (as BPP)**:
- **Trigger**: Also receives the forwarded `/search` request
- **Action**: Its `formulate_offer_node` runs
- **Offer**: Creates an `EnergyOffer` for 500.0 kWh at $0.25/kWh
- **Dispatch**: Sends `/on_search` callback to the buyer

**Log**:
```
--- BPP (utility-agent-01): FORMULATE OFFER ---
--- DISPATCHING HTTP POST to http://household_agent_1:8001/on_search ---
```

**Other Household Agents**:
- Some agents may be "offline" (30% chance) and don't respond
- Some agents may have insufficient surplus energy and don't make offers

### Step 5: Evaluation and Selection (Buyer)

- **Trigger**: The buyer receives multiple `/on_search` callbacks from different sellers
- **Action**: The graph is invoked, routing to the `evaluate_offers_node`
- **Evaluation**: This node analyzes the list of received offers
- **Selection**: Uses `min(offers, key=lambda o: o.price_per_kwh)` to select the cheapest offer
- **Result**: The graph flow proceeds to the `send_select` node

**Log**: `Best offer selected: $0.15/kWh from household-agent-02`

**Offers Received**:
- household-agent-02: 10.0 kWh at $0.15/kWh
- utility-agent-01: 500.0 kWh at $0.25/kWh
- **Selected**: household-agent-02 (cheapest)

### Step 6: The Complete Beckn Handshake

A rapid, automated negotiation now occurs directly between the two agents:

#### 6a. Select Phase
- **Buyer**: `send_select_node` dispatches a `/select` request to the chosen seller
- **Seller**: Receives `/select`, runs `process_selection_node`, dispatches `/on_select` back

#### 6b. Init Phase
- **Buyer**: `send_init_node` dispatches an `/init` request to the seller
- **Seller**: Receives `/init`, runs `process_init_node`, dispatches `/on_init` back

#### 6c. Confirm Phase
- **Buyer**: `send_confirm_node` dispatches a final `/confirm` request
- **Seller**: Receives `/confirm`, runs `process_confirmation_node`, finalizes the contract, updates its state, dispatches `/on_confirm`

### Step 7: Completion (Buyer)

- **Trigger**: The buyer receives the final `/on_confirm` callback containing the finalized contract details
- **Action**: The graph routes to the `process_bap_completion_node`
- **Update**: This node updates the agent's internal state, increasing its battery level with the purchased energy
- **Result**: The transaction is complete

**Log**: `✅ Contract confirmed! Energy purchased. New battery level: 12.25 kWh`

## Market Dynamics

### Energy Flow Patterns

1. **Buyers Consume**: Energy levels decrease over time (-0.03 kWh/cycle)
2. **Sellers Generate**: Energy levels increase over time (+0.02 kWh/cycle)
3. **Transactions**: Energy transfers between agents when needed
4. **Market Balance**: 5 buyers vs 6 sellers (good supply-demand ratio)

### Price Competition

- **Household Agents**: $0.15/kWh (competitive pricing)
- **Utility Agent**: $0.25/kWh (premium pricing)
- **Selection Logic**: `min(offers, key=lambda o: o.price_per_kwh)` ensures cheapest wins
- **Market Efficiency**: Buyers always get the best available price

### Partial Participation

- **30% Chance**: Agents are "offline" during searches
- **Realistic Behavior**: Simulates real-world agent availability
- **Market Resilience**: System continues to function even with some agents unavailable

## Data Collection Flow

### Utility Agent Data Collection

Every 5 minutes, the Utility Agent:

1. **Discovers Agents**: Queries the Beckn Gateway registry
2. **Sends A2A Requests**: Direct agent-to-agent data requests
3. **Collects SoC Data**: Gets state of charge from all household agents
4. **Stores Data**: Saves collected data for analysis

**Log**:
```
--- UTILITY: Waking up to collect data from all households ---
Discovered agents: ['http://household_agent_1:8001', 'http://household_agent_2:8003', ...]
--- A2A DATA COLLECTION COMPLETE ---
--- STORED data collection: 10 agents ---
```

## Reporting System

### Periodic Reports

Every 2 minutes, the Reporter Service:

1. **Collects Profiles**: Queries all agents' `/profile` endpoints
2. **Generates Report**: Creates timestamped JSON report
3. **Saves Report**: Stores in `./reports/` directory

**Report Format**:
```json
{
  "timestamp": "2025-08-06T06:15:34.383982",
  "agents": [
    {
      "agent_id": "household-agent-01",
      "current_energy_storage_kwh": 12.54,
      "max_capacity_kwh": 15.0,
      "current_role": "IDLE"
    },
    // ... all other agents
  ]
}
```

## System State After Transaction

The system is now in a new state:

- **Buyer**: Energy level increased from 2.25 kWh to 12.25 kWh
- **Seller**: Energy level decreased by the transferred amount
- **Market**: Ready for the next transaction cycle
- **Reports**: Updated with new energy levels

The loop continues, with agents' energy levels changing naturally over time, driving new transactions as needed.

## Key Features Demonstrated

- **✅ Complete Beckn Protocol Implementation**
- **✅ Multi-Agent Price Competition**
- **✅ Dynamic Energy Market**
- **✅ Automatic Data Collection**
- **✅ Real-time Reporting**
- **✅ Scalable Architecture**

This workflow demonstrates a **production-ready P2P energy grid** using the Beckn protocol! 🚀