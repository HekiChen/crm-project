#!/bin/bash

# Start Server Script
# This script ensures uvicorn runs from the correct directory

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the backend directory
cd "$SCRIPT_DIR" || exit 1

echo "🚀 Starting CRM Backend Server..."
echo "📁 Working directory: $SCRIPT_DIR"
echo ""

# Check if port 8000 is already in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port 8000 is already in use!"
    echo ""
    read -p "Kill existing process and restart? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Killing process on port 8000..."
        kill -9 $(lsof -ti:8000) 2>/dev/null
        sleep 1
        echo "✅ Process killed"
    else
        echo "❌ Aborted. Use a different port with: uvicorn app.main:app --reload --port 8001"
        exit 1
    fi
fi

# Check if conda environment exists
if ! conda env list | grep -q "crm-backend"; then
    echo "⚠️  Conda environment 'crm-backend' not found!"
    echo "Creating environment from environment.yml..."
    conda env create -f environment.yml
fi

# Activate conda environment
echo "Activating conda environment: crm-backend"
eval "$(conda shell.bash hook)"
conda activate crm-backend

# Verify we're in the right directory
if [ ! -f "app/main.py" ]; then
    echo "❌ Error: app/main.py not found!"
    echo "Current directory: $(pwd)"
    exit 1
fi

echo ""
echo "✅ Starting uvicorn..."
echo "🌐 Server will be available at: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🏥 Health Check: http://localhost:8000/api/v1/health"
echo ""
echo "Press CTRL+C to stop the server"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Start uvicorn
uvicorn app.main:app --reload
