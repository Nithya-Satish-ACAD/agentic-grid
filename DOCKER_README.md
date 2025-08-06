# P2P Energy Grid Simulation - Docker Setup

This document explains how to run the P2P Energy Grid Simulation using Docker.

## Overview

The simulation consists of **13 services** running in Docker containers:

### Core Services
- **1 Gateway** (Beckn protocol gateway) - `gateway:9000`
- **1 Utility Agent** (grid operator) - `utility_agent:8002`
- **10 Household Agents** (with varied energy states) - `household_agent_1` through `household_agent_10`
- **1 Reporter Service** (generates reports every 2 minutes) - `reporter`

## Quick Start

### 1. Build and Start Services

```bash
# Build all services
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 2. Test the Setup

```bash
# Run the test script
python test_docker_setup.py
```

### 3. Monitor the Simulation

```bash
# View logs from specific services
docker-compose logs -f household_agent_1
docker-compose logs -f utility_agent
docker-compose logs -f gateway
docker-compose logs -f reporter
```

### 4. Access Reports

Reports are automatically generated every 2 minutes and saved to the `./reports/` directory.

```bash
# View the latest report
ls -la reports/
cat reports/report_*.json | jq .
```

## Service Configuration

### Household Agents

Each household agent has a different initial state of charge (SoC) and energy model:

| Agent | Port | Initial SoC | Role | Energy Model | Price |
|-------|------|-------------|------|--------------|-------|
| household-agent-01 | 8001 | 15% | Buyer | Consumes -0.03 kWh/cycle | $0.15/kWh |
| household-agent-02 | 8003 | 95% | Seller | Generates +0.02 kWh/cycle | $0.15/kWh |
| household-agent-03 | 8005 | 15% | Buyer | Consumes -0.03 kWh/cycle | $0.15/kWh |
| household-agent-04 | 8007 | 95% | Seller | Generates +0.02 kWh/cycle | $0.15/kWh |
| household-agent-05 | 8009 | 15% | Buyer | Consumes -0.03 kWh/cycle | $0.15/kWh |
| household-agent-06 | 8011 | 95% | Seller | Generates +0.02 kWh/cycle | $0.15/kWh |
| household-agent-07 | 8013 | 15% | Buyer | Consumes -0.03 kWh/cycle | $0.15/kWh |
| household-agent-08 | 8015 | 95% | Seller | Generates +0.02 kWh/cycle | $0.15/kWh |
| household-agent-09 | 8017 | 15% | Buyer | Consumes -0.03 kWh/cycle | $0.15/kWh |
| household-agent-10 | 8019 | 95% | Seller | Generates +0.02 kWh/cycle | $0.15/kWh |

### Utility Agent

- **Port**: 8002
- **Role**: Grid operator with unlimited capacity
- **Function**: Provides grid power and collects data from households
- **Price**: $0.25/kWh (higher than household agents)

### Gateway

- **Port**: 9000
- **Function**: Beckn protocol gateway for agent discovery and message routing
- **Registry**: Maintains list of all registered BPPs (sellers)

### Reporter

- **Function**: Collects data from all agents every 2 minutes
- **Output**: JSON reports saved to `./reports/` directory
- **Format**: Timestamped agent states with energy levels and transaction history

## 🔄 Beckn Protocol Flow

### 1. Agent Registration
All agents register with the Gateway on startup:
```python
await client.post(f"{settings.BECKN_GATEWAY_URL}/register", 
                 json={"bpp_uri": "http://agent_url:port"})
```

### 2. Energy Market Dynamics
Every 20 seconds, each agent's supervisor evaluates energy state:
- **Low Energy (< 30%)**: Act as BAP (Buyer) - initiate search
- **High Energy (> 70%)**: Act as BPP (Seller) - respond to searches
- **Stable Energy**: Stay idle

### 3. Transaction Flow
When a buyer needs energy:

1. **Search**: Buyer sends search request to Gateway
2. **Broadcast**: Gateway forwards to all registered sellers
3. **Offers**: Sellers respond with price offers
4. **Selection**: Buyer selects cheapest offer: `min(offers, key=lambda o: o.price_per_kwh)`
5. **Handshake**: Complete Beckn flow (init → confirm → completion)
6. **Transfer**: Energy transferred between agents

### 4. Price Competition
- **Household Agents**: $0.15/kWh (competitive)
- **Utility Agent**: $0.25/kWh (premium)
- **Automatic Selection**: Cheapest offer always wins

## API Endpoints

### Gateway Endpoints

- `GET /registry` - List all registered agents
- `POST /register` - Register an agent
- `POST /search` - Broadcast search request

### Agent Endpoints

Each agent (household and utility) provides:

- `GET /profile` - Get current agent state
- `POST /a2a` - Handle A2A protocol tasks
- `POST /{action}` - Handle Beckn protocol actions (search, select, init, confirm, etc.)

### Utility Agent Admin Endpoints

- `POST /admin/request-data` - Trigger data collection from all households
- `GET /admin/collected-data` - View collected A2A data

## Testing the Simulation

### 1. Check Agent Registration

```bash
curl http://localhost:9000/registry
```

### 2. Check Individual Agent States

```bash
# Check household agent 1
curl http://localhost:8001/profile

# Check utility agent
curl http://localhost:8002/profile
```

### 3. Trigger Data Collection

```bash
curl -X POST http://localhost:8002/admin/request-data
```

### 4. Monitor Transactions

Watch the logs to see transactions between agents:

```bash
docker-compose logs -f | grep "TRANSACTION"
docker-compose logs -f | grep "Best offer selected"
```

### 5. View Market Activity

```bash
# Check energy levels changing over time
cat reports/report_*.json | jq '.agents[] | {agent_id, current_energy_storage_kwh}'

# Monitor transaction logs
docker-compose logs -f | grep "Contract confirmed"
```

## Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 8001-8019 and 9000 are available
2. **Memory issues**: The simulation uses significant memory. Ensure Docker has at least 4GB RAM allocated
3. **Network issues**: Check if containers can communicate with each other
4. **Agent registration failures**: Check Gateway logs for registration issues

### Debug Commands

```bash
# Check container status
docker-compose ps

# View container logs
docker-compose logs [service_name]

# Restart specific service
docker-compose restart [service_name]

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Performance Monitoring

```bash
# Monitor resource usage
docker stats

# Check disk usage
docker system df

# View network connectivity
docker network ls
docker network inspect gemini-p2p_default
```

## Customization

### Modifying Agent Behavior

Edit the environment variables in `docker-compose.yml`:

```yaml
environment:
  - INITIAL_SOC=50  # Change initial state of charge
  - AGENT_ID=custom-agent-id
  - AGENT_PORT=8001
```

### Adding More Agents

1. Add new service to `docker-compose.yml`
2. Update `src/reporting/reporter.py` to include the new agent
3. Rebuild and restart

### Changing Report Frequency

Edit `src/reporting/reporter.py`:

```python
await asyncio.sleep(120)  # Change from 120 seconds to desired interval
```

### Modifying Energy Models

Edit `src/agents/household/main.py`:

```python
# Change energy consumption/generation rates
energy_change = -0.03  # For buyers
energy_change = 0.02   # For sellers
```

## Cleanup

```bash
# Stop all services
docker-compose down

# Remove all containers and volumes
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

## Development

For development, you can run individual services:

```bash
# Run only gateway and one household agent
docker-compose up gateway household_agent_1

# Run with live code reloading
docker-compose up --build
```

The source code is mounted as volumes, so changes are reflected immediately without rebuilding.

## 🎯 Key Features

- **✅ Complete Beckn Protocol Implementation**
- **✅ Dynamic Energy Market with Price Competition**
- **✅ Automatic Data Collection via A2A Protocol**
- **✅ Real-time Reporting and Monitoring**
- **✅ Scalable Multi-Agent Architecture**
- **✅ Docker-based Deployment**
- **✅ Comprehensive Error Handling**

The system provides a **production-ready foundation** for P2P energy grid applications! 🚀 