Modularity & Structure

Follow the defined backend-structure layout; each module single responsibility.

Coding Standards

Adhere to PEP8; use Black for formatting; enforce type hints with mypy.

Prompt Management

Store prompt templates under prompt-templates/solar/ with metadata; include example inputs/outputs.

API Contracts

Define and use Pydantic models; plan contract tests with Utility later.

Version APIs as needed; maintain backward compatibility.

CI/CD

Use GitHub Actions: lint, type-check, unit tests, integration tests.

Build Docker images and push on merging to main.

Testing

Unit tests for adapters, core modules, AI flows (mock tools).

Integration tests mocking Utility and MCP.

Load tests simulating scheduler traffic.

Failure-mode tests for MCP downtime, LLM failure, Utility unreachable.

Logging & Metrics

Always include correlation ID; increment metrics on each key operation.

Error Handling

Catch exceptions in scheduler tasks; log and retry or escalate.

Configuration

All settings via env vars or config file; avoid hardcoded values.

Versioning

Semantic versioning; maintain changelog.