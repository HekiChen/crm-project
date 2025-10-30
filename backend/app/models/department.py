"""
Department model for CRM system.

Represents organizational units for grouping employees and positions.
"""
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.position import Position


class Department(BaseModel):
    """
    Department model representing organizational units.
    
    Departments define organizational structure and can be hierarchical.
    Each department can have a manager (employee) and contain positions/employees.
    """
    __tablename__ = "departments"
    
    # Core fields
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
        doc="Department name (e.g., 'Engineering', 'Sales')"
    )
    
    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Unique department code (e.g., 'ENG-001', 'SALES-001')"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Detailed description of the department and its responsibilities"
    )
    
    # Hierarchical structure - self-referential
    parent_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Reference to parent department for hierarchy"
    )
    
    # Department head/manager reference
    manager_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Reference to employee who manages this department"
    )
    
    # Status field
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Whether department is active and operational"
    )
    
    # Relationships
    employees: Mapped[list["Employee"]] = relationship(
        "Employee",
        back_populates="department",
        foreign_keys="[Employee.department_id]",
        lazy="select",
        doc="Employees assigned to this department"
    )
    
    positions: Mapped[list["Position"]] = relationship(
        "Position",
        back_populates="department",
        foreign_keys="[Position.department_id]",
        lazy="select",
        doc="Positions assigned to this department"
    )
    
    # Hierarchical relationships
    parent: Mapped[Optional["Department"]] = relationship(
        "Department",
        remote_side="[Department.id]",
        back_populates="children",
        foreign_keys=[parent_id],
        lazy="select",
        doc="Parent department in hierarchy"
    )
    
    children: Mapped[list["Department"]] = relationship(
        "Department",
        back_populates="parent",
        foreign_keys=[parent_id],
        lazy="select",
        doc="Child departments in hierarchy"
    )
    
    # Manager relationship
    manager_employee: Mapped[Optional["Employee"]] = relationship(
        "Employee",
        foreign_keys=[manager_id],
        lazy="select",
        doc="Employee who manages this department"
    )
    
    def __repr__(self) -> str:
        """String representation of Department."""
        return f"<Department(id={self.id}, code='{self.code}', name='{self.name}')>"
