# Utility Agent PoC: DEG/Beckn-Ready, Event-Driven, Multi-Agent Orchestrator

## Overview

This project implements a production-grade Utility Agent Proof of Concept (PoC) aligned with Digital Energy Grid (DEG) and Beckn guidelines. It serves as a grid coordinator, managing Distributed Energy Resources (DERs) like Solar, Load, and Battery agents through event-driven communication over a message bus (NATS). Agents can run independently on different hosts/IPs, enabling cross-host orchestration.

### Key Features
- **Event-Driven Design:** Uses NATS for pub/sub messaging between agents.
- **DEG/Beckn Readiness:** Stub endpoints and schemas for Beckn flows, modular for full integration.
- **Workflow Orchestration:** LangGraph for stateful workflows, including curtailment, conflict resolution, and alerts.
- **Extensibility:** Dynamic DER registration, stubs for new agent types.
- **Production-Ready:** Structured logging, async operations, tests, metrics.

## Architecture

- **Event Bus (NATS):** Handles pub/sub for status updates, commands, and responses (topics like `solar.status`, `utility.curtailment`).
- **API Layer (FastAPI):** Exposes endpoints for management and Beckn stubs.
- **Workflow (LangGraph):** Nodes for collecting status, negotiating flexibility, resolving conflicts, etc., with persistent state.
- **Adapters:** Modular interfaces for DER types (solar, load, battery).
- **Beckn Provisions:** Validated stubs for flows like on_search, confirm.

Agent Roles:
- **Utility Agent:** Orchestrates grid, issues commands, monitors responses.
- **Solar Agent:** (Stubbed) Responds to curtailment, publishes status.
- **Load/Battery Agents:** Future extensions via stubs.

## Setup and Running

1. **Environment:**
   - Python 3.11+
   - Install dependencies: `uv venv; source .venv/bin/activate; uv pip install -r requirements.txt` (generate requirements.txt if needed).
   - Configure `.env` (e.g., `EVENT_BUS_URL=nats://localhost:4222`).

2. **Run NATS Server:** 
   - Via Docker: `docker run -p 4222:4222 nats`
   - Natively (without Docker, e.g., on macOS): Install via Homebrew `brew install nats-server`, then run `nats-server`.

3. **Run Utility Agent API:** From the project root, run `python run_api.py` (includes reload for development).

4. **Run Tests:** From project root, run `PYTHONPATH=. pytest tests/` to handle package imports.

If curtailment fails with 'Failed to issue curtailment', ensure NATS is running (`docker ps` to check) and EVENT_BUS_URL in .env points to it.
If you see deprecation warnings for 'on_event' in logs, they've been updated to use lifespan handlers—rerun after code updates.
If tests fail with ModuleNotFoundError, ensure all imports use consistent relative or absolute paths—code updates should resolve this.

5. **Cross-Host Testing:**
   - Run NATS on one host.
   - Start Utility Agent on host A, simulated Solar on host B (use eventbus test_harness: `PYTHONPATH=. python utility_agent/adapters/eventbus.py` from project root).
   - Issue curtailment via API; check logs for pub/sub.

## Endpoints

- **/api/status (GET):** Utility state and registered DERs.
- **/api/curtailment (POST):** Issue curtailment plan.
- **/api/alerts (GET):** Operator alerts.
- **/api/register_der (POST):** Register new DER.
- **/api/conflicts (GET):** Current conflicts.
- **/health (GET):** Health check.
- **/metrics (GET):** Basic metrics.
- **/api/beckn/on_search (POST), /confirm, /on_confirm:** Beckn stubs.

## Message Schemas

- Use Pydantic models in `api/models.py` (e.g., DERStatus, FlexibilityPlan).
- Beckn payloads validated against stub schemas in `beckn/protocol.py`.

## Extending the System

### Adding New DER Agents (e.g., Load/Battery)
1. Implement adapter in `adapters/{type}_adapter.py` (e.g., specific logic).
2. Add topics to `eventbus.py` TOPICS.
3. Register via /register_der API.
4. Extend workflow nodes in `nodes.py` for type-specific handling.
5. Update tests.

### Full Beckn Integration
1. Expand models in `beckn/protocol.py` to full Beckn/UEI specs.
2. Implement real handlers (e.g., integrate with LangGraph workflow).
3. Add signing, authentication, and registry as per Beckn protocol.

For questions, refer to the code comments or open an issue.
