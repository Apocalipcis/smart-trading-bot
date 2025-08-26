#!/bin/bash

# Trading Bot Deployment Script
# This script handles building, testing, and deploying the trading bot

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="smart-trading-bot"
DOCKER_IMAGE="${PROJECT_NAME}:latest"
DATA_DIR="./data"
LOG_DIR="./logs"

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command_exists docker-compose; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p "${DATA_DIR}"
    mkdir -p "${LOG_DIR}"
    
    print_success "Directories created"
}

# Function to build Docker image
build_image() {
    print_status "Building Docker image..."
    
    docker build -t "${DOCKER_IMAGE}" .
    
    if [ $? -eq 0 ]; then
        print_success "Docker image built successfully"
    else
        print_error "Failed to build Docker image"
        exit 1
    fi
}

# Function to run tests
run_tests() {
    print_status "Running tests..."
    
    # Run tests in Docker container
    docker run --rm \
        -v "$(pwd)/tests:/app/tests" \
        -v "$(pwd)/src:/app/src" \
        "${DOCKER_IMAGE}" \
        python -m pytest tests/ -v --tb=short
    
    if [ $? -eq 0 ]; then
        print_success "Tests passed"
    else
        print_error "Tests failed"
        exit 1
    fi
}

# Function to start services
start_services() {
    print_status "Starting services..."
    
    # Stop existing services if running
    docker-compose down 2>/dev/null || true
    
    # Start services
    docker-compose up -d
    
    if [ $? -eq 0 ]; then
        print_success "Services started successfully"
    else
        print_error "Failed to start services"
        exit 1
    fi
}

# Function to check service health
check_health() {
    print_status "Checking service health..."
    
    # Wait for service to be ready
    sleep 10
    
    # Check health endpoint
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/status/health || echo "000")
    
    if [ "$response" = "200" ]; then
        print_success "Service is healthy"
    else
        print_error "Service health check failed (HTTP $response)"
        exit 1
    fi
}

# Function to show service status
show_status() {
    print_status "Service status:"
    echo "  - API: http://localhost:8000"
    echo "  - Documentation: http://localhost:8000/docs"
    echo "  - Health check: http://localhost:8000/api/v1/status/health"
    echo ""
    print_status "Docker containers:"
    docker-compose ps
}

# Function to stop services
stop_services() {
    print_status "Stopping services..."
    
    docker-compose down
    
    print_success "Services stopped"
}

# Function to show logs
show_logs() {
    print_status "Showing service logs..."
    
    docker-compose logs -f
}

# Function to clean up
cleanup() {
    print_status "Cleaning up..."
    
    docker-compose down
    docker system prune -f
    
    print_success "Cleanup completed"
}

# Main deployment function
deploy() {
    print_status "Starting deployment..."
    
    check_prerequisites
    create_directories
    build_image
    run_tests
    start_services
    check_health
    show_status
    
    print_success "Deployment completed successfully!"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  deploy      - Full deployment (build, test, start)"
    echo "  build       - Build Docker image only"
    echo "  test        - Run tests only"
    echo "  start       - Start services"
    echo "  stop        - Stop services"
    echo "  restart     - Restart services"
    echo "  status      - Show service status"
    echo "  logs        - Show service logs"
    echo "  health      - Check service health"
    echo "  cleanup     - Clean up Docker resources"
    echo "  help        - Show this help message"
    echo ""
}

# Main script logic
case "${1:-deploy}" in
    "deploy")
        deploy
        ;;
    "build")
        check_prerequisites
        build_image
        ;;
    "test")
        check_prerequisites
        build_image
        run_tests
        ;;
    "start")
        check_prerequisites
        start_services
        check_health
        show_status
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        stop_services
        start_services
        check_health
        show_status
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs
        ;;
    "health")
        check_health
        ;;
    "cleanup")
        cleanup
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    *)
        print_error "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac
