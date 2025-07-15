import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

import uvicorn
from solar_agent.api.app import app

if __name__ == "__main__":
    # The solar agent runs on port 8001 to avoid conflict with the utility agent on 8000
    uvicorn.run("solar_agent.api.app:app", host="0.0.0.0", port=8001, reload=True) 