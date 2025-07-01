# Solar Agent

A modular, production-ready backend for distributed solar energy management, designed for standalone operation or integration into a multi-agent grid (with Utility, Battery, Load agents, etc).

---

## Features

- **Modular Hardware Adapters:** Easily extend to new inverter/solar hardware.
- **LLM-Agnostic:** Supports OpenAI, Gemini, and local LLMs via Ollama.
- **LangGraph Workflows:** Flexible, human-in-the-loop, and fault-tolerant agent logic.
- **REST API:** FastAPI-based endpoints for control, monitoring, and integration.
- **Production-Ready:** Designed for Kubernetes, scalable messaging, and robust observability.

---

## Project Structure

```
src/solar_agent/
  adapters/      # Hardware abstraction (Sunspec, mock, etc)
  api/           # FastAPI endpoints and models
  core/          # Config, exceptions, core models
  llm/           # LLM provider interfaces (OpenAI, Gemini, Ollama)
  tools/         # Data generation, forecasting, MCP client
  workflow/      # LangGraph workflows, nodes, state
```

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Nithya-Satish-ACAD/agentic-grid.git
cd agentic-grid
git checkout solar-agent
```

### 2. Setup Environment

- Copy and edit environment variables:
  ```bash
  cp env.template .env
  ```
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

### 3. Run Locally

```bash
python main.py
```

Or with Docker:

```bash
docker-compose up --build
```

---

## API Usage

- REST endpoints documented via FastAPI at `/docs` when running.
- Example: `POST /api/solar/command` to send a control command.

---

## Contributing

- Use feature branches off `solar-agent`.
- Ensure all code is linted and tested (`run_tests.py`).
- Open a Pull Request for review.

---

## License

MIT

---

## Acknowledgements

- Built with [LangGraph](https://github.com/langchain-ai/langgraph), [FastAPI](https://fastapi.tiangolo.com/), and [Ollama](https://ollama.com/).

## 🚀 Features

### Core Capabilities
- **LangGraph Workflow Orchestration**: Stateful multi-step AI workflows with LLM integration
- **Hardware Abstraction**: Adapter pattern supporting SunSpec Modbus and mock data
- **REST API**: Comprehensive FastAPI endpoints for agent communication
- **Solar Forecasting**: LLM-powered generation forecasting with weather data integration
- **Curtailment Management**: Automated response to utility curtailment commands
- **Fault Detection**: Real-time monitoring and alerting for hardware faults
- **Human-in-the-Loop**: Support for manual approval of critical operations

### System Architecture
- **Modular Design**: Clean separation between adapters, workflow, and API layers
- **Production Ready**: Docker containerization, comprehensive logging, monitoring
- **Scalable**: Async/await patterns, background task processing
- **Configurable**: Environment-based configuration with sensible defaults
- **Testable**: Mock adapters and comprehensive test coverage

## 📋 Requirements

- Python 3.9+
- Docker & Docker Compose (for containerized deployment)
- OpenAI API key (for LLM-based forecasting)
- SunSpec-compatible inverters (optional, mock adapter available)

## 🛠️ Installation

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd solar-agent
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.template .env
   # Edit .env with your configuration
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

### Docker Deployment

1. **Basic deployment**
   ```bash
   docker-compose up -d
   ```

2. **With monitoring stack**
   ```bash
   docker-compose --profile monitoring up -d
   ```

3. **Production with PostgreSQL**
   ```bash
   docker-compose --profile production up -d
   ```

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Utility Agent │    │  Weather Service │    │   Human Operator│
│                 │    │    (MCP Server)  │    │                 │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          │ Curtailment          │ Weather Data         │ Approvals
          │ Commands             │                      │
          ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Solar Agent                               │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐     │
│  │   FastAPI     │  │   LangGraph   │  │    Tools      │     │
│  │   Endpoints   │  │   Workflow    │  │ - Forecasting │     │
│  │               │  │               │  │ - MCP Client  │     │
│  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘     │
│          │                  │                  │             │
│          └──────────────────┼──────────────────┘             │
│                             │                                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                Hardware Adapters                       │ │
│  │  ┌─────────────┐              ┌─────────────┐         │ │
│  │  │ Mock Adapter│              │SunSpec      │         │ │
│  │  │             │              │Adapter      │         │ │
│  │  └─────────────┘              └─────────────┘         │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
          │                                    │
          │ Simulated Data                     │ Modbus/TCP
          ▼                                    ▼
┌─────────────────┐                  ┌─────────────────┐
│  Mock Solar     │                  │  Physical Solar │
│  Installation   │                  │  Installation   │
└─────────────────┘                  └─────────────────┘
```

## 🔧 Configuration

### Environment Variables

Key configuration options (see `.env.template` for complete list):

```bash
# Agent Identity
SOLAR_AGENT_ID=solar-001
SOLAR_CAPACITY_KW=100.0

# Hardware Configuration
SOLAR_USE_MOCK_ADAPTER=true        # Use mock data for development
SOLAR_SUNSPEC_HOST=192.168.1.100   # SunSpec inverter IP
SOLAR_SUNSPEC_PORT=502             # Modbus port

# LLM Configuration
OPENAI_API_KEY=your-key-here
SOLAR_LLM_MODEL=gpt-3.5-turbo

# Workflow Settings
SOLAR_WORKFLOW_INTERVAL_SECONDS=30
SOLAR_ENABLE_PERSISTENCE=true
```

## 📡 API Endpoints

### Core Endpoints

- `POST /api/v1/curtailment` - Receive curtailment commands
- `GET /api/v1/status` - Get agent status and metrics
- `GET /api/v1/heartbeat` - Health check endpoint
- `POST /api/v1/alerts` - Send alerts to utility agent

### Management Endpoints

- `POST /api/v1/approval` - Human approval for critical operations
- `GET /api/v1/faults` - Get current fault status
- `POST /api/v1/maintenance` - Enter maintenance mode
- `GET /api/v1/metrics` - Performance metrics

### Example Usage

```bash
# Check agent status
curl http://localhost:8000/api/v1/status

# Send curtailment command
curl -X POST http://localhost:8000/api/v1/curtailment \
  -H "Content-Type: application/json" \
  -d '{
    "target_output_kw": 50.0,
    "duration_minutes": 60,
    "priority": 5,
    "reason": "Grid balancing"
  }'
```

## 🔄 LangGraph Workflow

The system uses a sophisticated LangGraph workflow with the following nodes:

1. **read_solar_data** - Read current solar panel data
2. **generate_forecast** - Create generation forecasts using LLM
3. **check_performance** - Compare actual vs predicted performance
4. **raise_underperformance_alert** - Alert on performance issues
5. **await_curtailment** - Wait for curtailment commands
6. **apply_curtailment** - Execute curtailment instructions
7. **monitor_faults** - Continuous fault monitoring
8. **raise_fault_alert** - Alert on hardware faults
9. **maintenance_mode** - Handle maintenance operations

### Workflow Features

- **Conditional Logic**: Dynamic routing based on system state
- **State Persistence**: Workflow state survives restarts
- **Human Interrupts**: Manual intervention for critical decisions
- **Error Handling**: Robust error recovery and retry logic

## 🔌 Hardware Adapters

### Mock Adapter (Development)
```python
from solar_agent.adapters import MockAdapter

adapter = MockAdapter(
    agent_id="solar-001",
    capacity_kw=100.0
)
```

Features:
- Realistic solar generation curves
- Weather effect simulation
- Configurable fault injection
- Time-based output patterns

### SunSpec Adapter (Production)
```python
from solar_agent.adapters import SunSpecAdapter

adapter = SunSpecAdapter(
    host="192.168.1.100",
    port=502,
    unit_id=1
)
```

Features:
- Modbus/TCP communication
- SunSpec register mapping
- Real-time data reading
- Fault status monitoring

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=solar_agent

# Run specific test suite
pytest tests/test_workflow.py
```

## 📊 Monitoring

### Prometheus Metrics
- Solar generation metrics
- Workflow execution times
- API request rates
- Fault counts

### Grafana Dashboards
- Real-time solar output
- Performance vs forecast
- System health metrics
- Alert summaries

Access Grafana at `http://localhost:3000` (admin/admin) when using monitoring profile.

## 🚀 Deployment

### Development
```bash
docker-compose up -d
```

### Production
```bash
# With PostgreSQL and Redis
docker-compose --profile production up -d

# With full monitoring stack
docker-compose --profile production --profile monitoring up -d
```

### Kubernetes
Kubernetes manifests available in `k8s/` directory for production deployment.

## 🔧 Development

### Code Quality
```bash
# Format code
black src/

# Sort imports
isort src/

# Type checking
mypy src/

# Linting
flake8 src/
```

### Adding New Adapters
1. Inherit from `HardwareAdapter` base class
2. Implement required async methods
3. Add to `adapters/__init__.py`
4. Update configuration options

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- Documentation: See `docs/` directory
- Issues: GitHub Issues
- Email: team@solargrid.com

## 🔮 Roadmap

- [ ] Time-series database integration (InfluxDB/TimescaleDB)
- [ ] Advanced ML forecasting models
- [ ] Multi-agent coordination protocols
- [ ] Edge computing deployment
- [ ] Blockchain integration for energy trading
- [ ] Advanced fault prediction algorithms 