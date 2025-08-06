# P2P Energy Grid Simulation

This project simulates a decentralized peer-to-peer (P2P) energy grid using a multi-agent system. It features **10 Household Agents** and **1 Utility Agent** that can buy and sell energy using the **Beckn Protocol**. The entire system is built with modern, asynchronous Python technologies and runs in Docker containers.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.12 (for development)

### Run the Simulation

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Test the setup
python test_docker_setup.py
```

## 🏗️ Architecture Overview

The simulation consists of **13 services** running in Docker containers:

### Core Services
1. **Mock Beckn Gateway** (`gateway:9000`) - Protocol gateway for agent discovery and message routing
2. **Utility Agent** (`utility_agent:8002`) - Grid operator with unlimited capacity
3. **10 Household Agents** (`household_agent_1` through `household_agent_10`) - Individual energy prosumers
4. **Reporter Service** - Generates periodic reports every 2 minutes

### Agent Configuration

| Agent | Port | Initial SoC | Role | Energy Model |
|-------|------|-------------|------|--------------|
| household-agent-01 | 8001 | 15% | Buyer | Consumes -0.03 kWh/cycle |
| household-agent-02 | 8003 | 95% | Seller | Generates +0.02 kWh/cycle |
| household-agent-03 | 8005 | 15% | Buyer | Consumes -0.03 kWh/cycle |
| household-agent-04 | 8007 | 95% | Seller | Generates +0.02 kWh/cycle |
| household-agent-05 | 8009 | 15% | Buyer | Consumes -0.03 kWh/cycle |
| household-agent-06 | 8011 | 95% | Seller | Generates +0.02 kWh/cycle |
| household-agent-07 | 8013 | 15% | Buyer | Consumes -0.03 kWh/cycle |
| household-agent-08 | 8015 | 95% | Seller | Generates +0.02 kWh/cycle |
| household-agent-09 | 8017 | 15% | Buyer | Consumes -0.03 kWh/cycle |
| household-agent-10 | 8019 | 95% | Seller | Generates +0.02 kWh/cycle |
| utility-agent-01 | 8002 | 999,999 kWh | Grid Operator | Unlimited capacity |

## 🔄 Beckn Protocol Implementation

The system implements the complete **5-step Beckn protocol flow**:

1. **Search** - Buyer initiates energy search
2. **Select** - Buyer selects cheapest offer
3. **Init** - Transaction initialization
4. **Confirm** - Final confirmation
5. **Status** - Transaction completion

### Market Dynamics

- **Price Competition**: Household agents ($0.15/kWh) vs Utility agent ($0.25/kWh)
- **Partial Participation**: 30% chance agents are "offline" during searches
- **Dynamic Energy Flow**: Buyers consume, sellers generate energy over time
- **Automatic Selection**: `min(offers, key=lambda o: o.price_per_kwh)` ensures cheapest wins

## 📊 Data Collection & Reporting

### A2A Protocol Implementation

- **Utility Agent** automatically collects data from all household agents every 5 minutes
- **Agent Discovery** via Beckn Gateway registry
- **SoC Data Collection** using A2A protocol
- **Data Storage** accessible via `/admin/collected-data` endpoint

### Reporting System

- **Periodic Reports**: Generated every 2 minutes
- **Agent States**: Complete energy levels and transaction history
- **Market Analysis**: Supply-demand balance and energy flow patterns

## 🛠️ Core Technologies

- **Python 3.12**: Core programming language
- **FastAPI**: High-performance ASGI web framework for API endpoints
- **LangGraph**: Stateful multi-agent orchestration and decision-making
- **Pydantic**: Data modeling and validation
- **Docker**: Containerized deployment
- **Beckn Protocol**: Decentralized transaction protocol
- **A2A Protocol**: Agent-to-agent communication

## 📁 Project Structure

```
gemini-p2p/
├── src/
│   ├── agents/             # Agent logic and LangGraph workflows
│   │   ├── household/      # Household agent implementation
│   │   ├── utility/        # Utility agent implementation
│   │   └── agent_graph.py  # Shared LangGraph nodes and state
│   ├── protocols/          # Beckn protocol implementation
│   │   └── beckn/
│   │       └── mock_gateway.py
│   ├── reporting/          # Data collection and reporting
│   │   └── reporter.py
│   └── shared/             # Shared models and configuration
│       ├── config.py
│       └── models.py
├── static/                 # Agent configuration files
├── reports/                # Generated simulation reports
├── docker-compose.yml      # Multi-service orchestration
├── Dockerfile             # Container configuration
└── pyproject.toml         # Project metadata and dependencies
```

## 🧪 Testing

### Test the Setup

```bash
# Run the test script
python test_docker_setup.py

# Check individual services
curl http://localhost:9000/registry
curl http://localhost:8001/profile
curl http://localhost:8002/profile
```

### Monitor the Simulation

```bash
# View logs from specific services
docker-compose logs -f household_agent_1
docker-compose logs -f utility_agent
docker-compose logs -f gateway

# Check reports
ls -la reports/
cat reports/report_*.json | jq .
```

## 📈 API Endpoints

### Gateway Endpoints
- `GET /registry` - List all registered agents
- `POST /register` - Register an agent
- `POST /search` - Broadcast search request

### Agent Endpoints
Each agent provides:
- `GET /profile` - Get current agent state
- `POST /a2a` - Handle A2A protocol tasks
- `POST /{action}` - Handle Beckn protocol actions

### Utility Agent Admin
- `POST /admin/request-data` - Trigger data collection
- `GET /admin/collected-data` - View collected data

## 🔧 Development

### Local Development

```bash
# Install dependencies
uv venv
source .venv/bin/activate
uv pip install -e .

# Run individual services
uvicorn src.protocols.beckn.mock_gateway:app --port 9000
uvicorn src.agents.household.main:app --port 8001
uvicorn src.agents.utility.main:app --port 8002
```

### Customization

Edit environment variables in `docker-compose.yml`:
```yaml
environment:
  - INITIAL_SOC=50  # Change initial state of charge
  - AGENT_ID=custom-agent-id
```

## 🚀 Key Features

- **✅ Complete Beckn Protocol Implementation**
- **✅ Dynamic Energy Market with Price Competition**
- **✅ Automatic Data Collection via A2A Protocol**
- **✅ Real-time Reporting and Monitoring**
- **✅ Scalable Multi-Agent Architecture**
- **✅ Docker-based Deployment**
- **✅ Comprehensive Documentation**

## 📚 Documentation

- [DOCKER_README.md](DOCKER_README.md) - Docker setup and deployment
- [ENDPOINTS.md](ENDPOINTS.md) - API endpoint documentation
- [WORKFLOW.md](WORKFLOW.md) - Transaction workflow examples
- [COMPREHENSIVE_GUIDE.md](COMPREHENSIVE_GUIDE.md) - Complete system overview

## 🎯 Requirements Fulfillment

### ✅ Requirement 1: P2P Energy Trading with Beckn Protocol
- **10 Household Agents** + **1 Utility Agent** actively trading
- **Full Beckn Protocol** implementation (search → select → init → confirm → status)
- **Price Competition** with automatic cheapest offer selection
- **Dynamic Energy Model** driving continuous transactions

### ✅ Requirement 2: Utility Agent Data Collection
- **Automatic Data Collection** every 5 minutes
- **Agent Discovery** via Beckn Gateway registry
- **A2A Protocol** for direct agent communication
- **Data Storage** and reporting system

The system provides a **rock-solid foundation** for building advanced P2P energy grid applications! 🚀