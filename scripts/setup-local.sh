#!/bin/bash

# Setup script for local ComfyUI development environment

echo "Setting up local ComfyUI development environment..."

# Create necessary directories
mkdir -p local-data/output
mkdir -p local-data/input
mkdir -p local-data/models

echo "Directories created:"
echo "  - local-data/output (for generated images)"
echo "  - local-data/input (for test images)"
echo "  - local-data/models (for additional models)"

echo ""
echo "Starting ComfyUI local development environment..."
echo "This will build the base image and start ComfyUI on http://localhost:8188"
echo ""

# Build and start the container
docker-compose -f docker-compose.local.yml up --build

echo ""
echo "ComfyUI is now running at http://localhost:8188"
echo "You can import your workflow and see what nodes are missing!"
echo ""
echo "To stop the container, run: docker-compose -f docker-compose.local.yml down" 