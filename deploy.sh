#!/bin/bash

# CRM Application Deployment Script
# Usage: ./deploy.sh [staging|production]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-staging}
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.${ENVIRONMENT}"

echo -e "${GREEN}🚀 Starting deployment to ${ENVIRONMENT}...${NC}"

# Check if environment file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ Environment file ${ENV_FILE} not found!${NC}"
    echo -e "${YELLOW}💡 Copy .env.production.example to ${ENV_FILE} and configure it.${NC}"
    exit 1
fi

# Load environment variables
set -a
source "$ENV_FILE"
set +a

echo -e "${GREEN}✓ Environment file loaded${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker is running${NC}"

# Login to GitHub Container Registry
if [ -n "$GITHUB_TOKEN" ]; then
    echo -e "${YELLOW}🔐 Logging in to GitHub Container Registry...${NC}"
    echo "$GITHUB_TOKEN" | docker login ghcr.io -u "$GITHUB_USERNAME" --password-stdin
    echo -e "${GREEN}✓ Logged in to GHCR${NC}"
fi

# Pull latest images
echo -e "${YELLOW}📦 Pulling latest Docker images...${NC}"
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" pull
echo -e "${GREEN}✓ Images pulled${NC}"

# Stop existing containers
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down
echo -e "${GREEN}✓ Containers stopped${NC}"

# Start services
echo -e "${YELLOW}🔄 Starting services...${NC}"
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --remove-orphans
echo -e "${GREEN}✓ Services started${NC}"

# Wait for services to be healthy
echo -e "${YELLOW}⏳ Waiting for services to be healthy...${NC}"
sleep 10

# Check backend health
BACKEND_URL="http://localhost:${BACKEND_PORT:-8000}/api/v1/health"
echo -e "${YELLOW}🏥 Checking backend health at ${BACKEND_URL}...${NC}"

MAX_RETRIES=30
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f -s "$BACKEND_URL" > /dev/null; then
        echo -e "${GREEN}✓ Backend is healthy${NC}"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -e "${YELLOW}   Attempt ${RETRY_COUNT}/${MAX_RETRIES}...${NC}"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}❌ Backend failed to start!${NC}"
    echo -e "${YELLOW}📋 Showing logs:${NC}"
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" logs --tail=50 backend
    exit 1
fi

# Check frontend health
FRONTEND_URL="http://localhost:${FRONTEND_PORT:-80}/health"
echo -e "${YELLOW}🏥 Checking frontend health at ${FRONTEND_URL}...${NC}"

if curl -f -s "$FRONTEND_URL" > /dev/null; then
    echo -e "${GREEN}✓ Frontend is healthy${NC}"
else
    echo -e "${RED}⚠️  Frontend health check failed (non-critical)${NC}"
fi

# Clean up old images
echo -e "${YELLOW}🧹 Cleaning up old Docker images...${NC}"
docker image prune -af --filter "until=24h"
echo -e "${GREEN}✓ Cleanup complete${NC}"

# Show running containers
echo -e "${GREEN}📊 Running containers:${NC}"
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps

echo ""
echo -e "${GREEN}✅ Deployment to ${ENVIRONMENT} completed successfully!${NC}"
echo ""
echo -e "${YELLOW}📝 Useful commands:${NC}"
echo -e "  View logs:    docker-compose -f $COMPOSE_FILE logs -f"
echo -e "  Stop:         docker-compose -f $COMPOSE_FILE down"
echo -e "  Restart:      docker-compose -f $COMPOSE_FILE restart"
echo -e "  Status:       docker-compose -f $COMPOSE_FILE ps"
echo ""
