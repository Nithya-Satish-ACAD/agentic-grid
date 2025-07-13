import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fastapi.testclient import TestClient
from utility_agent.api.app import app
from utility_agent.api.models import RegisterDERRequest, CurtailmentRequest

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_register_der():
    payload = {"id": "test_der", "type": "solar", "ip_address": "127.0.0.1"}
    response = client.post("/api/register_der", json=payload)
    assert response.status_code == 200
    assert "DER registered" in response.json()["status"]

def test_curtailment():
    payload = {"agent_id": "test_der", "amount": 10.0, "duration": 30}
    response = client.post("/api/curtailment", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "curtailment issued"}

def test_beckn_stub():
    payload = {"context": {"domain": "energy", "action": "on_search"}, "message": {}}
    response = client.post("/api/beckn/on_search", json=payload)
    assert response.status_code == 200
    assert response.json()["ack"] == True
