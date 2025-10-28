"""
FastAPI main application.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.config import settings
from app.core.database import init_db, close_db
from app.api.health import router as health_router
from app.middleware.security import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    configure_cors,
)
from app.middleware.logging import LoggingMiddleware
from app.middleware.error_handler import register_exception_handlers
from app.middleware.response_formatter import ResponseFormatterMiddleware
from app.api.employees import router as employees_router
from app.api.positions import router as positions_router
from app.api.departments import router as departments_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting up CRM Backend API...")
    await init_db()
    yield
    # Shutdown
    logger.info("Shutting down CRM Backend API...")
    await close_db()


# FastAPI application instance
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Middleware registration (order matters - outer to inner)
# 1. Security headers (outermost - applied to all responses including errors)
app.add_middleware(SecurityHeadersMiddleware)

# 2. CORS (allow cross-origin requests)
configure_cors(app)

# 3. Rate limiting (protect against abuse)
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=settings.rate_limit_per_minute
)

# 4. Logging (track requests)
app.add_middleware(LoggingMiddleware)

# 5. Response formatting (wrap successful responses)
# Now using pure ASGI implementation to avoid BaseHTTPMiddleware Content-Length issues
app.add_middleware(ResponseFormatterMiddleware)

# 6. Exception handlers (catch and format errors)
# Note: Auth is handled via dependency injection, not middleware
register_exception_handlers(app)

# Include routers
app.include_router(health_router, prefix=settings.api_v1_str, tags=["health"])
app.include_router(employees_router, prefix="/api/v1/employees", tags=["employees"])
app.include_router(positions_router, prefix="/api/v1/positions", tags=["positions"])
app.include_router(departments_router, prefix="/api/v1/departments", tags=["departments"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs_url": "/docs" if settings.debug else None
    }