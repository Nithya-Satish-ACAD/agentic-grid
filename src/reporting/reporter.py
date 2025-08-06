# src/reporting/reporter.py
import asyncio
import httpx
import json
from datetime import datetime
import os

AGENT_COUNT = 10
REPORTS_DIR = "/app/reports" # Inside Docker

async def collect_data():
    """Collects profile data from all running agents."""
    agent_data = []
    urls = [f"http://utility_agent:8002/profile"]
    for i in range(1, AGENT_COUNT + 1):
        port = 8001 if i == 1 else 8001 + (i-1) * 2
        urls.append(f"http://household_agent_{i}:{port}/profile")

    async with httpx.AsyncClient() as client:
        tasks = [client.get(url, timeout=5.0) for url in urls]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

    for i, res in enumerate(responses):
        if isinstance(res, httpx.Response):
            agent_data.append(res.json())
        else:
            print(f"Failed to collect data from {urls[i]}: {res}")
    return agent_data

async def main():
    """Main loop to generate reports periodically."""
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)
        
    while True:
        print("REPORTER: Collecting data for new report...")
        all_agent_data = await collect_data()
        
        timestamp = datetime.now().isoformat()
        report = {
            "timestamp": timestamp,
            "agents": all_agent_data
        }
        
        report_path = os.path.join(REPORTS_DIR, f"report_{timestamp}.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
            
        print(f"REPORTER: Report saved to {report_path}")
        await asyncio.sleep(120) # Wait for 2 minutes

if __name__ == "__main__":
    asyncio.run(main()) 