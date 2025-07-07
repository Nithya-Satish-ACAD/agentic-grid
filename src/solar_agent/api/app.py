import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from fastapi import FastAPI
from .endpoints import router as solar_agent_router

app = FastAPI(title="Solar Agent")
app.include_router(solar_agent_router) 