Sequence Flow (Mermaid)

sequenceDiagram
    participant Solar as Solar Agent
    participant MCP as Weather MCP
    participant Utility as Utility Agent

    Solar->>Solar: startup: load config, init adapter, generate agent_id
    Solar->>Utility: POST /agents/register {agent_id, site_id, location}
    Utility-->>Solar: 200 OK

    loop periodic cycle
        Solar->>Solar: adapter.get_reading()
        Solar->>MCP: get_weather(location, horizon)
        MCP-->>Solar: weather data JSON
        Solar->>Solar: forecastEngine.predict(readings, weather)
        Solar->>Solar: anomalyDetector.check(actual, predicted)
        alt deviation > threshold
            Solar->>Solar: langgraphFlow.invoke(readings, weather)
            Solar->>LLM: prompt anomaly_explanation
            LLM-->>Solar: JSON {causes, severity, recommendations}
            Solar->>Utility: POST /agents/{agent_id}/alerts {severity, explanation, timestamp}
            Utility-->>Solar: 200 OK or retry logic
        else no anomaly
            Solar->>Utility: POST /agents/{agent_id}/forecast {forecast array, timestamp}
            Utility-->>Solar: 200 OK
        end
    end

    Solar->>Solar: on receiving POST /commands/solar
    Solar-->>Solar: commandHandler.apply(params) via adapter
    Solar->>Utility: optionally report command acknowledgment

Component Diagram (Mermaid)

flowchart LR
  subgraph SolarAgent["Solar Agent"]
    A1["ConfigManager"]
    A2["AuthMiddleware (API key)"]
    A3["SimAdapter / InverterAdapter"]
    A4["ContextManager"]
    A5["ForecastEngine"]
    A6["AnomalyDetector"]
    A7["LangGraphFlow Solar"]
    A8["MCP Client"]
    A9["LLM Client"]
    A10["API Endpoints (FastAPI)"]
    A11["Metrics & Logging"]
    A12["Scheduler"]
  end

  A3 --> A4
  A4 --> A5
  A5 --> A6
  A6 --> A7
  A7 --> A8
  A8 --> MCP[Weather MCP]
  A7 --> A9
  A6 -->|no anomaly| A10 --> Utility[Utility Agent]
  A6 -->|anomaly| A10 --> Utility
  Utility -->|commands| A10
  A10 --> A3
  A11 --> A3
  A11 --> A5
  A11 --> A7
  A12 --> A3
  A12 --> A5
  A12 --> A6

Narrative Flow

Startup: load env config (SITE_ID, AGENT_ID or generate, UTILITY_URL, API keys, WEATHER_MCP_URL, intervals, thresholds), init structured logger and metrics, instantiate adapter (SimAdapter), init LangGraph with tools.

Registration: call Utility’s /agents/register with agent_id, site_id, capabilities, location.

Periodic Loop (Scheduler):

Reading: adapter.get_reading() returns structured reading (timestamp, power_kw, status fields).

Weather Fetch: mcp_client.call(method="get_weather", params{location, horizon}); validate schema.

Forecast: forecast_engine.predict(readings_history, weather) returns list of {timestamp, predicted_kw}.

Anomaly Check: compare latest actual vs predicted; if deviation > threshold:

Invoke LangGraphFlow: tool calls: weather_mcp_tool (cached if recent), llm_tool with prompt template anomaly_explanation, parse JSON response.

Publish alert: POST /agents/{agent_id}/alerts with payload including severity, explanation, timestamp.

No Anomaly: send forecast: POST /agents/{agent_id}/forecast with forecast array and timestamp.

Error Handling: retries with backoff on Utility or MCP failures; fallback: default forecast or log error; if MCP fails, skip anomaly flow or use cached weather.

Command Handling: expose POST /commands/solar: validate API key, parse CommandPayload, call adapter methods (e.g., enter maintenance mode), log outcome, optionally report ack to Utility.

Shutdown: on SIGTERM, attempt deregistration or final status update.