@echo off
setlocal

REM Check if Python is installed by checking if the "python" command is available
python --version >nul 2>&1

REM If Python is installed, the exit code will be 0, otherwise, it will be non-zero
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed on this system.
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

REM If Python is installed, run the create.py script
echo Python is installed. Running 001_00config_ini_file_update script...
python "%~dp0001_00config_ini_file_update.py"

REM Check if the script executed successfully
if %ERRORLEVEL% NEQ 0 (
    echo Error: 001_00config_ini_file_update encountered an issue during execution.
    pause
    exit /b 1
)

echo Script completed successfully.
