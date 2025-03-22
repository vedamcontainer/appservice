#!/bin/bash

# Check if docker-compose is installed
if ! command -v docker-compose &>/dev/null; then
    echo "❌ ERROR: docker-compose is not installed. Please install it and try again."
    exit 1
fi

echo "✅ docker-compose is installed."

# Check if docker-compose.yml exists in the current directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ ERROR: docker-compose.yml not found in the current directory."
    exit 1
fi

echo "✅ Found docker-compose.yml, proceeding..."

# Stop and remove existing containers
echo "🛑 Stopping running containers..."
docker-compose down
if [ $? -ne 0 ]; then
    echo "❌ ERROR: Failed to stop running containers."
    exit 1
fi
echo "✅ Containers stopped successfully."

# Rebuild and start the containers
echo "🚀 Rebuilding and starting Docker containers..."
docker-compose up --build -d
if [ $? -ne 0 ]; then
    echo "❌ ERROR: docker-compose up --build failed."
    exit 1
fi
echo "✅ Containers rebuilt and started successfully."

# Show running containers
echo "🔍 Checking running containers..."
docker ps

echo "✅ Process completed successfully. Exiting..."
exit 0
