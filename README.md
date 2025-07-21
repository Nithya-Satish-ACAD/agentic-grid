# P2P Energy Grid Simulation

This project simulates a decentralized peer-to-peer (P2P) energy grid using a multi-agent system. It features autonomous Solar and Utility agents that can buy and sell energy credits on a network governed by the Beckn protocol. The entire system is built with modern, asynchronous Python technologies.

## Core Technologies

- **Python 3.12**: The core programming language.
- **FastAPI**: A high-performance ASGI web framework used to create the API endpoints for each agent and the gateway.
- **LangGraph**: A library for building stateful, multi-agent applications. It serves as the "brain" or orchestration layer for each agent, managing their internal state and decision-making workflows.
- **Pydantic**: Used for data modeling and validation, ensuring that all communication between agents adheres to a strict, self-documenting schema.
- **uv**: An extremely fast Python package installer and manager, used for dependency management and running the virtual environment.
- **httpx**: A fully featured async-ready HTTP client used by agents to communicate with each other and the gateway.

## Architecture Overview

The simulation consists of three primary services running independently:

1.  **Mock Beckn Gateway (`src/protocols/beckn/mock_gateway.py`)**: A simple FastAPI service that acts as a network registry. BPPs (Beckn Provider Platforms, i.e., sellers) register their endpoints here. It facilitates discovery by broadcasting search requests from BAPs (Beckn Application Platforms, i.e., buyers) to all registered BPPs.

2.  **Solar Agent (`src/agents/solar/main.py`)**: An autonomous agent representing a prosumer with a solar panel and battery.
    -   Acts as a **BAP (Buyer)** when its battery is low, initiating a search for energy.
    -   Acts as a **BPP (Seller)** when its battery is full, responding to search requests with offers to sell surplus energy.

3.  **Utility Agent (`src/agents/utility/main.py`)**: An autonomous agent representing a traditional power utility.
    -   Primarily acts as a **BPP (Seller)**, responding to any search for energy with a standard offer.
    -   Is architected to potentially act as a BAP to buy energy during high-demand scenarios (not yet implemented in the simulation loop).

### Project Structure

The project follows the `src/` layout, a best practice for Python applications to ensure clean and reliable imports.

```
gemini-p2p/
│
├── src/
│   ├── agents/             # Core agent logic and applications
│   │   ├── solar/
│   │   ├── utility/
│   │   └── agent_graph.py  # Shared LangGraph state and nodes
│   ├── protocols/          # Network protocol implementations
│   │   └── beckn/
│   │       └── mock_gateway.py
│   └── shared/             # Shared code (models, config)
│       ├── config.py
│       └── models.py
├── tests/                  # (Placeholder for tests)
├── .env                    # Environment variables for service URLs
└── pyproject.toml          # Project metadata and dependencies
```

## Getting Started

### Prerequisites

- Python 3.12
- `uv` package manager (`pip install uv`)

### Installation

1.  **Clone the repository:**
    ```sh
    git clone <repo-url>
    cd <directory-name>
    ```

2.  **Create the virtual environment:**
    ```sh
    uv venv
    ```

3.  **Activate the environment:**
    ```sh
    source .venv/bin/activate
    ```

4.  **Install dependencies:**
    The project is installed in editable mode (`-e`) so changes to the source code are immediately reflected.
    ```sh
    uv pip install -e .
    ```

5.  **Configure Environment:**
    The `.env` file is pre-configured to run all services locally. No changes are needed.

## Running the Simulation

You must run the three services in three separate terminals from the project's root directory.

**Important:** Start the services in the following order to ensure the Gateway is ready before the agents try to register.

**1. Terminal 1: Start the Mock Beckn Gateway**
```sh
uvicorn src.protocols.beckn.mock_gateway:app --port 9000 --reload
```

**2. Terminal 2: Start the Utility Agent**
```sh
uvicorn src.agents.utility.main:app --port 8002 --reload
```

**3. Terminal 3: Start the Solar Agent**
```sh
uvicorn src.agents.solar.main:app --port 8001 --reload
```

### What to Expect

Once all three services are running, the simulation will begin automatically. In the **Solar Agent's terminal**, you will see a detailed log every ~25 seconds that traces a complete transaction:
1.  The agent's supervisor checks its low battery and decides to initiate a search.
2.  The gateway broadcasts this search to the Utility Agent.
3.  The Utility Agent sends an offer back.
4.  The Solar Agent evaluates and selects the offer.
5.  A rapid handshake of `select` and `confirm` messages occurs.
6.  The transaction completes with a success message: `✅ Contract confirmed! Energy purchased. New battery level: ...`

The loop will then continue, with the Solar Agent's battery level slowly increasing.