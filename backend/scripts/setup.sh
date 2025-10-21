#!/bin/bash

# CRM Backend Setup Script
# This script sets up the development environment for the CRM backend

set -e  # Exit on any error

echo "🚀 Setting up CRM Backend Development Environment..."

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    echo "❌ Conda is not installed. Please install Anaconda or Miniconda first."
    echo "   Visit: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

# Check if we're in the backend directory
if [[ ! -f "environment.yml" ]]; then
    echo "❌ Please run this script from the backend directory"
    exit 1
fi

echo "📦 Creating conda environment..."
conda env create -f environment.yml

echo "🔧 Activating environment..."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate crm-backend

echo "📋 Setting up environment file..."
if [[ ! -f ".env" ]]; then
    cp .env.example .env
    echo "✅ Created .env file from .env.example"
    echo "⚠️  Please update .env with your configuration"
else
    echo "ℹ️  .env file already exists"
fi

echo "🗃️  Setting up database..."
echo "Make sure PostgreSQL is running and accessible"

# Check if alembic is configured
if [[ -f "alembic.ini" ]]; then
    echo "📊 Running database migrations..."
    alembic upgrade head
else
    echo "⚠️  Alembic not configured. Skipping migrations."
fi

echo "🧪 Running tests to verify setup..."
pytest tests/ -v

echo "✅ Setup complete!"
echo ""
echo "🎯 Next steps:"
echo "   1. Update .env file with your configuration"
echo "   2. Ensure PostgreSQL and Redis are running"
echo "   3. Run: uvicorn app.main:app --reload"
echo "   4. Visit: http://localhost:8000/docs"
echo ""
echo "🐳 Alternative: Use Docker Compose"
echo "   docker-compose up --build"