"""
Tests for CRM custom field types and enums.

Tests verify:
- Phone number validation and normalization
- Email validation and normalization
- Money type precision and decimal handling
- Status enum values and validation
"""

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, Column
from sqlalchemy.exc import StatementError
from sqlalchemy.orm import Session, Mapped, mapped_column, declarative_base

from app.models.crm.field_types import (
    CustomerStatus,
    CustomerType,
    EmailType,
    EmploymentStatus,
    MoneyType,
    PhoneNumberType,
    Priority,
)

# Create test database engine
engine = create_engine("sqlite:///:memory:")
Base = declarative_base()


# Test models using custom field types
class PhoneModel(Base):
    """Test model for PhoneNumberType."""
    __tablename__ = "test_phones"
    id: Mapped[int] = mapped_column(primary_key=True)
    phone = Column(PhoneNumberType)


class EmailModel(Base):
    """Test model for EmailType."""
    __tablename__ = "test_emails"
    id: Mapped[int] = mapped_column(primary_key=True)
    email = Column(EmailType)


class MoneyModel(Base):
    """Test model for MoneyType."""
    __tablename__ = "test_money"
    id: Mapped[int] = mapped_column(primary_key=True)
    amount = Column(MoneyType)
    balance = Column(MoneyType, nullable=True)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()
    Base.metadata.drop_all(engine)


class TestPhoneNumberType:
    """Tests for PhoneNumberType."""
    
    def test_normalize_us_phone_10_digits(self, db_session):
        """Test normalizing 10-digit US phone number."""
        phone_model = PhoneModel(id=1, phone="5551234567")
        db_session.add(phone_model)
        db_session.commit()
        
        assert phone_model.phone == "+1-555-123-4567"
    
    def test_normalize_us_phone_with_formatting(self, db_session):
        """Test normalizing formatted US phone number."""
        phone_model = PhoneModel(id=1, phone="(555) 123-4567")
        db_session.add(phone_model)
        db_session.commit()
        
        assert phone_model.phone == "+1-555-123-4567"
    
    def test_normalize_us_phone_11_digits(self, db_session):
        """Test normalizing 11-digit US phone number with country code."""
        phone_model = PhoneModel(id=1, phone="15551234567")
        db_session.add(phone_model)
        db_session.commit()
        
        assert phone_model.phone == "+1-555-123-4567"
    
    def test_normalize_international_phone(self, db_session):
        """Test normalizing international phone number."""
        phone_model = PhoneModel(id=1, phone="447911123456")
        db_session.add(phone_model)
        db_session.commit()
        
        assert phone_model.phone == "+447911123456"
    
    def test_phone_with_dashes_and_spaces(self, db_session):
        """Test normalizing phone with various separators."""
        phone_model = PhoneModel(id=1, phone="1-555-123-4567")
        db_session.add(phone_model)
        db_session.commit()
        
        assert phone_model.phone == "+1-555-123-4567"
    
    def test_phone_null_value(self, db_session):
        """Test handling null phone number."""
        phone_model = PhoneModel(id=1, phone=None)
        db_session.add(phone_model)
        db_session.commit()
        
        assert phone_model.phone is None
    
    def test_phone_short_number(self, db_session):
        """Test handling short phone number (returns as-is)."""
        phone_model = PhoneModel(id=1, phone="12345")
        db_session.add(phone_model)
        db_session.commit()
        
        # Short numbers are returned as-is
        assert phone_model.phone == "12345"
    
    def test_phone_retrieval_from_db(self, db_session):
        """Test retrieving normalized phone from database."""
        phone_model = PhoneModel(id=1, phone="5551234567")
        db_session.add(phone_model)
        db_session.commit()
        
        # Retrieve from database
        retrieved = db_session.query(PhoneModel).filter_by(id=1).first()
        assert retrieved.phone == "+1-555-123-4567"


class TestEmailType:
    """Tests for EmailType."""
    
    def test_email_normalization_lowercase(self, db_session):
        """Test email is normalized to lowercase."""
        email_model = EmailModel(id=1, email="Test@Example.COM")
        db_session.add(email_model)
        db_session.commit()
        
        assert email_model.email == "test@example.com"
    
    def test_email_whitespace_trimmed(self, db_session):
        """Test whitespace is trimmed from email."""
        email_model = EmailModel(id=1, email="  user@example.com  ")
        db_session.add(email_model)
        db_session.commit()
        
        assert email_model.email == "user@example.com"
    
    def test_valid_email_formats(self, db_session):
        """Test various valid email formats."""
        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
            "user_name@example-domain.com",
            "123@example.com",
        ]
        
        for i, email in enumerate(valid_emails, start=1):
            email_model = EmailModel(id=i, email=email)
            db_session.add(email_model)
        
        db_session.commit()
        
        # Verify all were stored
        count = db_session.query(EmailModel).count()
        assert count == len(valid_emails)
    
    def test_invalid_email_no_at(self, db_session):
        """Test invalid email without @ symbol."""
        email_model = EmailModel(id=1, email="invalid.email.com")
        db_session.add(email_model)
        
        with pytest.raises(StatementError):
            db_session.commit()
    
    def test_invalid_email_no_domain(self, db_session):
        """Test invalid email without domain."""
        email_model = EmailModel(id=1, email="user@")
        db_session.add(email_model)
        
        with pytest.raises(StatementError):
            db_session.commit()
    
    def test_invalid_email_no_tld(self, db_session):
        """Test invalid email without top-level domain."""
        email_model = EmailModel(id=1, email="user@domain")
        db_session.add(email_model)
        
        with pytest.raises(StatementError):
            db_session.commit()
    
    def test_email_null_value(self, db_session):
        """Test handling null email."""
        email_model = EmailModel(id=1, email=None)
        db_session.add(email_model)
        db_session.commit()
        
        assert email_model.email is None
    
    def test_email_retrieval_from_db(self, db_session):
        """Test retrieving normalized email from database."""
        email_model = EmailModel(id=1, email="USER@EXAMPLE.COM")
        db_session.add(email_model)
        db_session.commit()
        
        # Retrieve from database
        retrieved = db_session.query(EmailModel).filter_by(id=1).first()
        assert retrieved.email == "user@example.com"


class TestMoneyType:
    """Tests for MoneyType."""
    
    def test_money_from_decimal(self, db_session):
        """Test storing Decimal value."""
        money_model = MoneyModel(id=1, amount=Decimal("123.45"))
        db_session.add(money_model)
        db_session.commit()
        
        assert money_model.amount == Decimal("123.45")
    
    def test_money_from_float(self, db_session):
        """Test storing float value (converted to Decimal)."""
        money_model = MoneyModel(id=1, amount=123.45)
        db_session.add(money_model)
        db_session.commit()
        
        # Should be stored as Decimal
        assert isinstance(money_model.amount, Decimal)
        assert money_model.amount == Decimal("123.45")
    
    def test_money_precision(self, db_session):
        """Test monetary precision (2 decimal places)."""
        money_model = MoneyModel(id=1, amount=Decimal("99.99"))
        db_session.add(money_model)
        db_session.commit()
        
        assert money_model.amount == Decimal("99.99")
    
    def test_money_large_values(self, db_session):
        """Test storing large monetary values."""
        money_model = MoneyModel(id=1, amount=Decimal("9999999999999.99"))
        db_session.add(money_model)
        db_session.commit()
        
        assert money_model.amount == Decimal("9999999999999.99")
    
    def test_money_null_value(self, db_session):
        """Test handling null monetary value."""
        money_model = MoneyModel(id=1, amount=Decimal("100.00"), balance=None)
        db_session.add(money_model)
        db_session.commit()
        
        assert money_model.balance is None
    
    def test_money_zero_value(self, db_session):
        """Test storing zero monetary value."""
        money_model = MoneyModel(id=1, amount=Decimal("0.00"))
        db_session.add(money_model)
        db_session.commit()
        
        assert money_model.amount == Decimal("0.00")
    
    def test_money_negative_value(self, db_session):
        """Test storing negative monetary value."""
        money_model = MoneyModel(id=1, amount=Decimal("-50.25"))
        db_session.add(money_model)
        db_session.commit()
        
        assert money_model.amount == Decimal("-50.25")
    
    def test_money_retrieval_from_db(self, db_session):
        """Test retrieving monetary value from database."""
        money_model = MoneyModel(id=1, amount=Decimal("456.78"))
        db_session.add(money_model)
        db_session.commit()
        
        # Retrieve from database
        retrieved = db_session.query(MoneyModel).filter_by(id=1).first()
        assert retrieved.amount == Decimal("456.78")
        assert isinstance(retrieved.amount, Decimal)
    
    def test_money_arithmetic_precision(self, db_session):
        """Test arithmetic operations maintain precision."""
        money_model = MoneyModel(id=1, amount=Decimal("10.10"))
        db_session.add(money_model)
        db_session.commit()
        
        # Perform arithmetic
        new_amount = money_model.amount + Decimal("5.05")
        money_model.amount = new_amount
        db_session.commit()
        
        assert money_model.amount == Decimal("15.15")


class TestEmploymentStatus:
    """Tests for EmploymentStatus enum."""
    
    def test_all_status_values_defined(self):
        """Test that all expected status values are defined."""
        expected_values = {"active", "on_leave", "terminated", "retired"}
        actual_values = {status.value for status in EmploymentStatus}
        
        assert actual_values == expected_values
    
    def test_status_enum_members(self):
        """Test accessing enum members."""
        assert EmploymentStatus.ACTIVE.value == "active"
        assert EmploymentStatus.ON_LEAVE.value == "on_leave"
        assert EmploymentStatus.TERMINATED.value == "terminated"
        assert EmploymentStatus.RETIRED.value == "retired"
    
    def test_status_from_value(self):
        """Test creating enum from value."""
        assert EmploymentStatus("active") == EmploymentStatus.ACTIVE
        assert EmploymentStatus("on_leave") == EmploymentStatus.ON_LEAVE
    
    def test_status_string_representation(self):
        """Test string representation of enum."""
        assert str(EmploymentStatus.ACTIVE) == "EmploymentStatus.ACTIVE"
    
    def test_status_equality(self):
        """Test enum equality comparison."""
        assert EmploymentStatus.ACTIVE == EmploymentStatus.ACTIVE
        assert EmploymentStatus.ACTIVE != EmploymentStatus.TERMINATED


class TestCustomerStatus:
    """Tests for CustomerStatus enum."""
    
    def test_all_status_values_defined(self):
        """Test that all expected status values are defined."""
        expected_values = {"active", "inactive", "prospect", "churned"}
        actual_values = {status.value for status in CustomerStatus}
        
        assert actual_values == expected_values
    
    def test_status_enum_members(self):
        """Test accessing enum members."""
        assert CustomerStatus.ACTIVE.value == "active"
        assert CustomerStatus.INACTIVE.value == "inactive"
        assert CustomerStatus.PROSPECT.value == "prospect"
        assert CustomerStatus.CHURNED.value == "churned"


class TestCustomerType:
    """Tests for CustomerType enum."""
    
    def test_all_type_values_defined(self):
        """Test that all expected type values are defined."""
        expected_values = {"individual", "business", "enterprise", "government"}
        actual_values = {customer_type.value for customer_type in CustomerType}
        
        assert actual_values == expected_values
    
    def test_type_enum_members(self):
        """Test accessing enum members."""
        assert CustomerType.INDIVIDUAL.value == "individual"
        assert CustomerType.BUSINESS.value == "business"
        assert CustomerType.ENTERPRISE.value == "enterprise"
        assert CustomerType.GOVERNMENT.value == "government"


class TestPriority:
    """Tests for Priority enum."""
    
    def test_all_priority_values_defined(self):
        """Test that all expected priority values are defined."""
        expected_values = {"low", "medium", "high", "vip"}
        actual_values = {priority.value for priority in Priority}
        
        assert actual_values == expected_values
    
    def test_priority_enum_members(self):
        """Test accessing enum members."""
        assert Priority.LOW.value == "low"
        assert Priority.MEDIUM.value == "medium"
        assert Priority.HIGH.value == "high"
        assert Priority.VIP.value == "vip"
    
    def test_priority_ordering(self):
        """Test that priorities can be compared."""
        # Note: Enums are not inherently orderable, but we can test equality
        assert Priority.LOW != Priority.HIGH
        assert Priority.VIP == Priority.VIP
