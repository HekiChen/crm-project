"""
ExportJob model for CRM system.

Represents async task tracking for data exports (no soft delete).
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base as CoreBase

if TYPE_CHECKING:
    from app.models.employee import Employee


class ExportJob(CoreBase):
    """
    ExportJob model representing async export task tracking.
    
    NOTE: Does NOT inherit from BaseModel - no soft delete support.
    ExportJobs are historical records that should never be deleted.
    """
    __tablename__ = "export_jobs"
    
    # Primary key (manual, since not using BaseModel)
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        index=True,
        doc="Unique identifier"
    )
    
    # Core fields
    employee_id: Mapped[UUID] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Employee who requested this export"
    )
    
    export_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Type of export: work_logs, employees, reports, etc."
    )
    
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        index=True,
        doc="Task status: pending, processing, completed, failed"
    )
    
    file_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        doc="Location of exported file (S3 key, local path, etc.)"
    )
    
    params: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        doc="Export parameters as JSON (date ranges, filters, etc.)"
    )
    
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Error message if export failed"
    )
    
    # Timing fields
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        doc="Timestamp when export processing started"
    )
    
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        doc="Timestamp when export completed (success or failure)"
    )
    
    # Timestamp fields (manual, since not using BaseModel)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        doc="Timestamp when record was created"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        doc="Timestamp when record was last updated"
    )
    
    # Relationships
    employee: Mapped["Employee"] = relationship(
        "Employee",
        back_populates="export_jobs",
        foreign_keys=[employee_id],
        lazy="select",
        doc="Employee who requested this export"
    )
    
    def __repr__(self) -> str:
        """String representation of ExportJob."""
        return f"<ExportJob(id={self.id}, type='{self.export_type}', status='{self.status}', employee_id={self.employee_id})>"
