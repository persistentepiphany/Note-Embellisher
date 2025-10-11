#!/bin/bash
# Build script for Render deployment

# Upgrade pip first
pip install --upgrade pip

# Install minimal Python dependencies
pip install -r requirements-render.txt

echo "Build completed successfully!"