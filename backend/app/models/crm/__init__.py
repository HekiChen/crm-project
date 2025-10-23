"""
CRM domain models and patterns.

This package contains reusable mixins, field types, and patterns
specific to CRM (Customer Relationship Management) functionality.
"""

from app.models.crm.field_types import (
    CustomerStatus,
    CustomerType,
    EmailType,
    EmploymentStatus,
    MoneyType,
    PhoneNumberType,
    Priority,
)
from app.models.crm.mixins import (
    AuditMixin,
    ContactMixin,
    CustomerMixin,
    EmployeeMixin,
    PersonMixin,
)

__all__ = [
    # Mixins
    "PersonMixin",
    "ContactMixin",
    "EmployeeMixin",
    "CustomerMixin",
    "AuditMixin",
    # Field Types
    "PhoneNumberType",
    "EmailType",
    "MoneyType",
    # Enums
    "EmploymentStatus",
    "CustomerStatus",
    "CustomerType",
    "Priority",
]
