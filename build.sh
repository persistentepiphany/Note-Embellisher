#!/bin/bash
# Build script for Render deployment

# Navigate to backend directory
cd backend

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies with verbose output
pip install -r requirements.txt --verbose

echo "Build completed successfully!"