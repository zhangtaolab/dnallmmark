#!/bin/bash

# DNALLM Mark - Local Server Launcher
# This script starts a local HTTP server for the project

cd "$(dirname "$0")/dnallm-mark"

echo "Starting DNALLM Mark server..."
echo "Server URL: http://localhost:8080"
echo "Press Ctrl+C to stop the server"
echo ""

# Try Python 3 first
if command -v python3 &> /dev/null; then
    python3 -m http.server 8080
# Try Python if python3 is not available
elif command -v python &> /dev/null; then
    python -m http.server 8080
# Try Node.js http-server
elif command -v npx &> /dev/null; then
    npx http-server -p 8080
else
    echo "Error: Neither Python 3 nor Node.js found."
    echo "Please install Python 3 or Node.js to run this server."
    exit 1
fi
