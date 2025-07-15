import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    EVENT_BUS_URL = os.getenv("EVENT_BUS_URL", "nats://localhost:4222")
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # LLM settings
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
    
    # OpenRouter settings
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "moonshotai/kimi-k2:free")
    OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL")
    OPENROUTER_SITE_NAME = os.getenv("OPENROUTER_SITE_NAME")

    # Add more configurations as needed for future extensions
