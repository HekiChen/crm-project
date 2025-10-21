#!/bin/bash

# Quick test script for local development environment
set -e

echo "🧪 Testing local CRM Backend development environment..."

# Check if conda environment exists
if ! conda env list | grep -q "crm-backend"; then
    echo "❌ Conda environment 'crm-backend' not found. Run ./setup-local-env.sh first."
    exit 1
fi

echo "✅ Conda environment found"

# Test imports
echo "🔍 Testing Python imports..."
conda run -n crm-backend python -c "
from app.main import app
from app.api.health import router
from app.core.config import settings
from app.core.database import get_db
print('✅ All imports successful')
"

# Test configuration loading
echo "🔍 Testing configuration..."
conda run -n crm-backend python -c "
from app.core.config import settings
print(f'✅ Config loaded: {settings.app_name} v{settings.app_version}')
print(f'✅ Environment: {settings.environment}')
print(f'✅ Debug mode: {settings.debug}')
"

# Test FastAPI app creation
echo "🔍 Testing FastAPI app creation..."
conda run -n crm-backend python -c "
from app.main import app
print(f'✅ FastAPI app created: {app.title}')
print(f'✅ API routes: {len(app.routes)} routes')
"

echo ""
echo "✅ Local development environment is working correctly!"
echo ""
echo "🚀 To start the development server:"
echo "   conda activate crm-backend"
echo "   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "📖 For more information, see backend/README.md"