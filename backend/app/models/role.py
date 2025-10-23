"""
Role model for CRM system.

Represents permission groups for access control (RBAC).
"""
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.employee_role import EmployeeRole
    from app.models.role_menu_perm import RoleMenuPerm


class Role(BaseModel):
    """
    Role model representing permission groups.
    
    Roles define groups of permissions that can be assigned to employees.
    System roles (Admin, Manager, Employee) are built-in and cannot be deleted.
    """
    __tablename__ = "roles"
    
    # Core fields
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Role name (e.g., 'Admin', 'Manager', 'Developer')"
    )
    
    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Unique role code (e.g., 'ADMIN', 'MGR', 'DEV')"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Detailed description of the role and its permissions"
    )
    
    # System role flag
    is_system_role: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Whether this is a built-in system role (cannot be deleted)"
    )
    
    # Relationships
    employee_roles: Mapped[list["EmployeeRole"]] = relationship(
        "EmployeeRole",
        back_populates="role",
        cascade="all, delete-orphan",
        lazy="select",
        doc="Employee role assignments (many-to-many via junction table)"
    )
    
    menu_permissions: Mapped[list["RoleMenuPerm"]] = relationship(
        "RoleMenuPerm",
        back_populates="role",
        cascade="all, delete-orphan",
        lazy="select",
        doc="Menu permissions for this role (many-to-many via junction table)"
    )
    
    def __repr__(self) -> str:
        """String representation of Role."""
        system_flag = " [SYSTEM]" if self.is_system_role else ""
        return f"<Role(id={self.id}, code='{self.code}', name='{self.name}'{system_flag})>"
