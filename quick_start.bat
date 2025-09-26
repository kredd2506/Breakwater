@echo off
REM Quick Start Script for NRP K8s System (Windows)
echo ===============================================
echo NRP K8s System - Quick Start (Windows)
echo ===============================================

echo.
echo Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.8+
    pause
    exit /b 1
)

echo [OK] Python is available
echo.

echo Setting up the system...
python setup.py
if errorlevel 1 (
    echo [ERROR] Setup failed!
    pause
    exit /b 1
)

echo.
echo ===============================================
echo Setup completed! Choose an option:
echo ===============================================
echo 1. Start Web Server (Browser interface)
echo 2. Start MCP Server (API interface)
echo 3. Start both servers (in separate windows)
echo 4. Exit
echo.
set /p choice=Enter your choice (1-4):

if "%choice%"=="1" (
    echo Starting Web Server...
    python start_web_server.py
) else if "%choice%"=="2" (
    echo Starting MCP Server...
    python start_mcp_server.py
) else if "%choice%"=="3" (
    echo Starting both servers...
    start "NRP Web Server" cmd /c "python start_web_server.py && pause"
    start "NRP MCP Server" cmd /c "python start_mcp_server.py && pause"
    echo Both servers started in separate windows
    echo Web interface: http://localhost:5000
    echo MCP endpoint: http://localhost:8020/mcp
    pause
) else if "%choice%"=="4" (
    echo Goodbye!
    exit /b 0
) else (
    echo Invalid choice!
    pause
    exit /b 1
)

pause