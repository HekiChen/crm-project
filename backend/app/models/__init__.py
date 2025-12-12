"""
SQLAlchemy database models.
"""
from app.core.database import Base
from app.models.department import Department
from app.models.position import Position
from app.models.role import Role
from app.models.employee import Employee
from app.models.menu import Menu
from app.models.employee_role import EmployeeRole
from app.models.role_menu_perm import RoleMenuPerm
# from app.models.work_log import WorkLog  # Commented out - pending implementation
from app.models.export_job import ExportJob

# Import all models here to ensure they are registered with SQLAlchemy

__all__ = [
    "Base",
    "Department",
    "Position",
    "Role",
    "Employee",
    "Menu",
    "EmployeeRole",
    "RoleMenuPerm",
    # "WorkLog",  # Commented out - pending implementation
    "ExportJob",
]