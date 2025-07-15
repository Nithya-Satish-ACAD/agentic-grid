# P2P Energy Grid Agent Demo

This project demonstrates a minimal, event-driven, two-agent system (Utility Agent and Solar Agent) using Python, FastAPI, and LangGraph. The agents run as independent services and communicate over HTTP endpoints, simulating a peer-to-peer energy grid scenario.

The architecture is explicitly designed to be modular, allowing the HTTP communication layer to be swapped out for a full Agent-to-Agent (A2A) protocol like the Beckn protocol for UEI (Universal Energy Interface) with minimal changes to the core business logic.

## Architecture

- **Utility Agent**: A FastAPI application running on `http://localhost:8000`. It acts as the grid coordinator, responsible for registering Distributed Energy Resources (DERs) like solar agents, monitoring their status via heartbeats, and issuing commands (e.g., curtailment).
- **Solar Agent**: A FastAPI application running on `http://localhost:8001`. It represents a DER. On startup, it automatically registers with the Utility Agent, sends periodic heartbeats to signal it's online, and listens for commands like `/curtailment`.
- **Communication**: All agent-to-agent communication is done via direct HTTP `POST` requests, simulating an event-driven flow. For example, when the Solar Agent sends a heartbeat, it makes a `POST` request to the Utility Agent's `/heartbeat` endpoint.
- **Business Logic**: All core business logic (e.g., how to process a registration, what to do when a command is received) is handled within workflow nodes managed by **LangGraph**. The API endpoints are "thin" and delegate all work to the workflow.

## Running the Demo

### 1. Setup

It is recommended to use a virtual environment.

```bash
# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies for both agents
# (You may need to adjust paths based on your shell)
pip install -r new-utility-agent/requirements.txt
pip install -r new-solar-agent/requirements.txt
```

### 2. Run the Agents

You need to run each agent in a separate terminal.

**Terminal 1: Start the Utility Agent**
```bash
cd new-utility-agent
python run_api.py
```
The Utility Agent will start on `http://localhost:8000`.

**Terminal 2: Start the Solar Agent**
```bash
cd new-solar-agent
python main.py
```
The Solar Agent will start on `http://localhost:8001`.

### 3. Observe the Workflow

When you start both agents, you will see the following sequence in the terminal logs:

1.  **Registration**: The Solar Agent starts up, and its workflow immediately calls the Utility Agent's `/register_der` endpoint. You will see a log on the Utility Agent's terminal confirming the registration.
2.  **Heartbeats**: The Solar Agent then starts a background task to send a heartbeat to the Utility Agent's `/heartbeat` endpoint every 30 seconds. You will see these logs appear periodically on the Utility Agent's terminal.
3.  **Check Status**: You can view the internal state of each agent by visiting their `/status` endpoints in your browser:
    -   Utility Agent Status: `http://localhost:8000/status` (shows registered DERs)
    -   Solar Agent Status: `http://localhost:8001/status` (shows if it's registered)

### 4. Test a Curtailment Command

You can manually trigger a curtailment command using `curl`. This simulates the Utility Agent's workflow deciding to issue a command.

```bash
curl -X 'POST' \
  'http://localhost:8001/curtailment' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "command_id": "cmd-1234",
    "agent_id": "solar-agent-001",
    "curtailment_kw": 10.5,
    "duration_minutes": 60
  }'
```

When you run this command, you will see:
1.  The Solar Agent logs that it received the command.
2.  Its workflow processes the command and immediately sends an acknowledgement `POST` request to the Utility Agent's `/ack` endpoint.
3.  The Utility Agent logs that it received the acknowledgement.

## Design for Upgrade to A2A Protocol

A core design principle of this demo is the separation of the communication layer from the business logic (workflows). This makes it easy to upgrade from simple HTTP calls to a standardized Agent-to-Agent protocol.

**How to Upgrade:**

1.  **Target the `comms.py` file**: All outbound HTTP calls are encapsulated in the `UtilityCommsManager` and `SolarCommsManager` classes within their respective `comms.py` files.
2.  **Replace the Implementation**: To upgrade, you would modify these manager classes. Instead of using `httpx` to make a `POST` request, you would use the client library for your chosen A2A protocol (e.g., a `BecknClient` or a custom A2A client).
3.  **Keep the Interface**: The method signatures (e.g., `send_heartbeat(payload)`) would remain the same. The workflow nodes that call these methods would not need to be changed at all.
4.  **Update Inbound Handlers**: Similarly, the FastAPI endpoint handlers (e.g., `@router.post("/heartbeat")`) would be replaced by handlers for the A2A protocol's server. These new handlers would still call the same workflow node functions to process the event.

This ensures that the agent's "brain" (the LangGraph workflow) remains independent of the "mouth and ears" (the communication protocol). 

## UEI Protocol Implementation Note

This project uses a **simplified, synchronous** implementation of the Beckn/UEI protocol for the discovery process. For demonstration and simulation purposes, the `search` request from the BAP (Solar Agent) receives the `catalog` in a direct HTTP response.

A fully compliant implementation would be **asynchronous**, where the BPP (Utility Agent) would acknowledge the `search` request and then send the `catalog` to a separate `/on_search` endpoint on the BAP. This has been marked with `TODO: UEI-Compliance` comments in the codebase for future development. 