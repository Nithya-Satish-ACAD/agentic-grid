# src/protocols/beckn/mock_gateway.py
import httpx
import asyncio
from fastapi import FastAPI, Request, BackgroundTasks

bpp_registry: list[str] = []
app = FastAPI(title="Mock Beckn Gateway")

async def forward_request(bpp_uri: str, payload: dict):
    """Asynchronously forwards a search request to a single BPP."""
    try:
        async with httpx.AsyncClient() as client:
            forward_url = f"{bpp_uri}/search"
            print(f"Gateway forwarding search to {forward_url}")
            await client.post(forward_url, json=payload, timeout=10.0)
    except httpx.RequestError as e:
        print(f"Gateway failed to forward search to {bpp_uri}: {e}")

@app.post("/register")
async def register_bpp(request: Request):
    payload = await request.json()
    bpp_uri = payload.get("bpp_uri")
    if bpp_uri and bpp_uri not in bpp_registry:
        bpp_registry.append(bpp_uri)
    print(f"Registered BPPs: {bpp_registry}")
    return {"status": "success"}

@app.post("/search")
async def broadcast_search(request: Request, background_tasks: BackgroundTasks):
    """
    Receives a search, immediately returns ACK, and forwards 
    to all BPPs in the background to prevent deadlock.
    """
    search_payload = await request.json()
    print(f"Gateway received search request: {search_payload['context']['transaction_id']}")
    
    for uri in bpp_registry:
        background_tasks.add_task(forward_request, uri, search_payload)

    return {"message": {"ack": {"status": "ACK"}}}