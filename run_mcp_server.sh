#!/bin/bash

echo "========================================"
echo "OpenAutomate MCP Server - Production"
echo "========================================"
echo

# Set production environment variables
export OPENAUTOMATE_API_BASE_URL=https://api.openautomate.io
echo "Using production API URL: $OPENAUTOMATE_API_BASE_URL"
echo

# Change to the MCP directory (script's directory)
cd "$(dirname "$0")"
echo "Current directory: $(pwd)"
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "ERROR: Python is not installed or not in PATH"
        echo "Please install Python 3.8+ and add it to your PATH"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

echo "Python version:"
$PYTHON_CMD --version
echo

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    if ! command -v pip &> /dev/null; then
        echo "ERROR: pip is not installed or not in PATH"
        echo "Please install pip for Python package management"
        exit 1
    else
        PIP_CMD="pip"
    fi
else
    PIP_CMD="pip3"
fi

# Install/update requirements
echo "Installing Python dependencies..."
$PIP_CMD install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install requirements"
    echo "Please check your internet connection and try again"
    exit 1
fi
echo
echo "Dependencies installed successfully!"
echo

# Start the MCP server
echo "Starting MCP Server in Production Mode..."
echo "Press Ctrl+C to stop the server"
echo
$PYTHON_CMD start_server.py

# If we get here, the server stopped
echo
echo "MCP Server stopped."
