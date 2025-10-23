"""
Tests for CRM validators.

Tests verify:
- Employee number format validation
- Customer number format validation
- Date range validation
- Email and phone validation
- Business rule validation
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.schemas.crm.validators import (
    BusinessRuleValidator,
    CustomerNumberValidator,
    DateRangeValidator,
    EmailValidator,
    EmployeeNumberValidator,
    PhoneValidator,
)


class TestEmployeeNumberValidator:
    """Tests for EmployeeNumberValidator."""
    
    def test_valid_employee_numbers(self):
        """Test valid employee number formats."""
        valid_numbers = [
            "EMP001",
            "EMP123",
            "EMP999",
            "EMP1234",
            "EMP12345",
            "EMP123456",
        ]
        
        for number in valid_numbers:
            result = EmployeeNumberValidator.validate_employee_number(number)
            assert result == number
    
    def test_employee_number_lowercase_converted(self):
        """Test that lowercase employee numbers are converted to uppercase."""
        result = EmployeeNumberValidator.validate_employee_number("emp001")
        assert result == "EMP001"
    
    def test_employee_number_with_whitespace(self):
        """Test that whitespace is trimmed."""
        result = EmployeeNumberValidator.validate_employee_number("  EMP001  ")
        assert result == "EMP001"
    
    def test_invalid_employee_number_too_short(self):
        """Test that employee numbers with too few digits are rejected."""
        with pytest.raises(ValueError, match="must be in format"):
            EmployeeNumberValidator.validate_employee_number("EMP12")
    
    def test_invalid_employee_number_too_long(self):
        """Test that employee numbers with too many digits are rejected."""
        with pytest.raises(ValueError, match="must be in format"):
            EmployeeNumberValidator.validate_employee_number("EMP1234567")
    
    def test_invalid_employee_number_wrong_prefix(self):
        """Test that wrong prefix is rejected."""
        with pytest.raises(ValueError, match="must be in format"):
            EmployeeNumberValidator.validate_employee_number("EMPL001")
    
    def test_invalid_employee_number_no_digits(self):
        """Test that employee number without digits is rejected."""
        with pytest.raises(ValueError, match="must be in format"):
            EmployeeNumberValidator.validate_employee_number("EMP")
    
    def test_employee_number_required(self):
        """Test that empty employee number is rejected."""
        with pytest.raises(ValueError, match="required"):
            EmployeeNumberValidator.validate_employee_number("")


class TestCustomerNumberValidator:
    """Tests for CustomerNumberValidator."""
    
    def test_valid_customer_numbers(self):
        """Test valid customer number formats."""
        valid_numbers = [
            "CUST001",
            "CUST123",
            "CUST999",
            "CUST1234",
            "CUST12345",
            "CUST123456",
        ]
        
        for number in valid_numbers:
            result = CustomerNumberValidator.validate_customer_number(number)
            assert result == number
    
    def test_customer_number_lowercase_converted(self):
        """Test that lowercase customer numbers are converted to uppercase."""
        result = CustomerNumberValidator.validate_customer_number("cust001")
        assert result == "CUST001"
    
    def test_customer_number_with_whitespace(self):
        """Test that whitespace is trimmed."""
        result = CustomerNumberValidator.validate_customer_number("  CUST001  ")
        assert result == "CUST001"
    
    def test_invalid_customer_number_too_short(self):
        """Test that customer numbers with too few digits are rejected."""
        with pytest.raises(ValueError, match="must be in format"):
            CustomerNumberValidator.validate_customer_number("CUST12")
    
    def test_invalid_customer_number_wrong_prefix(self):
        """Test that wrong prefix is rejected."""
        with pytest.raises(ValueError, match="must be in format"):
            CustomerNumberValidator.validate_customer_number("CUSTOMER001")
    
    def test_customer_number_required(self):
        """Test that empty customer number is rejected."""
        with pytest.raises(ValueError, match="required"):
            CustomerNumberValidator.validate_customer_number("")


class TestDateRangeValidator:
    """Tests for DateRangeValidator."""
    
    def test_valid_hire_date_today(self):
        """Test that today is a valid hire date."""
        today = date.today()
        result = DateRangeValidator.validate_hire_date(today)
        assert result == today
    
    def test_valid_hire_date_past(self):
        """Test that past dates are valid hire dates."""
        past_date = date.today() - timedelta(days=365)
        result = DateRangeValidator.validate_hire_date(past_date)
        assert result == past_date
    
    def test_invalid_hire_date_future(self):
        """Test that future dates are rejected."""
        future_date = date.today() + timedelta(days=1)
        
        with pytest.raises(ValueError, match="cannot be in the future"):
            DateRangeValidator.validate_hire_date(future_date)
    
    def test_invalid_hire_date_too_old(self):
        """Test that dates before 1970 are rejected."""
        old_date = date(1969, 12, 31)
        
        with pytest.raises(ValueError, match="cannot be before"):
            DateRangeValidator.validate_hire_date(old_date)
    
    def test_valid_hire_date_1970(self):
        """Test that 1970-01-01 is the minimum valid hire date."""
        min_date = date(1970, 1, 1)
        result = DateRangeValidator.validate_hire_date(min_date)
        assert result == min_date
    
    def test_valid_date_range(self):
        """Test valid date range with end date after start date."""
        start = date(2024, 1, 1)
        end = date(2024, 12, 31)
        
        result_start, result_end = DateRangeValidator.validate_date_range(start, end)
        assert result_start == start
        assert result_end == end
    
    def test_valid_date_range_no_end(self):
        """Test valid date range with no end date (ongoing)."""
        start = date(2024, 1, 1)
        
        result_start, result_end = DateRangeValidator.validate_date_range(start, None)
        assert result_start == start
        assert result_end is None
    
    def test_invalid_date_range_end_before_start(self):
        """Test that end date before start date is rejected."""
        start = date(2024, 12, 31)
        end = date(2024, 1, 1)
        
        with pytest.raises(ValueError, match="End date must be after start date"):
            DateRangeValidator.validate_date_range(start, end)
    
    def test_valid_date_range_same_day(self):
        """Test valid date range where start and end are the same day."""
        same_date = date(2024, 1, 1)
        
        # Same day should be valid (not before)
        result_start, result_end = DateRangeValidator.validate_date_range(same_date, same_date)
        assert result_start == same_date
        assert result_end == same_date


class TestEmailValidator:
    """Tests for EmailValidator."""
    
    def test_valid_email_accepted(self):
        """Test that valid emails are accepted."""
        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
        ]
        
        for email in valid_emails:
            result = EmailValidator.validate_email_domain(email)
            assert result == email
    
    def test_disposable_email_rejected(self):
        """Test that disposable email domains are rejected."""
        disposable_emails = [
            "user@tempmail.com",
            "test@throwaway.email",
            "spam@guerrillamail.com",
            "temp@10minutemail.com",
        ]
        
        for email in disposable_emails:
            with pytest.raises(ValueError, match="disposable domain"):
                EmailValidator.validate_email_domain(email)
    
    def test_email_case_insensitive(self):
        """Test that email domain checking is case-insensitive."""
        with pytest.raises(ValueError, match="disposable domain"):
            EmailValidator.validate_email_domain("user@TempMail.COM")
    
    def test_empty_email_allowed(self):
        """Test that empty email is allowed (for optional fields)."""
        result = EmailValidator.validate_email_domain("")
        assert result == ""
    
    def test_none_email_allowed(self):
        """Test that None email is allowed (for optional fields)."""
        result = EmailValidator.validate_email_domain(None)
        assert result is None


class TestPhoneValidator:
    """Tests for PhoneValidator."""
    
    def test_valid_phone_10_digits(self):
        """Test that 10-digit phone is valid."""
        result = PhoneValidator.validate_phone_format("555-123-4567")
        assert result == "555-123-4567"
    
    def test_valid_phone_11_digits(self):
        """Test that 11-digit phone is valid."""
        result = PhoneValidator.validate_phone_format("1-555-123-4567")
        assert result == "1-555-123-4567"
    
    def test_valid_phone_international(self):
        """Test that international phone is valid."""
        result = PhoneValidator.validate_phone_format("+44 7911 123456")
        assert result == "+44 7911 123456"
    
    def test_invalid_phone_too_short(self):
        """Test that phone with less than 10 digits is rejected."""
        with pytest.raises(ValueError, match="at least 10 digits"):
            PhoneValidator.validate_phone_format("555-1234")
    
    def test_invalid_phone_too_long(self):
        """Test that phone with more than 15 digits is rejected."""
        with pytest.raises(ValueError, match="cannot exceed 15 digits"):
            PhoneValidator.validate_phone_format("1234567890123456")
    
    def test_phone_with_special_characters(self):
        """Test that phone with special characters is accepted (digits counted)."""
        result = PhoneValidator.validate_phone_format("(555) 123-4567")
        assert result == "(555) 123-4567"
    
    def test_empty_phone_allowed(self):
        """Test that empty phone is allowed (for optional fields)."""
        result = PhoneValidator.validate_phone_format("")
        assert result == ""
    
    def test_none_phone_allowed(self):
        """Test that None phone is allowed (for optional fields)."""
        result = PhoneValidator.validate_phone_format(None)
        assert result is None


class TestBusinessRuleValidator:
    """Tests for BusinessRuleValidator."""
    
    def test_valid_manager_different_from_employee(self):
        """Test that different employee and manager IDs are valid."""
        employee_id = uuid4()
        manager_id = uuid4()
        
        result = BusinessRuleValidator.validate_manager_hierarchy(employee_id, manager_id)
        assert result == manager_id
    
    def test_valid_manager_none(self):
        """Test that None manager ID is valid (no manager)."""
        employee_id = uuid4()
        
        result = BusinessRuleValidator.validate_manager_hierarchy(employee_id, None)
        assert result is None
    
    def test_invalid_manager_same_as_employee(self):
        """Test that employee cannot be their own manager."""
        employee_id = uuid4()
        
        with pytest.raises(ValueError, match="cannot be their own manager"):
            BusinessRuleValidator.validate_manager_hierarchy(employee_id, employee_id)
    
    def test_valid_customer_priority_individual_low(self):
        """Test that individual customers can have low priority."""
        result_type, result_priority = BusinessRuleValidator.validate_customer_priority(
            "individual", "low"
        )
        assert result_type == "individual"
        assert result_priority == "low"
    
    def test_valid_customer_priority_enterprise_high(self):
        """Test that enterprise customers can have high priority."""
        result_type, result_priority = BusinessRuleValidator.validate_customer_priority(
            "enterprise", "high"
        )
        assert result_type == "enterprise"
        assert result_priority == "high"
    
    def test_valid_customer_priority_enterprise_vip(self):
        """Test that enterprise customers can have VIP priority."""
        result_type, result_priority = BusinessRuleValidator.validate_customer_priority(
            "enterprise", "vip"
        )
        assert result_type == "enterprise"
        assert result_priority == "vip"
    
    def test_invalid_customer_priority_enterprise_low(self):
        """Test that enterprise customers cannot have low priority."""
        with pytest.raises(ValueError, match="must have HIGH or VIP priority"):
            BusinessRuleValidator.validate_customer_priority("enterprise", "low")
    
    def test_invalid_customer_priority_enterprise_medium(self):
        """Test that enterprise customers cannot have medium priority."""
        with pytest.raises(ValueError, match="must have HIGH or VIP priority"):
            BusinessRuleValidator.validate_customer_priority("enterprise", "medium")
    
    def test_valid_customer_priority_business_medium(self):
        """Test that business customers can have medium priority."""
        result_type, result_priority = BusinessRuleValidator.validate_customer_priority(
            "business", "medium"
        )
        assert result_type == "business"
        assert result_priority == "medium"
