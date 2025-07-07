import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

import uvicorn
from src.solar_agent.api.app import app

if __name__ == "__main__":
    uvicorn.run("src.solar_agent.api.app:app", host="0.0.0.0", port=8000, reload=True) 