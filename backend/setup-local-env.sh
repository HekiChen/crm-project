#!/bin/bash

# Setup script for local conda environment for CRM Backend
set -e

echo "🚀 Setting up local conda environment for CRM Backend..."

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    echo "❌ Conda is not installed. Please install Conda or Miniconda first."
    echo "   Download from: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

# Change to backend directory
cd "$(dirname "$0")"

# Check if environment.yml exists
if [ ! -f "environment.yml" ]; then
    echo "❌ environment.yml not found. Please run this script from the backend directory."
    exit 1
fi

# Create conda environment
echo "📦 Creating conda environment 'crm-backend'..."
if conda env list | grep -q "crm-backend"; then
    echo "⚠️  Environment 'crm-backend' already exists. Updating it..."
    conda env update -f environment.yml -n crm-backend
else
    conda env create -f environment.yml
fi

# Activate environment and install additional dev dependencies
echo "🔧 Installing additional development dependencies..."
eval "$(conda shell.bash hook)"
conda activate crm-backend

# Install pre-commit hooks if available
if [ -f ".pre-commit-config.yaml" ]; then
    echo "🪝 Setting up pre-commit hooks..."
    pip install pre-commit
    pre-commit install
fi

# Create .env file from template if it doesn't exist
if [ ! -f ".env" ] && [ -f ".env.local.template" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.local.template .env
    echo "📝 Please edit .env file with your local configuration"
fi

echo ""
echo "✅ Local development environment setup complete!"
echo ""
echo "🎯 Next steps:"
echo "   1. Activate the environment: conda activate crm-backend"
echo "   2. Edit .env file with your local database settings"
echo "   3. Set up local services using ONE of these options:"
echo ""
echo "      🐳 Option A: Use Docker for services only (RECOMMENDED)"
echo "         docker run --name crm-postgres-local \\"
echo "           -e POSTGRES_DB=crm_db \\"
echo "           -e POSTGRES_USER=crm_user \\"
echo "           -e POSTGRES_PASSWORD=crm_password \\"
echo "           -p 5432:5432 -d postgres:15-alpine"
echo ""
echo "         docker run --name crm-redis-local \\"
echo "           -p 6400:6400 -d redis:7-alpine"
echo ""
echo "      🍺 Option B: Use Homebrew (macOS)"
echo "         brew install postgresql@15 redis"
echo "         brew services start postgresql@15 redis"
echo "         createuser crm_user"
echo "         createdb crm_db -O crm_user"
echo ""
echo "      🐍 Option C: Use existing Docker Compose services"
echo "         docker-compose up postgres redis -d"
echo "         # Then use DATABASE_URL=postgresql+asyncpg://crm_user:crm_password@localhost:5433/crm_db"
echo ""
echo "   4. Run the application: uvicorn app.main:app --reload"
echo ""
echo "📚 For more information, see backend/README.md"