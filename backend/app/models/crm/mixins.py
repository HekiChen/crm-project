"""
Domain-specific mixins for CRM entities.

These mixins provide reusable field patterns that can be composed
with BaseModel to create CRM domain entities.
"""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import JSON, Boolean, Date, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column


class PersonMixin:
    """
    Mixin for person-related fields.
    
    Provides:
    - first_name: Person's first name
    - last_name: Person's last name
    - full_name: Computed property combining first and last name
    """
    
    __abstract__ = True
    
    first_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    @property
    def full_name(self) -> str:
        """Return the person's full name."""
        return f"{self.first_name} {self.last_name}".strip()


class ContactMixin:
    """
    Mixin for contact information fields.
    
    Provides:
    - email: Email address
    - phone: Phone number
    - address1: Primary address line
    - address2: Secondary address line (optional)
    - city: City
    - state: State/province
    - zip_code: Postal/ZIP code
    - country: Country
    """
    
    __abstract__ = True
    
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    zip_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, default="US")


class EmployeeMixin:
    """
    Mixin for employee-specific fields.
    
    Provides:
    - employee_number: Unique employee identifier
    - hire_date: Date of hire
    - position_id: Foreign key to position/role
    - department_id: Foreign key to department
    - manager_id: Foreign key to manager (self-referential)
    """
    
    __abstract__ = True
    
    employee_number: Mapped[str] = mapped_column(
        String(50), 
        nullable=False, 
        unique=True, 
        index=True
    )
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    position_id: Mapped[Optional[UUID]] = mapped_column(nullable=True, index=True)
    department_id: Mapped[Optional[UUID]] = mapped_column(nullable=True, index=True)
    manager_id: Mapped[Optional[UUID]] = mapped_column(nullable=True, index=True)


class CustomerMixin:
    """
    Mixin for customer-specific fields.
    
    Provides:
    - customer_number: Unique customer identifier
    - customer_type: Type of customer (individual, business, etc.)
    - status: Customer status (active, inactive, etc.)
    - priority: Customer priority level (low, medium, high, vip)
    """
    
    __abstract__ = True
    
    customer_number: Mapped[str] = mapped_column(
        String(50), 
        nullable=False, 
        unique=True, 
        index=True
    )
    customer_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False, 
        default="individual",
        index=True
    )
    status: Mapped[str] = mapped_column(
        String(50), 
        nullable=False, 
        default="active",
        index=True
    )
    priority: Mapped[str] = mapped_column(
        String(50), 
        nullable=False, 
        default="medium",
        index=True
    )


class AuditMixin:
    """
    Extended audit trail mixin beyond BaseModel.
    
    Provides:
    - version: Record version for optimistic locking
    - change_reason: Reason for the change
    - changed_fields: JSON tracking which fields changed
    
    Note: This extends BaseModel's audit fields (created_by_id, updated_by_id)
    with additional tracking capabilities.
    """
    
    __abstract__ = True
    
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    change_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    changed_fields: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
