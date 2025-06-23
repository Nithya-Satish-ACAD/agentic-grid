# Solar Agent

A robust, modular Solar Agent microservice for solar power monitoring, forecasting, and anomaly detection.

## Overview

Solar Agent is a standalone microservice that integrates with solar inverters to provide:
- Real-time power monitoring
- AI-powered forecasting using weather data
- Anomaly detection and analysis
- Integration with Utility Agent for grid coordination

## Features

- **Modular Architecture**: Clean separation of concerns with adapter pattern for hardware abstraction
- **AI Integration**: LangGraph workflows for anomaly analysis and OpenAI integration
- **Weather Integration**: MCP (Model Context Protocol) integration for weather data
- **Production Ready**: Structured logging, metrics, correlation IDs, and comprehensive error handling
- **Configurable**: Environment-based configuration with sensible defaults
- **Testable**: Comprehensive unit and integration tests

## Quick Start

### Prerequisites

- Python 3.10+
- Virtual environment (recommended)
- API keys for OpenAI (optional, for anomaly analysis)

### Installation

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd solar-agent
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

4. **Run the application**:
   ```bash
   uvicorn solar_agent.api.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Configuration

Key environment variables (see `env.example` for complete list):

- `SITE_ID`: Your solar site identifier
- `AGENT_ID`: Unique agent identifier (auto-generated if not provided)
- `UTILITY_URL`: URL of the Utility Agent
- `WEATHER_MCP_URL`: URL of the Weather MCP server
- `API_KEY_SOLAR`: API key for authentication
- `LLM_API_KEY`: OpenAI API key for anomaly analysis
- `FORECAST_INTERVAL`: Seconds between forecast cycles (default: 300)
- `ANOMALY_THRESHOLD`: Deviation threshold for anomaly detection (default: 0.15)

## API Endpoints

### Core Endpoints

- `POST /api/v1/agents/register` - Register agent with Utility
- `POST /api/v1/agents/{agent_id}/status` - Update agent status
- `POST /api/v1/agents/{agent_id}/forecast` - Post power forecast
- `POST /api/v1/agents/{agent_id}/alerts` - Post anomaly alerts
- `POST /api/v1/commands/solar` - Execute inverter commands

### Monitoring Endpoints

- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `GET /docs` - API documentation (Swagger UI)

## Architecture

### Directory Structure

```
solar_agent/
├── adapters/          # Hardware abstraction layer
├── api/              # FastAPI application and routes
├── core/             # Business logic components
├── ai/               # AI/ML components and LangGraph flows
├── clients/          # External service clients
├── models/           # Data models and configuration
├── utils/            # Utilities (logging, metrics, correlation)
└── tests/            # Unit and integration tests

prompt-templates/
└── solar/            # AI prompt templates

cursor-reference-docs/ # Project documentation
```

### Key Components

- **Adapters**: Hardware abstraction for different inverter types
- **Context Manager**: Maintains readings history for forecasting
- **Forecast Engine**: Generates power predictions using historical data and weather
- **Anomaly Detector**: Identifies deviations from expected power output
- **LangGraph Flows**: AI-powered anomaly analysis workflows
- **Scheduler**: Manages periodic execution of monitoring tasks

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/

# Run with coverage
pytest --cov=solar_agent
```

### Code Quality

```bash
# Format code
black solar_agent/

# Type checking
mypy solar_agent/

# Security scanning
bandit -r solar_agent/
```

### Docker

```bash
# Build image
docker build -t solar-agent .

# Run container
docker run -p 8000:8000 --env-file .env solar-agent
```

## Docker Compose

For local development with all services:

```bash
docker-compose up -d
```

This starts:
- Solar Agent (port 8000)
- Weather MCP Server (port 8002)
- Utility Agent stub (port 8001)

## Documentation

Comprehensive documentation is available in `cursor-reference-docs/`:

- `prd.md` - Product Requirements Document
- `backend-structure.md` - Detailed architecture specification
- `flow-doc.md` - System flow diagrams and narratives
- `tech-stack-doc.md` - Technology stack details
- `implementation-plan.md` - Development roadmap
- `security-checklist.md` - Security considerations
- `project-rules.md` - Development guidelines

## Contributing

1. Follow the project structure and coding standards
2. Add tests for new functionality
3. Update documentation as needed
4. Ensure all tests pass before submitting

## License

[Add your license information here]

## Support

For issues and questions, please refer to the documentation or create an issue in the repository. 