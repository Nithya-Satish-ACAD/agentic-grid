#!/usr/bin/env python3
"""
Simple demo to test Solar Agent FastAPI functionality.
"""

import asyncio
import sys
import json
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastapi import FastAPI
from solar_agent.core.config import Settings
from solar_agent.core.models import SolarData, AgentStatus
from solar_agent.adapters import MockAdapter


def create_demo_app() -> FastAPI:
    """Create a simple demo FastAPI app."""
    app = FastAPI(
        title="Solar Agent Demo",
        description="Demo of Solar Agent core functionality",
        version="0.1.0"
    )
    
    # Initialize components
    settings = Settings()
    adapter_config = {
        "capacity_kw": settings.capacity_kw,
        "fault_probability": 0.001
    }
    adapter = MockAdapter(config=adapter_config)
    
    @app.on_event("startup")
    async def startup():
        await adapter.connect()
        print(f"✅ Solar Agent Demo started!")
        print(f"   • Agent ID: {settings.agent_id}")
        print(f"   • Capacity: {settings.capacity_kw}kW")
        print(f"   • Mock adapter connected")
    
    @app.on_event("shutdown")
    async def shutdown():
        await adapter.disconnect()
        print("👋 Solar Agent Demo stopped")
    
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "name": "Solar Agent Demo",
            "version": "0.1.0",
            "status": "running",
            "agent_id": settings.agent_id,
            "capacity_kw": settings.capacity_kw
        }
    
    @app.get("/solar-data")
    async def get_solar_data():
        """Get current solar data."""
        data = await adapter.read_solar_data()
        return {
            "timestamp": data.timestamp.isoformat(),
            "current_output_kw": data.current_output_kw,
            "voltage_v": data.voltage_v,
            "current_a": data.current_a,
            "efficiency": data.efficiency,
            "temperature_c": data.temperature_c,
            "irradiance_w_m2": data.irradiance_w_m2
        }
    
    @app.get("/status")
    async def get_status():
        """Get agent status."""
        data = await adapter.read_solar_data()
        is_online = await adapter.is_online()
        faults = await adapter.get_fault_status()
        
        return {
            "agent_id": settings.agent_id,
            "timestamp": data.timestamp.isoformat(),
            "is_online": is_online,
            "current_output_kw": data.current_output_kw,
            "capacity_kw": settings.capacity_kw,
            "utilization_percent": (data.current_output_kw / settings.capacity_kw) * 100,
            "faults_count": len(faults),
            "efficiency": data.efficiency,
            "temperature_c": data.temperature_c
        }
    
    @app.post("/curtailment")
    async def apply_curtailment(target_output_kw: float):
        """Apply curtailment command."""
        try:
            await adapter.set_output_limit(target_output_kw)
            return {
                "success": True,
                "message": f"Curtailment applied: {target_output_kw}kW",
                "target_output_kw": target_output_kw
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Curtailment failed: {str(e)}",
                "target_output_kw": target_output_kw
            }
    
    @app.get("/device-info")
    async def get_device_info():
        """Get device information."""
        return await adapter.get_device_info()
    
    return app


def main():
    """Run the demo."""
    print("🚀 Starting Solar Agent Demo...")
    
    # Create the app
    app = create_demo_app()
    
    print("\n🌟 Demo endpoints available:")
    print("   • GET  /           - Root endpoint with basic info")
    print("   • GET  /solar-data - Current solar panel readings")
    print("   • GET  /status     - Comprehensive agent status")
    print("   • POST /curtailment?target_output_kw=50 - Apply curtailment")
    print("   • GET  /device-info - Hardware device information")
    print("\n📖 Open http://localhost:8000/docs for interactive API docs")
    print("\n💡 Example requests:")
    print("   curl http://localhost:8000/solar-data")
    print("   curl -X POST 'http://localhost:8000/curtailment?target_output_kw=25'")
    
    # Start the server
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    main() 