import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    EVENT_BUS_URL = os.getenv("EVENT_BUS_URL", "nats://localhost:4222")
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    # Add more configurations as needed for future extensions
