FROM python:3.12-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY static/ ./static/
COPY pyproject.toml .

# Install the package in development mode
RUN pip install -e .

# Create reports directory
RUN mkdir -p /app/reports

# Set Python path to include src directory
ENV PYTHONPATH=/app/src

# Expose ports
EXPOSE 8001 8002 8003 8005 8007 8009 8011 8013 8015 8017 8019 9000

# Default command (can be overridden)
CMD ["python", "src/agents/household/main.py"] 