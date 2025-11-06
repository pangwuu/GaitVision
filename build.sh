#!/usr/bin/env bash
# exit on error
set -o errexit

# Install and build the React frontend
echo "Building React frontend..."
cd GaitVision/client
npm install
npm run build
cd ../../ # Navigate back to the project root

# Install Python dependencies for the backend
echo "Installing Python dependencies..."
cd GaitVision/flask-server
pip install -r requirements.txt
