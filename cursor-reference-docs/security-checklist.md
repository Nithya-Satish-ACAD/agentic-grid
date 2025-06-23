Auth & Authorization

Validate static API key header matches configured value; store mapping to agent_id/site_id.

Structure code for future JWT validation.

Transport Security

For PoC, HTTP is acceptable; plan TLS for production.

Ensure HTTP client enforces TLS when configured.

Input Validation

Use Pydantic models for all incoming requests; reject extra fields.

Validate MCP responses against Pydantic schema; fallback on invalid data.

Secrets Management

Store API keys, URLs, and LLM credentials via environment variables; do not commit secrets.

Third-Party MCP Security

Clone weather-mcp-server at a known commit; scan dependencies; run in isolated container.

Validate response structure; handle timeouts and errors.

Logging & Monitoring

Structured logs without sensitive data; include correlation IDs.

Expose metrics: forecasts_sent, alerts_sent, mcp_calls, llm_calls, errors.

Resilience & Fallbacks

Implement timeouts & retries for MCP and Utility calls; fallback forecast or skip anomaly analysis if necessary.

Use circuit breaker pattern to avoid retry storms.

Expose health endpoint; handle graceful shutdown and optional deregistration.

Data Protection

For PoC minimal; plan encryption at rest/in transit for production.