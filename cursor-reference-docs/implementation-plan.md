Repository & Setup

Create repo solar_agent/ with directory layout as in backend-structure.md.

Write README.md with setup instructions, env var definitions, running tests, architecture summary.

Create requirements.txt listing dependencies: fastapi, uvicorn, langgraph, openai, httpx, pydantic, prometheus-client, pytest, structlog, etc.

Write Dockerfile to install dependencies and set entrypoint.

Write docker-compose.yml including solar_agent, weather-mcp-server, and a stub Utility (or real Utility endpoint URL via env).

Core Modules Development

Config & Logger: Implement models/config.py and utils/logging.py.

Adapter Interface: adapters/base.py; implement adapters/simulated.py with failure simulation.

Context Manager: core/context_manager.py maintaining readings history.

Forecast Engine: core/forecast_engine.py stub or simple algorithm.

Anomaly Detector: core/anomaly_detector.py; integrate LangGraph flow.

AI Integration

Prompt Templates: Create prompt-templates/solar/anomaly_explanation.prompt and metadata YAML.

MCP Client: clients/mcp_client.py with caching and validation.

LLM Client: in ai/tools.py, wrapper with timeout and error handling.

LangGraph Flow: ai/langgraph_flows.py implement analyze_anomaly(readings, weather).

Tests: Unit tests mocking MCP and LLM.

API & Clients

Pydantic Schemas: models/schemas.py for payloads.

Utility Client: clients/utility_client.py with retry/backoff.

API Routes: api/routes.py; dependencies for auth and config.

FastAPI App: api/main.py setup, middleware, metrics endpoint.

Scheduler & Startup

Scheduler: core/scheduler.py for periodic tasks and registration.

Startup/Shutdown Events: In FastAPI app, launch and cancel scheduler.

Observability

Metrics: utils/metrics.py define Prometheus counters; expose /metrics.

Logging: Structured logs with correlation IDs.

Tracing: Plan for OpenTelemetry integration.

Testing

Unit Tests: adapters, core modules, AI flows.

Integration Tests: simulate endpoints with TestClient; mock Utility/MCP.

Load Tests: simulate scheduler load.

Failure Scenarios: test MCP/LLM/Utility failures and fallbacks.

CI/CD

GitHub Actions: lint, mypy, tests.

Docker Build & Push: on main branch.

Dev Deployment: Docker Compose or Kubernetes dev cluster; integration tests.

Documentation for Cursor Agent

Supply these markdown files: PRD.md, flow-doc.md, tech-stack-doc.md, backend-structure.md, security-checklist.md, project-rules.md, implementation-plan.md.

Include .env.example and prompt templates under prompt-templates/solar/.

Provide guidance for iterative code generation and testing.