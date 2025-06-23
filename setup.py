"""
Setup script for Solar Agent package.
"""

from setuptools import setup, find_packages

setup(
    name="solar-agent",
    version="0.1.0",
    description="Solar Agent - Modular microservice for solar power monitoring, forecasting, and anomaly detection",
    author="Solar Agent Team",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "langgraph>=0.0.40",
        "openai>=1.3.0",
        "httpx>=0.25.0",
        "pydantic>=2.5.0",
        "python-dotenv>=1.0.0",
        "prometheus-client>=0.19.0",
        "structlog>=23.2.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.11.0",
            "mypy>=1.7.0",
            "bandit>=1.7.5",
            "safety>=2.3.0",
        ],
    },
) 