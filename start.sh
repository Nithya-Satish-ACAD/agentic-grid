#!/bin/bash

# Solar Agent Startup Script
# This script provides easy commands for running the Solar Agent system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help function
show_help() {
    echo "Solar Agent Management Script"
    echo
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  dev         Start development server with mock adapter"
    echo "  test        Run comprehensive test suite"
    echo "  build       Build Docker image"
    echo "  docker      Start with Docker Compose"
    echo "  docker-prod Start production stack with Docker"
    echo "  monitoring  Start with monitoring stack"
    echo "  setup       Initial setup and environment configuration"
    echo "  clean       Clean up logs and temporary files"
    echo "  help        Show this help message"
    echo
}

# Setup function
setup() {
    print_status "Setting up Solar Agent environment..."
    
    # Create directories
    mkdir -p logs data config
    
    # Create environment file if it doesn't exist
    if [ ! -f .env ]; then
        print_status "Creating .env from template..."
        cp env.template .env
        print_warning "Please edit .env file with your configuration"
    fi
    
    # Install Python dependencies
    if [ -f requirements.txt ]; then
        print_status "Installing Python dependencies..."
        pip install -r requirements.txt
    fi
    
    print_success "Setup complete!"
}

# Development server
dev() {
    print_status "Starting Solar Agent in development mode..."
    
    # Set environment variables for development
    export SOLAR_USE_MOCK_ADAPTER=true
    export SOLAR_LOG_LEVEL=DEBUG
    export SOLAR_ENABLE_PERSISTENCE=false
    export PYTHONPATH="${PWD}/src:${PYTHONPATH}"
    
    # Run the application
    python main.py
}

# Test function
test() {
    print_status "Running Solar Agent test suite..."
    
    # Set test environment
    export PYTHONPATH="${PWD}/src:${PYTHONPATH}"
    export SOLAR_USE_MOCK_ADAPTER=true
    export SOLAR_LOG_LEVEL=WARNING
    
    # Run custom test runner
    python run_tests.py
    
    # Also run pytest if available
    if command -v pytest &> /dev/null; then
        print_status "Running additional pytest suite..."
        pytest tests/ -v || print_warning "pytest tests failed or no tests directory found"
    fi
}

# Docker build
build() {
    print_status "Building Solar Agent Docker image..."
    docker build -t solar-agent:latest .
    print_success "Docker image built successfully!"
}

# Docker compose
docker_run() {
    print_status "Starting Solar Agent with Docker Compose..."
    
    # Create required directories
    mkdir -p logs data config
    
    # Start basic stack
    docker-compose up -d
    
    print_success "Solar Agent started!"
    print_status "API available at http://localhost:8000"
    print_status "View logs: docker-compose logs -f solar-agent"
}

# Production Docker
docker_prod() {
    print_status "Starting Solar Agent production stack..."
    
    # Create required directories
    mkdir -p logs data config
    
    # Start production stack
    docker-compose --profile production up -d
    
    print_success "Production stack started!"
    print_status "API: http://localhost:8000"
    print_status "Database: PostgreSQL on port 5432"
    print_status "Redis: port 6379"
}

# Monitoring stack
monitoring() {
    print_status "Starting Solar Agent with monitoring..."
    
    # Create monitoring directories
    mkdir -p logs data config monitoring
    
    # Start with monitoring profile
    docker-compose --profile monitoring --profile production up -d
    
    print_success "Monitoring stack started!"
    print_status "API: http://localhost:8000"
    print_status "Prometheus: http://localhost:9090"
    print_status "Grafana: http://localhost:3000 (admin/admin)"
}

# Clean function
clean() {
    print_status "Cleaning up Solar Agent files..."
    
    # Clean logs
    rm -rf logs/*
    print_status "Cleaned logs directory"
    
    # Clean data (be careful with this in production)
    if [ "$1" = "--all" ]; then
        print_warning "Cleaning all data including database..."
        rm -rf data/*
    fi
    
    # Clean Python cache
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    
    print_success "Cleanup complete!"
}

# Main script logic
case "${1:-help}" in
    dev)
        dev
        ;;
    test)
        test
        ;;
    build)
        build
        ;;
    docker)
        docker_run
        ;;
    docker-prod)
        docker_prod
        ;;
    monitoring)
        monitoring
        ;;
    setup)
        setup
        ;;
    clean)
        clean $2
        ;;
    help|*)
        show_help
        ;;
esac 