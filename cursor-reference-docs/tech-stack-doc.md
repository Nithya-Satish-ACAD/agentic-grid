Core Languages & Frameworks

Python 3.10+

FastAPI for REST and WebSocket/SSE if needed

LangGraph for internal AI workflows

OpenAI SDK or local LLM via LangServe for llm_tool

Docker & Docker Compose for PoC

SQLite for PoC state (optional: in-memory or file); plan for SQLAlchemy/Alembic for future PostgreSQL

Redis (optional) for cache/session if needed

Libraries

Pydantic for data models and schema validation

HTTPX or requests for HTTP client calls to Utility and MCP

Prometheus client for metrics exposure

structlog or Python logging with JSON formatter for structured logs

pytest and pytest-asyncio for testing

mermaid diagrams in docs

Bandit, Safety for security scanning

Infrastructure & Deployment

Dockerfile: containerize Solar Agent; entrypoint runs FastAPI & scheduler

Docker Compose: run solar-agent plus weather-mcp-server and Utility stub for integration tests

Kubernetes (future): Helm/Kustomize manifests; ConfigMaps for env; Secrets for API keys; readiness/liveness probes; resource quotas

CI/CD: GitHub Actions: lint, type-check (mypy), unit tests, build image; optionally push to registry

Monitoring: Prometheus scraping endpoint /metrics; Grafana dashboards for agent metrics (forecast counts, alert counts, LLM latency)