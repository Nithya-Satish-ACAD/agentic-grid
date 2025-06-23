Directory Layout

solar_agent/
├── adapters/
│   ├── base.py           # InverterAdapter interface
│   └── simulated.py      # SimAdapter returning synthetic readings; includes failure simulation flags
├── api/
│   ├── main.py           # FastAPI app instantiation, include router, middleware
│   ├── routes.py         # registration, status, forecast, alert, commands endpoints
│   └── dependencies.py   # auth (API key), config injection, correlation ID
├── core/
│   ├── context_manager.py # manage recent readings history
│   ├── forecast_engine.py # statistical forecasting stub or initial model
│   ├── anomaly_detector.py# threshold logic, triggers LangGraphFlow
│   └── scheduler.py      # startup registration and periodic task loop using asyncio tasks or APScheduler
├── ai/
│   ├── prompt_manager.py  # load/render prompt templates from prompt-templates/solar/
│   ├── langgraph_flows.py # define LangGraph flows: anomaly_explanation flow
│   └── tools.py           # weather_mcp_tool, llm_tool wrappers with timeout and schema validation
├── clients/
│   ├── utility_client.py  # post to Utility endpoints with retry/backoff; include correlation ID
│   └── mcp_client.py      # call Weather MCP JSON-RPC; validate response; caching layer
├── models/
│   ├── schemas.py         # Pydantic models: RegisterPayload, StatusPayload, ForecastPayload, AlertPayload, CommandPayload
│   └── config.py          # read env vars into dataclasses: SITE_ID, AGENT_ID, UTILITY_URL, API_KEYS, WEATHER_MCP_URL, thresholds, intervals
├── utils/
│   ├── logging.py         # configure structured logger, integrate correlation ID
│   ├── metrics.py         # define Prometheus counters/gauges (forecasts_sent, alerts_sent, llm_calls, mcp_calls, errors)
│   └── correlation.py     # generate and propagate correlation IDs across async context and HTTP headers
├── prompt-templates/
│   └── solar/
│       ├── anomaly_explanation.prompt
│       └── anomaly_explanation.meta.yaml
├── tests/
│   ├── unit/
│   │   ├── test_adapters.py
│   │   ├── test_forecast_engine.py
│   │   ├── test_anomaly_detector.py
│   │   └── test_langgraph_flows.py (with mocked tools)
│   └── integration/
│       ├── test_registration_flow.py (mock Utility)
│       └── test_periodic_cycle.py (mock MCP and Utility)
├── Dockerfile
├── docker-compose.yml     # for local PoC with solar_agent, weather-mcp-server, utility_stub
├── requirements.txt
└── README.md              # setup, env var definitions, running tests, architecture summary

Key Modules Details

adapters/base.py:

from abc import ABC, abstractmethod

class InverterAdapter(ABC):
    @abstractmethod
    async def get_reading(self) -> dict:
        '''Return {'timestamp': ..., 'power_kw': ..., 'status': ...}'''

adapters/simulated.py: implement sinusoidal or random readings; accept config for failure injection.

core/context_manager.py: maintain a deque of recent readings; provide history to forecast_engine.

core/forecast_engine.py: simple moving average or placeholder; signature predict(history: list[dict], weather: dict) -> list[dict].

core/anomaly_detector.py: compare reading vs prediction; threshold from config; on anomaly call langgraph_flows.analyze_anomaly(readings, weather).

ai/prompt_manager.py: load prompt file and metadata; render with Jinja2 or simple templating.

ai/langgraph_flows.py: define LangGraph flow:

register tools: weather_mcp_tool and llm_tool

function analyze_anomaly(readings, weather): call tools, parse response.

ai/tools.py:

weather_mcp_tool(params): HTTPX call to WEATHER_MCP_URL; JSON-RPC body; validate result schema.

llm_tool(params): call OpenAI with timeout; parse text; return raw text for JSON parsing.

clients/utility_client.py: functions register_agent(), post_forecast(), post_alert() with retry/backoff using httpx or tenacity.

clients/mcp_client.py: caching layer (in-memory TTL) for repeated weather calls; schema validation using Pydantic.

api/routes.py: define endpoints:

POST /agents/register expects RegisterPayload; calls utility_client.register_agent at startup only.

POST /agents/{agent_id}/status for heartbeat.

POST /agents/{agent_id}/forecast and /alerts for manual or test invocation if needed.

POST /commands/solar to receive commands.

GET /health and /metrics.

utils/logging.py: configure JSON logger, include correlation ID in logs.

utils/metrics.py: initialize Prometheus metrics and integrate with FastAPI endpoint /metrics.

core/scheduler.py: on startup, schedule periodic async tasks: reading->forecast->anomaly->send; ensure robust error handling and cancellation on shutdown.