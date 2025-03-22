@echo off
REM Navigate to the script directory
cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH.
    pause
    exit /b
)

REM Run the Python script
python rebuild_images.py

echo python file is successfully executed