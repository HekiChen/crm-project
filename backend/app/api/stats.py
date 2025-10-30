"""
Statistics API endpoints.

Provides dashboard statistics including counts of employees, departments, roles, and recent activities.
"""
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_employee
from app.models.employee import Employee
from app.schemas.stats import DashboardStatsResponse
from app.services.stats_service import StatsService

router = APIRouter(tags=["stats"])


def get_stats_service(db: AsyncSession = Depends(get_db)) -> StatsService:
    """
    Dependency to get stats service instance.
    
    Args:
        db: Database session
        
    Returns:
        StatsService instance
    """
    return StatsService(db)


@router.get(
    "/dashboard",
    response_model=DashboardStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get dashboard statistics",
    description="""
Retrieve aggregate statistics for the dashboard display.

Returns counts of:
- **Total Employees**: Non-deleted employees in the system
- **Total Departments**: Non-deleted departments
- **Total Roles**: Non-deleted roles
- **Recent Activities**: Work log entries from the last 7 days

**Authentication**: Requires valid JWT access token.

**Performance**: Optimized with COUNT queries, typically responds in < 250ms.
    """,
    responses={
        200: {
            "description": "Successfully retrieved dashboard statistics",
            "content": {
                "application/json": {
                    "example": {
                        "data": {
                            "total_employees": 42,
                            "total_departments": 8,
                            "total_roles": 5,
                            "recent_activities": 156
                        },
                        "meta": {
                            "request_id": None,
                            "timestamp": "2025-10-29T12:00:00Z"
                        }
                    }
                }
            }
        },
        401: {
            "description": "Unauthorized - invalid or missing authentication token"
        },
        503: {
            "description": "Service unavailable - database connection error"
        }
    }
)
async def get_dashboard_stats(
    service: StatsService = Depends(get_stats_service),
    current_employee: Employee = Depends(get_current_employee),
) -> Any:
    """
    Get dashboard statistics.
    
    Requires authentication. Returns aggregate counts for dashboard display.
    
    Args:
        service: Stats service instance (injected)
        current_employee: Currently authenticated employee (injected)
        
    Returns:
        Dashboard statistics with counts
    """
    stats = await service.get_dashboard_stats()
    return DashboardStatsResponse(**stats)
