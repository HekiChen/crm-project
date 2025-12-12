"""Work log model for tracking employee work progress."""

import enum
from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Date, Enum, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.employee import Employee


class LogType(str, enum.Enum):
    """Work log frequency types."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class WorkLog(BaseModel):
    """
    Work log model for tracking employee progress.
    
    Employees create work logs to track their progress, issues, and plans.
    Managers can rate work logs using a 1-5 star rating system.
    """
    __tablename__ = "work_logs"
    
    employee_id: Mapped[UUID] = mapped_column(ForeignKey("employees.id"), nullable=False, index=True)
    log_type: Mapped[LogType] = mapped_column(Enum(LogType), nullable=False, index=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    progress: Mapped[str] = mapped_column(Text, nullable=False)
    issues: Mapped[str | None] = mapped_column(Text, nullable=True)
    plans: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-5 stars, null if not rated
    rated_by_id: Mapped[UUID | None] = mapped_column(ForeignKey("employees.id"), nullable=True)
    rated_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    
    # Relationships
    employee = relationship("Employee", foreign_keys=[employee_id])
    rated_by = relationship("Employee", foreign_keys=[rated_by_id])
    
    def __repr__(self) -> str:
        return f"<WorkLog(id={self.id}, employee_id={self.employee_id}, type={self.log_type}, start={self.start_date})>"
