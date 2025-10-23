"""
CRM-specific validators for Pydantic schemas.

Provides validation functions for:
- Employee numbers (format and uniqueness)
- Date ranges (hire dates, etc.)
- Email and phone validation
- Business rules (e.g., manager hierarchy)
"""

import re
from datetime import date, datetime
from typing import Any

from pydantic import field_validator, model_validator


class EmployeeNumberValidator:
    """
    Validator for employee number format.
    
    Employee numbers must follow format: EMP followed by 3-6 digits
    Examples: EMP001, EMP12345
    """
    
    EMPLOYEE_NUMBER_PATTERN = re.compile(r'^EMP\d{3,6}$')
    
    @staticmethod
    def validate_employee_number(value: str) -> str:
        """
        Validate employee number format.
        
        Args:
            value: Employee number to validate
            
        Returns:
            Validated employee number
            
        Raises:
            ValueError: If format is invalid
        """
        if not value:
            raise ValueError("Employee number is required")
        
        value = value.strip().upper()
        
        if not EmployeeNumberValidator.EMPLOYEE_NUMBER_PATTERN.match(value):
            raise ValueError(
                "Employee number must be in format 'EMP' followed by 3-6 digits (e.g., EMP001)"
            )
        
        return value


class CustomerNumberValidator:
    """
    Validator for customer number format.
    
    Customer numbers must follow format: CUST followed by 3-6 digits
    Examples: CUST001, CUST12345
    """
    
    CUSTOMER_NUMBER_PATTERN = re.compile(r'^CUST\d{3,6}$')
    
    @staticmethod
    def validate_customer_number(value: str) -> str:
        """
        Validate customer number format.
        
        Args:
            value: Customer number to validate
            
        Returns:
            Validated customer number
            
        Raises:
            ValueError: If format is invalid
        """
        if not value:
            raise ValueError("Customer number is required")
        
        value = value.strip().upper()
        
        if not CustomerNumberValidator.CUSTOMER_NUMBER_PATTERN.match(value):
            raise ValueError(
                "Customer number must be in format 'CUST' followed by 3-6 digits (e.g., CUST001)"
            )
        
        return value


class DateRangeValidator:
    """
    Validators for date ranges and date logic.
    
    Provides validation for hire dates, employment dates, etc.
    """
    
    @staticmethod
    def validate_hire_date(value: date) -> date:
        """
        Validate hire date is not in the future.
        
        Args:
            value: Hire date to validate
            
        Returns:
            Validated hire date
            
        Raises:
            ValueError: If hire date is in the future
        """
        if not value:
            raise ValueError("Hire date is required")
        
        today = date.today()
        if value > today:
            raise ValueError("Hire date cannot be in the future")
        
        # Optionally check if hire date is too far in the past
        # (e.g., company founding date)
        min_date = date(1970, 1, 1)
        if value < min_date:
            raise ValueError(f"Hire date cannot be before {min_date}")
        
        return value
    
    @staticmethod
    def validate_date_range(start_date: date, end_date: date | None) -> tuple[date, date | None]:
        """
        Validate that end date is after start date.
        
        Args:
            start_date: Start date
            end_date: End date (can be None for ongoing)
            
        Returns:
            Tuple of validated start and end dates
            
        Raises:
            ValueError: If end date is before start date
        """
        if end_date is not None and end_date < start_date:
            raise ValueError("End date must be after start date")
        
        return start_date, end_date


class EmailValidator:
    """
    Enhanced email validator for Pydantic schemas.
    
    Provides additional email validation beyond basic format checking.
    """
    
    DISPOSABLE_EMAIL_DOMAINS = {
        "tempmail.com",
        "throwaway.email",
        "guerrillamail.com",
        "10minutemail.com",
    }
    
    @staticmethod
    def validate_email_domain(value: str | None) -> str | None:
        """
        Validate email is not from a disposable domain.
        
        Args:
            value: Email address to validate
            
        Returns:
            Validated email
            
        Raises:
            ValueError: If email is from a disposable domain
        """
        if not value:
            return value
        
        email_lower = value.lower()
        domain = email_lower.split('@')[-1] if '@' in email_lower else ''
        
        if domain in EmailValidator.DISPOSABLE_EMAIL_DOMAINS:
            raise ValueError(f"Email from disposable domain '{domain}' is not allowed")
        
        return value


class PhoneValidator:
    """
    Phone number validator for Pydantic schemas.
    
    Validates phone number format and length.
    """
    
    @staticmethod
    def validate_phone_format(value: str | None) -> str | None:
        """
        Validate phone number has minimum required digits.
        
        Args:
            value: Phone number to validate
            
        Returns:
            Validated phone number
            
        Raises:
            ValueError: If phone number has insufficient digits
        """
        if not value:
            return value
        
        # Extract only digits
        digits = re.sub(r'\D', '', value)
        
        if len(digits) < 10:
            raise ValueError("Phone number must contain at least 10 digits")
        
        if len(digits) > 15:
            raise ValueError("Phone number cannot exceed 15 digits")
        
        return value


class BusinessRuleValidator:
    """
    Validators for CRM business rules.
    
    Provides validation for complex business logic.
    """
    
    @staticmethod
    def validate_manager_hierarchy(employee_id: Any, manager_id: Any | None) -> Any | None:
        """
        Validate that an employee is not their own manager.
        
        Args:
            employee_id: Employee's ID
            manager_id: Manager's ID (can be None)
            
        Returns:
            Validated manager ID
            
        Raises:
            ValueError: If employee is their own manager
        """
        if manager_id is not None and employee_id == manager_id:
            raise ValueError("Employee cannot be their own manager")
        
        return manager_id
    
    @staticmethod
    def validate_customer_priority(customer_type: str, priority: str) -> tuple[str, str]:
        """
        Validate customer priority matches customer type business rules.
        
        Business rule: Enterprise customers must have at least HIGH priority
        
        Args:
            customer_type: Type of customer
            priority: Priority level
            
        Returns:
            Tuple of validated customer type and priority
            
        Raises:
            ValueError: If priority doesn't match business rules
        """
        if customer_type == "enterprise" and priority in ["low", "medium"]:
            raise ValueError(
                "Enterprise customers must have HIGH or VIP priority"
            )
        
        return customer_type, priority
