#!/usr/bin/env python3
"""
Test script for the Docker setup
"""
import asyncio
import httpx
import time

async def test_gateway():
    """Test if the gateway is accessible."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:9000/registry", timeout=5.0)
            print(f"✅ Gateway accessible: {response.status_code}")
            return True
    except Exception as e:
        print(f"❌ Gateway not accessible: {e}")
        return False

async def test_household_agent(agent_id, port):
    """Test if a household agent is accessible."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://localhost:{port}/profile", timeout=5.0)
            print(f"✅ {agent_id} accessible on port {port}: {response.status_code}")
            return True
    except Exception as e:
        print(f"❌ {agent_id} not accessible on port {port}: {e}")
        return False

async def test_utility_agent():
    """Test if the utility agent is accessible."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8002/profile", timeout=5.0)
            print(f"✅ Utility agent accessible: {response.status_code}")
            return True
    except Exception as e:
        print(f"❌ Utility agent not accessible: {e}")
        return False

async def main():
    """Test all services."""
    print("🧪 Testing Docker Setup")
    print("=" * 40)
    
    # Test gateway
    gateway_ok = await test_gateway()
    
    # Test household agents
    household_agents = [
        ("household-agent-01", 8001),
        ("household-agent-02", 8003),
        ("household-agent-03", 8005),
        ("household-agent-04", 8007),
        ("household-agent-05", 8009),
        ("household-agent-06", 8011),
        ("household-agent-07", 8013),
        ("household-agent-08", 8015),
        ("household-agent-09", 8017),
        ("household-agent-10", 8019),
    ]
    
    household_results = []
    for agent_id, port in household_agents:
        result = await test_household_agent(agent_id, port)
        household_results.append(result)
        await asyncio.sleep(0.5)  # Small delay between tests
    
    # Test utility agent
    utility_ok = await test_utility_agent()
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 Test Results:")
    print(f"Gateway: {'✅' if gateway_ok else '❌'}")
    print(f"Utility Agent: {'✅' if utility_ok else '❌'}")
    print(f"Household Agents: {sum(household_results)}/10 ✅")
    
    if gateway_ok and utility_ok and sum(household_results) >= 8:
        print("\n🎉 Docker setup is working correctly!")
        return True
    else:
        print("\n⚠️  Some services are not accessible. Check Docker logs.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1) 