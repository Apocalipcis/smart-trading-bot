#!/bin/bash

# Trading Bot Development Script
# This script starts both the backend API and frontend for development

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_PORT=8000
FRONTEND_PORT=3000

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
    
    if ! command_exists python; then
        print_error "Python is not installed. Please install Python 3.8+ first."
        exit 1
    fi
    
    if ! command_exists node; then
        print_error "Node.js is not installed. Please install Node.js 18+ first."
        exit 1
    fi
    
    if ! command_exists npm; then
        print_error "npm is not installed. Please install npm first."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to setup Python virtual environment
setup_python_env() {
    print_status "Setting up Python virtual environment..."
    
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        python -m venv venv
    fi
    
    print_status "Activating virtual environment..."
    # Handle Windows vs Unix paths
    if [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
    elif [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        print_error "Virtual environment activate script not found"
        exit 1
    fi
    
    print_status "Installing Python dependencies..."
    pip install -e .
    
    print_success "Python environment setup complete"
}

# Function to setup Node.js dependencies
setup_node_env() {
    print_status "Setting up Node.js dependencies..."
    
    cd web
    
    if [ ! -d "node_modules" ]; then
        print_status "Installing npm dependencies..."
        npm install
    fi
    
    cd ..
    
    print_success "Node.js environment setup complete"
}

# Function to start backend
start_backend() {
    print_status "Starting backend API server..."
    
    # Activate virtual environment
    # Handle Windows vs Unix paths
    if [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
    elif [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        print_error "Virtual environment activate script not found"
        exit 1
    fi
    
    # Set environment variables for development
    export LOG_LEVEL=DEBUG
    export DEBUG_MODE=true
    export RELOAD=true
    export TRADING_ENABLED=false
    export ORDER_CONFIRMATION_REQUIRED=true
    
    # Start the backend server
    uvicorn src.api.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload &
    BACKEND_PID=$!
    
    print_success "Backend started on http://localhost:$BACKEND_PORT"
    print_status "Backend PID: $BACKEND_PID"
}

# Function to start frontend
start_frontend() {
    print_status "Starting frontend development server..."
    
    cd web
    
    # Start the frontend development server
    npm run dev &
    FRONTEND_PID=$!
    
    cd ..
    
    print_success "Frontend started on http://localhost:$FRONTEND_PORT"
    print_status "Frontend PID: $FRONTEND_PID"
}

# Function to wait for services to be ready
wait_for_services() {
    print_status "Waiting for services to be ready..."
    
    # Wait for backend
    print_status "Waiting for backend API..."
    for i in {1..30}; do
        if curl -s http://localhost:$BACKEND_PORT/api/v1/status/health > /dev/null 2>&1; then
            print_success "Backend API is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "Backend API failed to start within 30 seconds"
            exit 1
        fi
        sleep 1
    done
    
    # Wait for frontend
    print_status "Waiting for frontend..."
    for i in {1..30}; do
        if curl -s http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
            print_success "Frontend is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "Frontend failed to start within 30 seconds"
            exit 1
        fi
        sleep 1
    done
}

# Function to cleanup on exit
cleanup() {
    print_status "Shutting down services..."
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        print_status "Backend stopped"
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        print_status "Frontend stopped"
    fi
    
    print_success "Development environment stopped"
}

# Set trap to cleanup on script exit
trap cleanup EXIT

# Main execution
main() {
    print_status "Starting Trading Bot Development Environment"
    print_status "============================================="
    
    check_prerequisites
    setup_python_env
    setup_node_env
    
    print_status "Starting services..."
    start_backend
    start_frontend
    
    wait_for_services
    
    print_success "Development environment is ready!"
    print_status "Backend API: http://localhost:$BACKEND_PORT"
    print_status "Frontend UI: http://localhost:$FRONTEND_PORT"
    print_status "API Documentation: http://localhost:$BACKEND_PORT/docs"
    print_status ""
    print_status "Press Ctrl+C to stop all services"
    
    # Wait for user to stop
    wait
}

# Run main function
main "$@"
