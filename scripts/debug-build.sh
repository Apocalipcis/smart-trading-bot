#!/bin/bash

# Debug Build Script for Smart Trading Bot
# This script provides detailed logging during Docker build

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="smart-trading-bot"
DOCKER_IMAGE="${PROJECT_NAME}:debug"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
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

print_status "Starting debug build with detailed logging..."

# Check if Dockerfile.debug exists
if [ ! -f "Dockerfile.debug" ]; then
    print_error "Dockerfile.debug not found!"
    exit 1
fi

print_status "Building with debug Dockerfile..."
print_status "This will show detailed progress for each step"

# Build with maximum verbosity
docker build \
    -f Dockerfile.debug \
    -t "${DOCKER_IMAGE}" \
    --progress=plain \
    --no-cache \
    --build-arg BUILDKIT_INLINE_CACHE=0 \
    .

if [ $? -eq 0 ]; then
    print_success "Debug build completed successfully!"
    print_status "Image tagged as: ${DOCKER_IMAGE}"
    
    # Show image info
    print_status "Image details:"
    docker images "${DOCKER_IMAGE}"
    
    # Show image layers
    print_status "Image layers:"
    docker history "${DOCKER_IMAGE}"
    
else
    print_error "Debug build failed!"
    exit 1
fi

print_status "Debug build script completed"
