#!/bin/bash

# Trading Bot Frontend Development Script
# This script starts only the frontend for development

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
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

# Function to start frontend
start_frontend() {
    print_status "Starting frontend..."
    
    cd web
    
    # Start the frontend development server
    npm run dev &
    FRONTEND_PID=$!
    
    cd ..
    
    print_success "Frontend started on http://localhost:$FRONTEND_PORT"
    print_status "Frontend PID: $FRONTEND_PID"
}

# Function to wait for frontend to be ready
wait_for_frontend() {
    print_status "Waiting for frontend to be ready..."
    
    for i in {1..30}; do
        if curl -s http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
            print_success "Frontend is ready!"
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
    print_status "Shutting down frontend..."
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        print_status "Frontend stopped"
    fi
    
    print_success "Frontend development environment stopped"
}

# Set trap to cleanup on script exit
trap cleanup EXIT

# Main execution
main() {
    print_status "Starting Trading Bot Frontend Development Environment"
    print_status "=================================================="
    
    # Ensure we're in the project root
    if [ ! -f "pyproject.toml" ]; then
        print_error "Please run this script from the project root directory"
        exit 1
    fi
    
    check_prerequisites
    setup_node_env
    
    print_status "Starting frontend service..."
    start_frontend
    
    wait_for_frontend
    
    print_success "Frontend development environment is ready!"
    print_status "Frontend UI: http://localhost:$FRONTEND_PORT"
    print_status ""
    print_status "Press Ctrl+C to stop the frontend service"
    
    # Wait for user to stop
    wait
}

# Run main function
main "$@"
