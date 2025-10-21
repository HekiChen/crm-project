# CRM Project

A modern Customer Relationship Management system built with FastAPI backend and standardized development practices.

## Overview

This project implements a scalable CRM system using:

- **Backend**: FastAPI with Python 3.11+
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Caching**: Redis for performance optimization
- **Deployment**: Docker containerization
- **Development**: OpenSpec-driven development workflow

## Core Requirements

- Python 3.11+
- Docker and Docker Compose
- Conda/Mamba package manager

## Project Structure

```text
crm-project/
├── backend/                 # FastAPI backend application
│   ├── app/
│   │   ├── main.py         # Application entry point
│   │   ├── core/           # Core configuration and database
│   │   └── api/            # API endpoints and health checks
│   ├── tests/              # Test suite
│   ├── Dockerfile          # Backend container configuration
│   ├── environment.yml     # Conda environment definition
│   └── pyproject.toml      # Python project configuration
├── openspec/               # OpenSpec development workflow
│   ├── AGENTS.md           # AI assistant instructions
│   ├── project.md          # Project specifications
│   └── specs/              # Technical specifications
└── docker-compose.yml     # Multi-service orchestration
```

## Getting Started

### Option 1: Docker Development (Recommended for consistency)

```bash
# Start all services (backend, database, cache)
docker-compose up -d

# Check service health
curl http://localhost:8000/api/v1/health
```

### Option 2: Local Development (Recommended for development speed)

```bash
# Navigate to backend directory
cd backend

# Run automated setup (one-time setup)
./setup-local-env.sh

# Activate conda environment
conda activate crm-backend

# Configure environment
cp .env.local.template .env
# Edit .env with your local settings

# Start local PostgreSQL and Redis services
# See backend/README.md for detailed setup instructions

# Run the application
uvicorn app.main:app --reload
```

### API Access

- **API Base URL**: <http://localhost:8000>
- **Interactive Docs**: <http://localhost:8000/docs>
- **Health Check**: <http://localhost:8000/api/v1/health>
- **Database Health**: <http://localhost:8000/api/v1/health/db>

### Development Commands

```bash
# View service logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Rebuild after changes
docker-compose up --build
```

## Development Workflow

This project uses OpenSpec for specification-driven development:

1. **Propose**: Create change proposals in `openspec/changes/`
2. **Implement**: Follow specs to implement features
3. **Archive**: Document completed changes in `openspec/specs/`

See `openspec/AGENTS.md` for detailed workflow instructions.
