#!/bin/bash

# Local database setup script for CRM Backend
set -e

echo "🗄️  Setting up local database services for CRM Backend..."

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if Docker container is running
container_running() {
    docker ps --format "table {{.Names}}" | grep -q "$1"
}

echo "📋 Available setup options:"
echo "1. Docker containers (recommended)"
echo "2. Use existing Docker Compose services" 
echo "3. Homebrew services (macOS only)"
echo "4. Show connection troubleshooting"

read -p "Choose an option (1-4): " choice

case $choice in
    1)
        echo "🐳 Setting up Docker containers..."
        
        # Check if Docker is available
        if ! command_exists docker; then
            echo "❌ Docker not found. Please install Docker first."
            exit 1
        fi
        
        # Set up PostgreSQL
        if container_running "crm-postgres-local"; then
            echo "ℹ️  PostgreSQL container already running"
        else
            echo "📦 Starting PostgreSQL container..."
            docker run --name crm-postgres-local \
                -e POSTGRES_DB=crm_db \
                -e POSTGRES_USER=crm_user \
                -e POSTGRES_PASSWORD=crm_password \
                -p 5432:5432 \
                -d postgres:15-alpine
            
            echo "⏳ Waiting for PostgreSQL to be ready..."
            sleep 5
        fi
        
        # Set up Redis
        if container_running "crm-redis-local"; then
            echo "ℹ️  Redis container already running"
        else
            echo "📦 Starting Redis container..."
            docker run --name crm-redis-local \
                -p 6400:6400 \
                -d redis:7-alpine
        fi
        
        echo "✅ Database services are running!"
        echo "📝 Use these settings in your .env file:"
        echo "DATABASE_URL=postgresql+asyncpg://crm_user:crm_password@localhost:5432/crm_db"
        echo "REDIS_URL=redis://localhost:6400/0"
        ;;
        
    2)
        echo "🐳 Using Docker Compose services..."
        
        if [ ! -f "../docker-compose.yml" ]; then
            echo "❌ docker-compose.yml not found. Run from backend directory."
            exit 1
        fi
        
        cd ..
        echo "📦 Starting PostgreSQL and Redis from Docker Compose..."
        docker-compose up postgres redis -d
        
        echo "✅ Docker Compose services are running!"
        echo "📝 Use these settings in your .env file:"
        echo "DATABASE_URL=postgresql+asyncpg://crm_user:crm_password@localhost:5433/crm_db"
        echo "REDIS_URL=redis://localhost:6410/0"
        ;;
        
    3)
        echo "🍺 Setting up Homebrew services..."
        
        if ! command_exists brew; then
            echo "❌ Homebrew not found. Please install Homebrew first."
            echo "   Visit: https://brew.sh"
            exit 1
        fi
        
        # Install PostgreSQL and Redis
        echo "📦 Installing PostgreSQL and Redis..."
        brew install postgresql@15 redis
        
        # Start services
        echo "🚀 Starting services..."
        brew services start postgresql@15
        brew services start redis
        
        # Set up database
        echo "🗄️  Setting up database and user..."
        createuser crm_user 2>/dev/null || echo "ℹ️  User crm_user already exists"
        createdb crm_db -O crm_user 2>/dev/null || echo "ℹ️  Database crm_db already exists"
        
        echo "✅ Homebrew services are running!"
        echo "📝 Use these settings in your .env file:"
        echo "DATABASE_URL=postgresql+asyncpg://crm_user:crm_password@localhost:5432/crm_db"
        echo "REDIS_URL=redis://localhost:6400/0"
        ;;
        
    4)
        echo "🔧 Connection troubleshooting:"
        echo ""
        echo "Common issues and solutions:"
        echo ""
        echo "1. 'role \"crm_user\" does not exist':"
        echo "   - Run this script to set up the database"
        echo "   - Or create user manually: createuser crm_user"
        echo ""
        echo "2. 'database \"crm_db\" does not exist':"
        echo "   - Create database: createdb crm_db -O crm_user"
        echo ""
        echo "3. 'connection refused':"
        echo "   - Check if PostgreSQL is running"
        echo "   - Check the port (5432 for local, 5433 for Docker Compose)"
        echo ""
        echo "4. 'Redis connection failed':"
        echo "   - Check if Redis is running"
        echo "   - Check the port (6400 for local, 6410 for Docker Compose)"
        echo ""
        echo "5. Test connections:"
        echo "   PostgreSQL: pg_isready -h localhost -p 5432"
        echo "   Redis: redis-cli ping"
        ;;
        
    *)
        echo "❌ Invalid option. Please choose 1-4."
        exit 1
        ;;
esac

echo ""
echo "🎯 Next steps:"
echo "1. Update your .env file with the connection strings shown above"
echo "2. Run: uvicorn app.main:app --reload"
echo "3. Test: curl http://localhost:8000/api/v1/health"