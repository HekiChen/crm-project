"""
Position model for CRM system.

Represents job roles/positions within the organization.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Position(BaseModel):
    """
    Position model representing job roles in the organization.
    
    Positions define roles that employees can be assigned to,
    with optional department association and hierarchical levels.
    """
    __tablename__ = "positions"
    
    # Core fields
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
        doc="Position name (e.g., 'Software Engineer', 'Manager')"
    )
    
    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Unique position code (e.g., 'SE-001', 'MGR-001')"
    )
    
    level: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        doc="Position level in organizational hierarchy (1-10)"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Detailed description of the position and responsibilities"
    )
    
    # Department reference (nullable until Department entity implemented)
    department_id: Mapped[Optional[UUID]] = mapped_column(
        nullable=True,
        index=True,
        doc="Reference to department (when Department entity exists)"
    )
    
    # Status field
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Whether position is active and available for assignment"
    )
    
    # Relationships
    employees: Mapped[list["Employee"]] = relationship(
        "Employee",
        back_populates="position",
        foreign_keys="[Employee.position_id]",
        lazy="select",
        doc="Employees assigned to this position"
    )
    
    def __repr__(self) -> str:
        """String representation of Position."""
        return f"<Position(id={self.id}, code='{self.code}', name='{self.name}')>"
