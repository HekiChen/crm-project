# CRM Project

[![CI/CD Pipeline](https://github.com/HekiChen/crm-project/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/HekiChen/crm-project/actions/workflows/ci-cd.yml)
[![Backend](https://img.shields.io/badge/backend-FastAPI-009688?logo=fastapi)](./backend)
[![Frontend](https://img.shields.io/badge/frontend-Vue.js-4FC08D?logo=vue.js)](./frontend)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker)](./docker-compose.prod.yml)

A modern Customer Relationship Management system built with FastAPI backend, Vue.js frontend, and full CI/CD automation.

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

# Run the backend application from project root
python run.py
```

### API Access

- **API Base URL**: <http://localhost:8000>
- **Interactive Docs**: <http://localhost:8000/docs>
- **Health Check**: <http://localhost:8000/api/v1/health>
- **Database Health**: <http://localhost:8000/api/v1/health/db>

## Features

### Position/Job Role Management

Comprehensive position management system for organizing job roles within your organization:

**Key Features:**
- ✅ CRUD operations for position/job roles
- ✅ Unique position codes (e.g., 'SSE-001', 'PM-001')
- ✅ Hierarchical levels (1-10) for organizational structure
- ✅ Active/inactive status tracking
- ✅ Employee-position relationships with FK constraints
- ✅ Soft delete with automatic employee position cleanup
- ✅ Pagination and filtering support

**API Endpoints:**
- `POST /api/v1/positions` - Create new position
- `GET /api/v1/positions/{id}` - Get position by ID
- `GET /api/v1/positions` - List positions (with pagination and filters)
- `PUT /api/v1/positions/{id}` - Update position
- `DELETE /api/v1/positions/{id}` - Soft delete position

**Example Usage:**
```bash
# Create a new position
curl -X POST http://localhost:8000/api/v1/positions \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Senior Software Engineer",
    "code": "SSE-001",
    "level": 5,
    "description": "Responsible for designing and implementing complex software systems",
    "is_active": true
  }'

# List all active positions
curl http://localhost:8000/api/v1/positions?is_active=true

# Get employees by position
curl http://localhost:8000/api/v1/employees?position_id={position_id}
```

**Database Schema:**
- Positions table with unique code constraint
- FK relationship: `employees.position_id → positions.id`
- ON DELETE SET NULL: Employee positions auto-cleared when position deleted
- Soft delete: Positions marked as deleted but retained for audit

### Development Commands

```bash
# View service logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Rebuild after changes
docker-compose up --build
```

## CRUD Template System

The project includes a powerful CLI tool for generating production-ready CRUD operations:

```bash
# Quick start - generate a User entity
crud-generate user \
  --fields "username:str:unique,email:str:unique,full_name:str,is_active:bool"

# Advanced - generate Employee with CRM domain pattern
crud-generate employee \
  --domain employee \
  --fields "first_name:str,last_name:str,email:str:unique,phone:phone,hire_date:date,salary:money"
```

### What Gets Generated

Each entity automatically creates:

- 📦 **Model**: SQLAlchemy model with relationships
- ⚙️ **Service**: Business logic layer with CRUD operations
- 🌐 **Router**: FastAPI endpoints with OpenAPI documentation
- 📋 **Schemas**: Pydantic models for validation
- ✅ **API Tests**: Comprehensive endpoint tests
- 🧪 **Service Tests**: Business logic tests
- 🔄 **Migration**: Alembic migration script

### Features

- **15 field types**: str, text, int, float, decimal, money, bool, date, datetime, time, uuid, json, email, phone, fk
- **Field constraints**: unique, nullable, index, primary
- **Domain patterns**: Built-in patterns for employee, customer, generic entities
- **Soft delete**: Optional soft delete support
- **Timestamps**: Automatic created_at/updated_at tracking
- **Audit trails**: Built-in audit field support
- **Foreign keys**: Automatic relationship handling

### Example Output

```bash
$ crud-generate customer --domain customer --fields "first_name:str,last_name:str,email:str:unique"

✨ CRUD generation complete! ✨

Generated 7 files for customer entity:
┌──────┬─────────────────────────────────────────────────┐
│ Type │ File                                            │
├──────┼─────────────────────────────────────────────────┤
│ 📦   │ app/models/customer.py                          │
│ ⚙️   │ app/services/customer_service.py                │
│ 🌐   │ app/api/v1/endpoints/customers.py               │
│ 📋   │ app/schemas/customer.py                         │
│ ✅   │ tests/test_customers_api.py                     │
│ 🧪   │ tests/test_customers_service.py                 │
│ 🔄   │ migrations/versions/xxx_add_customers_table.py  │
└──────┴─────────────────────────────────────────────────┘

📊 Statistics:
• Files generated: 7
• Migrations created: 1
• Entity: customer
• Fields: 5 (first_name, last_name, email, customer_type, account_status)

📋 Next Steps:
1. Apply migration: alembic upgrade head
2. Start server: uvicorn app.main:app --reload
3. Test API: curl http://localhost:8000/api/v1/customers
4. View docs: http://localhost:8000/docs
5. Run tests: pytest tests/test_customers_api.py -v
```

### Documentation

- **Quick Start**: See examples above
- **Detailed Guide**: [backend/docs/crud-template-system.md](backend/docs/crud-template-system.md)
- **Usage Examples**: [backend/docs/examples/README.md](backend/docs/examples/README.md)
- **Field Types**: Full reference in documentation
- **Domain Patterns**: Employee, Customer, Generic patterns
- **Customization**: Template editing guide

### Common Use Cases

```bash
# Basic user management
crud-generate user --fields "username:str:unique,email:str:unique,full_name:str"

# Product catalog with inventory
crud-generate product --fields "name:str,sku:str:unique,price:decimal,stock:int"

# Order management
crud-generate order --fields "customer_id:fk:customers,order_date:datetime,status:str,total:decimal"

# Employee management with CRM features
crud-generate employee --domain employee --fields "first_name:str,last_name:str,email:str:unique"
```

### Benefits

- ✅ **Save hours** of boilerplate coding
- ✅ **Consistent patterns** across all entities
- ✅ **Production-ready** code with tests
- ✅ **Best practices** built-in (pagination, validation, error handling)
- ✅ **Type-safe** with Pydantic validation
- ✅ **Documented** with OpenAPI schemas
- ✅ **Tested** with comprehensive test coverage

---

## Development Workflow

This project uses OpenSpec for specification-driven development:

1. **Propose**: Create change proposals in `openspec/changes/`
2. **Implement**: Follow specs to implement features
3. **Archive**: Document completed changes in `openspec/specs/`

## Running Backend Services

To start the backend FastAPI server from the project root:

```bash
python run.py
```

This will launch the API at <http://localhost:8000> with auto-reload enabled for development.

Make sure your environment and dependencies are set up (see Getting Started above).

See `openspec/AGENTS.md` for detailed workflow instructions.

## Deployment

### Quick Deploy with CI/CD

This project includes a complete CI/CD pipeline that automatically:
- ✅ Runs tests on every push
- ✅ Bumps version numbers
- ✅ Builds Docker containers
- ✅ Deploys to staging/production

**5-Minute Setup**: See [QUICK_START.md](./QUICK_START.md)

**Full Documentation**: See [DEPLOYMENT.md](./DEPLOYMENT.md)

### Manual Deployment

```bash
# Deploy to production
./deploy.sh production

# Deploy to staging
./deploy.sh staging
```

### Container Images

Pre-built images available at:
```
ghcr.io/hekichen/crm-project/backend:latest
ghcr.io/hekichen/crm-project/frontend:latest
```

