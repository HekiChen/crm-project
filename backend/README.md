# CRM Backend API

A FastAPI-based backend for the CRM system with employee management, work logging, and role-based access control.

## Features

- **FastAPI Framework**: Modern, fast (high-performance) web framework
- **Async Support**: Full async/await support with SQLAlchemy async
- **Database**: PostgreSQL with SQLAlchemy ORM and Alembic migrations
- **Authentication**: JWT-based authentication system
- **Caching**: Redis for caching and session storage
- **Task Queue**: Celery for background tasks (work log exports)
- **Testing**: Comprehensive test suite with pytest
- **Code Quality**: Ruff for linting and formatting
- **Containerization**: Docker and Docker Compose for development
- **API Documentation**: Automatic OpenAPI/Swagger documentation

## Quick Start with Docker (Recommended)

1. **Clone and navigate to the project:**
   ```bash
   git clone <repository-url>
   cd crm-project
   ```

2. **Start all services:**
   ```bash
   docker-compose up --build
   ```

3. **Access the API:**
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/api/v1/health

## Local Development Setup

### Prerequisites

- Python 3.11+
- Conda (Anaconda or Miniconda)
- PostgreSQL
- Redis

### Installation

#### Option A: Quick Setup with Script (Recommended)

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Run the automated setup script:**
   ```bash
   ./setup-local-env.sh
   ```

3. **Activate the environment and configure:**
   ```bash
   conda activate crm-backend
   cp .env.local.template .env
   # Edit .env with your local database settings
   ```

4. **Start local services** (see Local Services Setup section below)

5. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

6. **Start the development server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

#### Option B: Manual Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create conda environment:**
   ```bash
   conda env create -f environment.yml
   conda activate crm-backend
   ```

3. **Install additional development dependencies:**
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.local.template .env
   # Edit .env with your configuration
   ```

5. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

6. **Start the development server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Local Services Setup

For local development, you need PostgreSQL and Redis running locally.

### PostgreSQL Setup

#### Using Docker (Recommended)
```bash
docker run --name crm-postgres \
  -e POSTGRES_DB=crm_db \
  -e POSTGRES_USER=crm_user \
  -e POSTGRES_PASSWORD=crm_password \
  -p 5432:5432 \
  -d postgres:15-alpine
```

#### Using Homebrew (macOS)
```bash
brew install postgresql@15
brew services start postgresql@15

# Create database and user
createuser crm_user
createdb crm_db -O crm_user
```

### Redis Setup

#### Using Docker (Recommended)
```bash
docker run --name crm-redis -p 6379:6379 -d redis:7-alpine
```

#### Using Homebrew (macOS)
```bash
brew install redis
brew services start redis
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_health.py

# Run tests with specific markers
pytest -m "not slow"
```

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Fix linting issues
ruff check --fix .
```

### Database Operations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Show migration history
alembic history
```

### Celery Tasks

```bash
# Start Celery worker
celery -A app.core.celery worker --loglevel=info

# Start Celery flower (monitoring)
celery -A app.core.celery flower

# Run specific task
celery -A app.core.celery call app.tasks.export_work_logs
```

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # Settings and configuration
│   │   └── database.py      # Database connection and session
│   ├── api/
│   │   ├── __init__.py
│   │   └── health.py        # Health check endpoints
│   ├── models/
│   │   ├── __init__.py      # Database models
│   │   └── ...
│   ├── services/
│   │   ├── __init__.py      # Business logic services
│   │   └── ...
│   └── utils/
│       ├── __init__.py      # Utility functions
│       └── ...
├── tests/
│   ├── __init__.py
│   ├── conftest.py         # Test configuration and fixtures
│   └── test_*.py           # Test files
├── alembic/                # Database migrations
├── environment.yml         # Conda environment configuration
├── pyproject.toml          # Project configuration and Ruff settings
├── pytest.ini             # pytest configuration
├── Dockerfile              # Docker configuration
├── .env.example            # Environment variables template
└── README.md               # This file
```

## Configuration

The application uses environment variables for configuration. Key settings:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT token secret key
- `DEBUG`: Enable/disable debug mode
- `ENVIRONMENT`: deployment environment (development/testing/production)

See `.env.example` for all available configuration options.

## API Documentation

When running in development mode (`DEBUG=true`), automatic API documentation is available:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Health Checks

The API provides health check endpoints:

- `GET /api/v1/health` - Basic application health
- `GET /api/v1/health/db` - Database connectivity check

## Production Deployment

For production deployment:

1. Set `DEBUG=false` in environment variables
2. Use a strong `SECRET_KEY`
3. Configure proper `DATABASE_URL` and `REDIS_URL`
4. Set up proper logging and monitoring
5. Use a reverse proxy (nginx) in front of the application
6. Consider using a production WSGI server like Gunicorn

## Contributing

1. Follow the existing code style (enforced by Ruff)
2. Write tests for new features
3. Update documentation as needed
4. Ensure all tests pass before submitting changes

## Troubleshooting

### Common Issues

1. **Database connection errors**: Ensure PostgreSQL is running and credentials are correct
2. **Redis connection errors**: Ensure Redis is running and accessible
3. **Import errors**: Ensure conda environment is activated
4. **Migration errors**: Check database permissions and connection string

### Development Tips

- Use `docker-compose logs backend` to view application logs
- Use `docker-compose exec backend bash` to access container shell
- Use `conda activate crm-backend` before running local commands
- Check health endpoints to verify service status