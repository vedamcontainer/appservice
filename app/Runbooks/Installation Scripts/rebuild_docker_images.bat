@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

:: Check if Docker Compose is installed
docker-compose -v >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo ❌ ERROR: Docker Compose is not installed. Please install it and try again.
    EXIT /B 1
)

echo ✅ Docker Compose is installed.

:: Check if docker-compose.yml exists in the current directory
IF NOT EXIST "docker-compose.yml" (
    echo ❌ ERROR: docker-compose.yml not found in the current directory.
    EXIT /B 1
)

echo ✅ Found docker-compose.yml, proceeding...

:: Stop and remove existing containers
echo 🛑 Stopping running containers...
docker-compose down
IF %ERRORLEVEL% NEQ 0 (
    echo ❌ ERROR: Failed to stop running containers.
    EXIT /B 1
)
echo ✅ Containers stopped successfully.

:: Rebuild and start the containers
echo 🚀 Rebuilding and starting Docker containers...
docker-compose up --build -d
IF %ERRORLEVEL% NEQ 0 (
    echo ❌ ERROR: docker-compose up --build failed.
    EXIT /B 1
)
echo ✅ Containers rebuilt and started successfully.

:: Show running containers
echo 🔍 Checking running containers...
docker ps

echo ✅ Process completed successfully. Exiting...
EXIT /B 0
