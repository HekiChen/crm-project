"""
Statistics service for dashboard metrics.

Provides aggregate statistics for the dashboard display.
"""
from datetime import date, timedelta
from typing import Dict

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.models.department import Department
from app.models.role import Role
# from app.models.work_log import WorkLog  # Commented out - pending implementation


class StatsService:
    """
    Service for retrieving dashboard statistics.
    
    Provides efficient aggregate queries for system metrics.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize stats service.
        
        Args:
            db: Async database session
        """
        self.db = db
    
    async def get_dashboard_stats(self) -> Dict[str, int]:
        """
        Get dashboard statistics including counts of employees, departments, roles,
        and recent work log activities.
        
        Returns:
            Dictionary containing:
                - total_employees: Count of non-deleted employees
                - total_departments: Count of non-deleted departments
                - total_roles: Count of non-deleted roles
                - recent_activities: Count of work logs from last 7 days
        
        Example:
            >>> stats = await service.get_dashboard_stats()
            >>> print(stats)
            {
                "total_employees": 42,
                "total_departments": 8,
                "total_roles": 5,
                "recent_activities": 156
            }
        """
        # Count non-deleted employees
        employee_count = await self.db.scalar(
            select(func.count(Employee.id)).where(Employee.is_deleted == False)
        ) or 0
        
        # Count non-deleted departments
        department_count = await self.db.scalar(
            select(func.count(Department.id)).where(Department.is_deleted == False)
        ) or 0
        
        # Count non-deleted roles
        role_count = await self.db.scalar(
            select(func.count(Role.id)).where(Role.is_deleted == False)
        ) or 0
        
        # Count work logs from last 7 days
        # Temporarily disabled - WorkLog implementation pending
        # seven_days_ago = date.today() - timedelta(days=7)
        # recent_activities_count = await self.db.scalar(
        #     select(func.count(WorkLog.id)).where(WorkLog.date >= seven_days_ago)
        # ) or 0
        recent_activities_count = 0
        
        return {
            "total_employees": employee_count,
            "total_departments": department_count,
            "total_roles": role_count,
            "recent_activities": recent_activities_count,
        }
