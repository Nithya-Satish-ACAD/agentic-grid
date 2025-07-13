import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from utility_agent.api.app import app
from utility_agent.logging_config import setup_logging
setup_logging()

if __name__ == "__main__":
    uvicorn.run("utility_agent.api.app:app", host="0.0.0.0", port=8000, reload=True) 