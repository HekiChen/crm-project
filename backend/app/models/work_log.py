"""
WorkLog model for CRM system.

Represents daily work activity tracking with approval workflow.
"""
from datetime import date, datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.employee import Employee


class WorkLog(BaseModel):
    """
    WorkLog model representing daily work activities.
    
    WorkLogs track employee work hours and activities with an approval workflow.
    Status progression: draft → submitted → approved/rejected
    """
    __tablename__ = "work_logs"
    
    # Core fields
    employee_id: Mapped[UUID] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Employee who logged this work"
    )
    
    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        doc="Date of the work activity"
    )
    
    hours: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        doc="Hours worked (e.g., 8.50 for 8 hours 30 minutes)"
    )
    
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Description of work performed"
    )
    
    # Workflow status
    status: Mapped[str] = mapped_column(
        String(20),
        default="draft",
        nullable=False,
        index=True,
        doc="Workflow status: draft, submitted, approved, rejected"
    )
    
    # Approval fields
    approver_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Employee who approved or rejected this work log"
    )
    
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        doc="Timestamp when work log was approved or rejected"
    )
    
    rejection_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Reason for rejection (if status=rejected)"
    )
    
    # Relationships
    employee: Mapped["Employee"] = relationship(
        "Employee",
        back_populates="work_logs",
        foreign_keys=[employee_id],
        lazy="select",
        doc="Employee who created this work log"
    )
    
    approver: Mapped[Optional["Employee"]] = relationship(
        "Employee",
        back_populates="approved_work_logs",
        foreign_keys=[approver_id],
        lazy="select",
        doc="Employee who approved/rejected this work log"
    )
    
    def __repr__(self) -> str:
        """String representation of WorkLog."""
        return f"<WorkLog(id={self.id}, employee_id={self.employee_id}, date={self.date}, hours={self.hours}, status='{self.status}')>"
