"""
Dependency functions for FastAPI.
"""
from app.dependencies.auth import get_current_employee, oauth2_scheme

__all__ = [
    "get_current_employee",
    "oauth2_scheme",
]
