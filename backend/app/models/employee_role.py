"""
EmployeeRole model for CRM system.

Junction table for many-to-many relationship between Employee and Role.
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base as CoreBase

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.role import Role


class EmployeeRole(CoreBase):
    """
    EmployeeRole junction table for Employee-Role many-to-many relationship.
    
    NOTE: Simplified schema without soft delete (assignment is binary: exists or doesn't).
    Tracks who assigned which role to which employee and when.
    """
    __tablename__ = "employee_roles"
    __table_args__ = (
        UniqueConstraint("employee_id", "role_id", name="uq_employee_role"),
    )
    
    # Primary key
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        index=True,
        doc="Unique identifier"
    )
    
    # Foreign keys
    employee_id: Mapped[UUID] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Employee receiving this role"
    )
    
    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Role being assigned"
    )
    
    # Audit fields
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        doc="Timestamp when role was assigned"
    )
    
    assigned_by_id: Mapped[Optional[UUID]] = mapped_column(
        nullable=True,
        doc="ID of user who assigned this role"
    )
    
    # Relationships
    employee: Mapped["Employee"] = relationship(
        "Employee",
        back_populates="employee_roles",
        foreign_keys=[employee_id],
        lazy="select"
    )
    
    role: Mapped["Role"] = relationship(
        "Role",
        back_populates="employee_roles",
        foreign_keys=[role_id],
        lazy="select"
    )
    
    def __repr__(self) -> str:
        """String representation of EmployeeRole."""
        return f"<EmployeeRole(id={self.id}, employee_id={self.employee_id}, role_id={self.role_id})>"
