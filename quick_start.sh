#!/bin/bash
# Quick Start Script for NRP K8s System (Linux/macOS)

echo "==============================================="
echo "NRP K8s System - Quick Start (Linux/macOS)"
echo "==============================================="

echo
echo "Checking Python..."
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "[ERROR] Python not found! Please install Python 3.8+"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

echo "[OK] Python is available"
echo

echo "Setting up the system..."
$PYTHON_CMD setup.py
if [ $? -ne 0 ]; then
    echo "[ERROR] Setup failed!"
    exit 1
fi

echo
echo "==============================================="
echo "Setup completed! Choose an option:"
echo "==============================================="
echo "1. Start Web Server (Browser interface)"
echo "2. Start MCP Server (API interface)"
echo "3. Start both servers (in background)"
echo "4. Exit"
echo

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo "Starting Web Server..."
        $PYTHON_CMD start_web_server.py
        ;;
    2)
        echo "Starting MCP Server..."
        $PYTHON_CMD start_mcp_server.py
        ;;
    3)
        echo "Starting both servers..."
        $PYTHON_CMD start_web_server.py &
        WEB_PID=$!
        $PYTHON_CMD start_mcp_server.py &
        MCP_PID=$!

        echo "Both servers started!"
        echo "Web interface: http://localhost:5000"
        echo "MCP endpoint: http://localhost:8020/mcp"
        echo "Web Server PID: $WEB_PID"
        echo "MCP Server PID: $MCP_PID"
        echo
        echo "Press Ctrl+C to stop both servers..."

        trap 'kill $WEB_PID $MCP_PID; exit' INT
        wait $WEB_PID $MCP_PID
        ;;
    4)
        echo "Goodbye!"
        exit 0
        ;;
    *)
        echo "Invalid choice!"
        exit 1
        ;;
esac