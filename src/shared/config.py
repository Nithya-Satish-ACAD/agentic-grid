# src/shared/config.py
import os
from dotenv import load_dotenv

# Load .env from the project root
load_dotenv()

class Settings:
    """Loads and holds configuration settings for the application."""
    SOLAR_AGENT_BASE_URL: str = os.getenv("SOLAR_AGENT_BASE_URL", "http://localhost:8001")
    UTILITY_AGENT_BASE_URL: str = os.getenv("UTILITY_AGENT_BASE_URL", "http://localhost:8002")
    BECKN_GATEWAY_URL: str = os.getenv("BECKN_GATEWAY_URL", "http://localhost:9000")

settings = Settings()