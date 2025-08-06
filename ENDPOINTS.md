# API Endpoints Documentation

This document outlines the API endpoints for each service in the P2P Energy Grid Simulation.

## 1. Mock Beckn Gateway

**Base URL:** `http://localhost:9000`

### `GET /registry`

Returns the list of all registered Beckn Provider Platforms (BPPs). Used by the Utility Agent for agent discovery.

- **Response:**
    ```json
    {
      "agents": [
        "http://household_agent_1:8001",
        "http://household_agent_2:8003",
        "http://household_agent_3:8005",
        "http://household_agent_4:8007",
        "http://household_agent_5:8009",
        "http://household_agent_6:8011",
        "http://household_agent_7:8013",
        "http://household_agent_8:8015",
        "http://household_agent_9:8017",
        "http://household_agent_10:8019",
        "http://utility_agent:8002"
      ]
    }
    ```

### `POST /register`

Registers a Beckn Provider Platform (BPP) so that it can be discovered. All agents (household and utility) call this on startup.

- **Request Body:**
    ```json
    {
      "bpp_uri": "http://agent-url:port"
    }
    ```
- **Response:**
    ```json
    {
      "status": "success"
    }
    ```

### `POST /search`

Receives a search request from a Beckn Application Platform (BAP) and broadcasts it to all registered BPPs in the background.

- **Request Body:** A standard Beckn search payload.
    ```json
    {
      "context": {
        "domain": "ONIX:energy",
        "action": "search",
        "version": "1.0.0",
        "bap_id": "household-agent-01",
        "bap_uri": "http://household_agent_1:8001",
        "transaction_id": "abc123-def456",
        "bpp_id": "",
        "bpp_uri": "",
        "city": "",
        "country": "",
        "core_version": "1.0.0",
        "message_id": "msg123",
        "timestamp": "2025-08-06T06:15:34.383982"
      },
      "message": {
        "intent": {}
      }
    }
    ```
- **Response:** An immediate Beckn Acknowledgement.
    ```json
    {
      "message": {
        "ack": {
          "status": "ACK"
        }
      }
    }
    ```

---

## 2. Household Agents & Utility Agent

**Base URLs:**
- Household Agent 1: `http://localhost:8001`
- Household Agent 2: `http://localhost:8003`
- Household Agent 3: `http://localhost:8005`
- Household Agent 4: `http://localhost:8007`
- Household Agent 5: `http://localhost:8009`
- Household Agent 6: `http://localhost:8011`
- Household Agent 7: `http://localhost:8013`
- Household Agent 8: `http://localhost:8015`
- Household Agent 9: `http://localhost:8017`
- Household Agent 10: `http://localhost:8019`
- Utility Agent: `http://localhost:8002`

### `GET /profile`

Returns the current state of the agent, including energy levels, role, and transaction history.

- **Response:**
    ```json
    {
      "agent_id": "household-agent-01",
      "agent_type": "household",
      "current_energy_storage_kwh": 12.54,
      "max_capacity_kwh": 15.0,
      "current_role": "IDLE",
      "total_energy_purchased_kwh": 45.2,
      "total_energy_sold_kwh": 12.8,
      "total_transactions": 8,
      "last_transaction_time": "2025-08-06T06:15:34.383982"
    }
    ```

### `POST /a2a`

Handles Agent-to-Agent (A2A) protocol requests. Used by the Utility Agent to collect data from household agents.

- **Request Body:**
    ```json
    {
      "jsonrpc": "2.0",
      "method": "createTask",
      "id": 1,
      "params": {
        "message": {
          "skillId": "get_soc_data"
        }
      }
    }
    ```
- **Response:**
    ```json
    {
      "jsonrpc": "2.0",
      "id": 1,
      "result": {
        "agent_id": "household-agent-01",
        "current_energy_storage_kwh": 12.54,
        "max_capacity_kwh": 15.0,
        "state_of_charge_percent": 83.6
      }
    }
    ```

### `POST /{action:path}`

This single endpoint handles all Beckn transaction messages. The `action` in the URL path corresponds to the `context.action` field in a Beckn request.

#### Role: Agent as a BPP (Seller)

An agent acts as a BPP when it receives these requests:

- **`POST /search`**: Receives a forwarded search request from the Gateway. Triggers the `formulate_offer` logic.
- **`POST /select`**: Receives a selection confirmation from a BAP. Triggers the `process_selection` logic.
- **`POST /init`**: Receives an initialization request from a BAP. Triggers the `process_init` logic.
- **`POST /confirm`**: Receives the final order confirmation from a BAP. Triggers the `process_confirmation` logic.

#### Role: Agent as a BAP (Buyer)

An agent acts as a BAP when it receives these callback requests:

- **`POST /on_search`**: Receives a catalog of offers from a BPP. Triggers the `evaluate_offers` logic.
- **`POST /on_select`**: Receives confirmation that its selection was received. Triggers the `send_init` logic.
- **`POST /on_init`**: Receives initialization confirmation from the BPP. Triggers the `send_confirm` logic.
- **`POST /on_confirm`**: Receives the finalized contract from the BPP. Triggers the `process_bap_completion` logic.

All requests to this endpoint expect a standard Beckn JSON payload and will return a standard Beckn `ACK` response immediately, while processing the logic in a background task.

---

## 3. Utility Agent Admin Endpoints

**Base URL:** `http://localhost:8002`

### `POST /admin/request-data`

Triggers the Utility Agent to collect data from all household agents using the A2A protocol.

- **Request Body:** Empty or optional parameters
    ```json
    {}
    ```
- **Response:**
    ```json
    {
      "status": "success",
      "message": "Data collection initiated",
      "agents_contacted": 10,
      "timestamp": "2025-08-06T06:15:34.383982"
    }
    ```

### `GET /admin/collected-data`

Returns the most recently collected data from all household agents.

- **Response:**
    ```json
    {
      "timestamp": "2025-08-06T06:15:34.383982",
      "data_collection": [
        {
          "agent_id": "household-agent-01",
          "current_energy_storage_kwh": 12.54,
          "max_capacity_kwh": 15.0,
          "state_of_charge_percent": 83.6
        },
        {
          "agent_id": "household-agent-02",
          "current_energy_storage_kwh": 14.2,
          "max_capacity_kwh": 15.0,
          "state_of_charge_percent": 94.7
        }
        // ... data for all 10 household agents
      ]
    }
    ```

---

## 4. Beckn Protocol Message Flow

### Complete 5-Step Beckn Flow

The system implements the complete Beckn protocol flow:

1. **Search** (`POST /search`): Buyer initiates energy search
2. **Select** (`POST /select`): Buyer selects cheapest offer
3. **Init** (`POST /init`): Transaction initialization
4. **Confirm** (`POST /confirm`): Final confirmation
5. **Status** (`POST /on_confirm`): Transaction completion

### Example Transaction Flow

```
1. household-agent-01 (BAP) → Gateway: POST /search
2. Gateway → All BPPs: POST /search (broadcast)
3. household-agent-02 (BPP) → household-agent-01: POST /on_search (offer)
4. utility-agent (BPP) → household-agent-01: POST /on_search (offer)
5. household-agent-01 → household-agent-02: POST /select (selection)
6. household-agent-02 → household-agent-01: POST /on_select (confirmation)
7. household-agent-01 → household-agent-02: POST /init (initialization)
8. household-agent-02 → household-agent-01: POST /on_init (init confirmation)
9. household-agent-01 → household-agent-02: POST /confirm (final confirmation)
10. household-agent-02 → household-agent-01: POST /on_confirm (completion)
```

### Price Competition

- **Household Agents**: $0.15/kWh (competitive pricing)
- **Utility Agent**: $0.25/kWh (premium pricing)
- **Selection Logic**: `min(offers, key=lambda o: o.price_per_kwh)` ensures cheapest wins

---

## 5. Testing Endpoints

### Check System Status

```bash
# Check Gateway registry
curl http://localhost:9000/registry

# Check individual agent states
curl http://localhost:8001/profile  # Household Agent 1
curl http://localhost:8002/profile  # Utility Agent

# Trigger data collection
curl -X POST http://localhost:8002/admin/request-data

# View collected data
curl http://localhost:8002/admin/collected-data
```

### Monitor Transactions

```bash
# View logs to see Beckn protocol in action
docker-compose logs -f | grep "Contract confirmed"
docker-compose logs -f | grep "Best offer selected"
docker-compose logs -f | grep "A2A DATA COLLECTION"
```

---

## 6. Error Handling

All endpoints return appropriate HTTP status codes:

- **200 OK**: Successful operation
- **400 Bad Request**: Invalid request format
- **404 Not Found**: Endpoint not found
- **500 Internal Server Error**: Server-side error

### Common Error Scenarios

1. **Agent Registration Failures**: Check Gateway logs for registration issues
2. **Network Connectivity**: Ensure containers can communicate with each other
3. **Transaction Failures**: Check agent logs for Beckn protocol errors
4. **Data Collection Failures**: Verify A2A protocol implementation

The system provides **comprehensive error handling** and **detailed logging** for debugging and monitoring purposes.