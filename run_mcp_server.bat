@echo off
echo ========================================
echo OpenAutomate MCP Server - Production
echo ========================================
echo.

REM Set production environment variables
set OPENAUTOMATE_API_BASE_URL=https://api.openautomate.io
echo Using production API URL: %OPENAUTOMATE_API_BASE_URL%
echo.

REM Change to the MCP directory
cd /d "%~dp0"
echo Current directory: %CD%
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to your PATH
    pause
    exit /b 1
)

echo Python version:
python --version
echo.

REM Install/update requirements
echo Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install requirements
    echo Please check your internet connection and try again
    pause
    exit /b 1
)
echo.
echo Dependencies installed successfully!
echo.

REM Start the MCP server
echo Starting MCP Server in Production Mode...
echo Press Ctrl+C to stop the server
echo.
python start_server.py

REM If we get here, the server stopped
echo.
echo MCP Server stopped.
pause