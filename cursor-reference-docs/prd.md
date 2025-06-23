Project Overview

Purpose:

Build a robust, modular Solar Agent as a standalone microservice.

Validate core patterns: LangGraph workflows, MCP integration (weather-mcp-server), adapter pattern for hardware abstraction, multi-tenant readiness, modular code structure, production-grade practices.

Provide comprehensive documentation for an AI-assisted coding environment (e.g., Cursor) to generate production-quality code with minimal hallucination.

Scope:

Simulated/mocked inverter data via adapter interface, easily swappable for real hardware later.

Integration with third-party Weather MCP server (sjanaX01/weather-mcp-server) for weather data.

REST API for registration, status, forecast, alerts, command endpoint to receive control actions.

Internal logic orchestrated by LangGraph: forecasting and anomaly detection/explanation flows.

Configurable via environment variables; structured logging, metrics exposure.

SQLite for PoC state if needed; design for future PostgreSQL migration.

Auth via static API keys for PoC; future JWT/OIDC.

Stakeholders:

Backend Engineers: implement Solar Agent microservice.

DevOps: Docker Compose, later Kubernetes deployment.

Data/ML: forecast logic, prompt templates, LLM integration.

Security: review auth, secret handling, third-party MCP security.

QA/Test: unit, integration, load, and failure-mode tests.

Product Owner: define functional requirements (forecast interval, anomaly thresholds).