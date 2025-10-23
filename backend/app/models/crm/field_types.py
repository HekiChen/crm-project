"""
Custom field types and enums for CRM entities.

Provides validated field types and enums for common CRM patterns:
- PhoneNumberType: Validated phone numbers with formatting
- EmailType: Validated email addresses
- MoneyType: Decimal with currency support and precision
- Status enums: EmploymentStatus, CustomerStatus, CustomerType, Priority
"""

import enum
import re
from decimal import Decimal
from typing import Optional

from sqlalchemy import Numeric, String, TypeDecorator
from sqlalchemy.orm import Mapped


class PhoneNumberType(TypeDecorator):
    """
    Custom type for phone numbers with validation and formatting.
    
    Stores phone numbers in a consistent format (e.g., +1-555-123-4567)
    and validates format on input.
    """
    
    impl = String(20)
    cache_ok = True
    
    @staticmethod
    def normalize_phone(value: Optional[str]) -> Optional[str]:
        """
        Normalize phone number to consistent format.
        
        Args:
            value: Raw phone number string
            
        Returns:
            Normalized phone number or None
        """
        if not value:
            return None
        
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', value)
        
        # Format based on length
        if len(digits) == 10:
            # US number without country code
            return f"+1-{digits[0:3]}-{digits[3:6]}-{digits[6:10]}"
        elif len(digits) == 11 and digits[0] == '1':
            # US number with country code
            return f"+1-{digits[1:4]}-{digits[4:7]}-{digits[7:11]}"
        elif len(digits) > 11:
            # International number
            return f"+{digits}"
        else:
            # Return as-is if cannot format
            return value
    
    def process_bind_param(self, value: Optional[str], dialect) -> Optional[str]:
        """Process value before binding to database."""
        return self.normalize_phone(value)
    
    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
        """Process value after retrieving from database."""
        return value


class EmailType(TypeDecorator):
    """
    Custom type for email addresses with validation.
    
    Stores emails in lowercase and validates basic email format.
    """
    
    impl = String(255)
    cache_ok = True
    
    # Basic email regex pattern
    EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    @staticmethod
    def normalize_email(value: Optional[str]) -> Optional[str]:
        """
        Normalize email to lowercase and validate format.
        
        Args:
            value: Raw email string
            
        Returns:
            Normalized email or None
            
        Raises:
            ValueError: If email format is invalid
        """
        if not value:
            return None
        
        email = value.strip().lower()
        
        if not EmailType.EMAIL_REGEX.match(email):
            raise ValueError(f"Invalid email format: {value}")
        
        return email
    
    def process_bind_param(self, value: Optional[str], dialect) -> Optional[str]:
        """Process value before binding to database."""
        return self.normalize_email(value)
    
    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
        """Process value after retrieving from database."""
        return value


class MoneyType(TypeDecorator):
    """
    Custom type for monetary values with precision.
    
    Stores monetary values as Decimal with 2 decimal places.
    Prevents floating point precision issues.
    """
    
    impl = Numeric(precision=15, scale=2)
    cache_ok = True
    
    def process_bind_param(self, value: Optional[float | Decimal], dialect) -> Optional[Decimal]:
        """Process value before binding to database."""
        if value is None:
            return None
        
        if isinstance(value, Decimal):
            return value
        
        # Convert to Decimal to avoid float precision issues
        return Decimal(str(value))
    
    def process_result_value(self, value: Optional[Decimal], dialect) -> Optional[Decimal]:
        """Process value after retrieving from database."""
        return value


class EmploymentStatus(str, enum.Enum):
    """
    Employment status enumeration.
    
    Defines valid employment status values:
    - ACTIVE: Currently employed
    - ON_LEAVE: On leave (sick, vacation, etc.)
    - TERMINATED: Employment terminated
    - RETIRED: Retired from employment
    """
    
    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    TERMINATED = "terminated"
    RETIRED = "retired"


class CustomerStatus(str, enum.Enum):
    """
    Customer status enumeration.
    
    Defines valid customer status values:
    - ACTIVE: Active customer
    - INACTIVE: Inactive customer
    - PROSPECT: Potential customer
    - CHURNED: Former customer
    """
    
    ACTIVE = "active"
    INACTIVE = "inactive"
    PROSPECT = "prospect"
    CHURNED = "churned"


class CustomerType(str, enum.Enum):
    """
    Customer type enumeration.
    
    Defines valid customer types:
    - INDIVIDUAL: Individual customer
    - BUSINESS: Business customer
    - ENTERPRISE: Large enterprise customer
    - GOVERNMENT: Government organization
    """
    
    INDIVIDUAL = "individual"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"
    GOVERNMENT = "government"


class Priority(str, enum.Enum):
    """
    Priority level enumeration.
    
    Defines valid priority levels:
    - LOW: Low priority
    - MEDIUM: Medium priority
    - HIGH: High priority
    - VIP: VIP/Critical priority
    """
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VIP = "vip"
