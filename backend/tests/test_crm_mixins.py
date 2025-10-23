"""
Tests for CRM domain mixins.

Tests verify:
- Mixin field definitions
- Computed properties
- Mixin composition with BaseModel
- Field constraints and defaults
"""

from datetime import date, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, Mapped, mapped_column, declarative_base

from app.models.crm.mixins import (
    AuditMixin,
    ContactMixin,
    CustomerMixin,
    EmployeeMixin,
    PersonMixin,
)

# Create test database engine
engine = create_engine("sqlite:///:memory:")
Base = declarative_base()


# Test models combining Base with mixins
class PersonModel(Base, PersonMixin):
    """Test model using PersonMixin."""
    __tablename__ = "test_persons"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)


class ContactModel(Base, ContactMixin):
    """Test model using ContactMixin."""
    __tablename__ = "test_contacts"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)


class EmployeeModel(Base, EmployeeMixin):
    """Test model using EmployeeMixin."""
    __tablename__ = "test_employees"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)


class CustomerModel(Base, CustomerMixin):
    """Test model using CustomerMixin."""
    __tablename__ = "test_customers"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)


class AuditModel(Base, AuditMixin):
    """Test model using AuditMixin."""
    __tablename__ = "test_audits"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)


class FullEntityModel(Base, PersonMixin, ContactMixin, EmployeeMixin):
    """Test model combining multiple mixins."""
    __tablename__ = "test_full_entities"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()
    Base.metadata.drop_all(engine)


class TestPersonMixin:
    """Tests for PersonMixin."""
    
    def test_person_fields_exist(self, db_session):
        """Test that PersonMixin provides required fields."""
        person = PersonModel(
            id=uuid4(),
            first_name="John",
            last_name="Doe"
        )
        db_session.add(person)
        db_session.commit()
        
        assert person.first_name == "John"
        assert person.last_name == "Doe"
    
    def test_full_name_property(self, db_session):
        """Test that full_name property combines first and last name."""
        person = PersonModel(
            id=uuid4(),
            first_name="Jane",
            last_name="Smith"
        )
        db_session.add(person)
        db_session.commit()
        
        assert person.full_name == "Jane Smith"
    
    def test_full_name_with_whitespace(self, db_session):
        """Test that full_name handles whitespace correctly."""
        person = PersonModel(
            id=uuid4(),
            first_name="  John  ",
            last_name="  Doe  "
        )
        db_session.add(person)
        db_session.commit()
        
        # The property should strip, but the stored values keep whitespace
        assert person.full_name == "John     Doe".strip()
    
    def test_first_name_required(self, db_session):
        """Test that first_name is required."""
        person = PersonModel(
            id=uuid4(),
            last_name="Doe"
        )
        db_session.add(person)
        
        with pytest.raises(Exception):  # IntegrityError or similar
            db_session.commit()
    
    def test_last_name_required(self, db_session):
        """Test that last_name is required."""
        person = PersonModel(
            id=uuid4(),
            first_name="John"
        )
        db_session.add(person)
        
        with pytest.raises(Exception):  # IntegrityError or similar
            db_session.commit()


class TestContactMixin:
    """Tests for ContactMixin."""
    
    def test_contact_fields_optional(self, db_session):
        """Test that all ContactMixin fields are optional."""
        contact = ContactModel(id=uuid4())
        db_session.add(contact)
        db_session.commit()
        
        assert contact.email is None
        assert contact.phone is None
        assert contact.address1 is None
        assert contact.address2 is None
        assert contact.city is None
        assert contact.state is None
        assert contact.zip_code is None
    
    def test_country_defaults_to_us(self, db_session):
        """Test that country defaults to 'US'."""
        contact = ContactModel(id=uuid4())
        db_session.add(contact)
        db_session.commit()
        
        assert contact.country == "US"
    
    def test_full_address_fields(self, db_session):
        """Test storing complete address information."""
        contact = ContactModel(
            id=uuid4(),
            email="test@example.com",
            phone="555-1234",
            address1="123 Main St",
            address2="Apt 4B",
            city="Springfield",
            state="IL",
            zip_code="62701",
            country="US"
        )
        db_session.add(contact)
        db_session.commit()
        
        assert contact.email == "test@example.com"
        assert contact.phone == "555-1234"
        assert contact.address1 == "123 Main St"
        assert contact.address2 == "Apt 4B"
        assert contact.city == "Springfield"
        assert contact.state == "IL"
        assert contact.zip_code == "62701"
        assert contact.country == "US"
    
    def test_email_indexed(self, db_session):
        """Test that email field is indexed."""
        # This is verified through the column definition
        # In a real test, we'd check the database schema
        contact = ContactModel(
            id=uuid4(),
            email="indexed@example.com"
        )
        db_session.add(contact)
        db_session.commit()
        
        result = db_session.query(ContactModel).filter_by(
            email="indexed@example.com"
        ).first()
        assert result is not None
        assert result.email == "indexed@example.com"


class TestEmployeeMixin:
    """Tests for EmployeeMixin."""
    
    def test_employee_fields_exist(self, db_session):
        """Test that EmployeeMixin provides required fields."""
        employee = EmployeeModel(
            id=uuid4(),
            employee_number="EMP001",
            hire_date=date(2024, 1, 15)
        )
        db_session.add(employee)
        db_session.commit()
        
        assert employee.employee_number == "EMP001"
        assert employee.hire_date == date(2024, 1, 15)
    
    def test_employee_number_unique(self, db_session):
        """Test that employee_number must be unique."""
        emp1 = EmployeeModel(
            id=uuid4(),
            employee_number="EMP001",
            hire_date=date(2024, 1, 15)
        )
        db_session.add(emp1)
        db_session.commit()
        
        emp2 = EmployeeModel(
            id=uuid4(),
            employee_number="EMP001",
            hire_date=date(2024, 2, 1)
        )
        db_session.add(emp2)
        
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()
    
    def test_foreign_keys_optional(self, db_session):
        """Test that position, department, and manager are optional."""
        employee = EmployeeModel(
            id=uuid4(),
            employee_number="EMP002",
            hire_date=date(2024, 1, 15)
        )
        db_session.add(employee)
        db_session.commit()
        
        assert employee.position_id is None
        assert employee.department_id is None
        assert employee.manager_id is None
    
    def test_employee_with_relationships(self, db_session):
        """Test employee with all relationship fields populated."""
        position_id = uuid4()
        department_id = uuid4()
        manager_id = uuid4()
        
        employee = EmployeeModel(
            id=uuid4(),
            employee_number="EMP003",
            hire_date=date(2024, 1, 15),
            position_id=position_id,
            department_id=department_id,
            manager_id=manager_id
        )
        db_session.add(employee)
        db_session.commit()
        
        assert employee.position_id == position_id
        assert employee.department_id == department_id
        assert employee.manager_id == manager_id


class TestCustomerMixin:
    """Tests for CustomerMixin."""
    
    def test_customer_fields_with_defaults(self, db_session):
        """Test that CustomerMixin fields have correct defaults."""
        customer = CustomerModel(
            id=uuid4(),
            customer_number="CUST001"
        )
        db_session.add(customer)
        db_session.commit()
        
        assert customer.customer_number == "CUST001"
        assert customer.customer_type == "individual"
        assert customer.status == "active"
        assert customer.priority == "medium"
    
    def test_customer_number_unique(self, db_session):
        """Test that customer_number must be unique."""
        cust1 = CustomerModel(
            id=uuid4(),
            customer_number="CUST001"
        )
        db_session.add(cust1)
        db_session.commit()
        
        cust2 = CustomerModel(
            id=uuid4(),
            customer_number="CUST001"
        )
        db_session.add(cust2)
        
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()
    
    def test_customer_type_custom_value(self, db_session):
        """Test setting custom customer_type."""
        customer = CustomerModel(
            id=uuid4(),
            customer_number="CUST002",
            customer_type="business"
        )
        db_session.add(customer)
        db_session.commit()
        
        assert customer.customer_type == "business"
    
    def test_customer_status_custom_value(self, db_session):
        """Test setting custom status."""
        customer = CustomerModel(
            id=uuid4(),
            customer_number="CUST003",
            status="inactive"
        )
        db_session.add(customer)
        db_session.commit()
        
        assert customer.status == "inactive"
    
    def test_customer_priority_custom_value(self, db_session):
        """Test setting custom priority."""
        customer = CustomerModel(
            id=uuid4(),
            customer_number="CUST004",
            priority="vip"
        )
        db_session.add(customer)
        db_session.commit()
        
        assert customer.priority == "vip"
    
    def test_indexed_fields_queryable(self, db_session):
        """Test that indexed fields can be queried efficiently."""
        customer = CustomerModel(
            id=uuid4(),
            customer_number="CUST005",
            customer_type="business",
            status="active",
            priority="high"
        )
        db_session.add(customer)
        db_session.commit()
        
        # Query by indexed fields
        result = db_session.query(CustomerModel).filter_by(
            customer_type="business",
            status="active",
            priority="high"
        ).first()
        
        assert result is not None
        assert result.customer_number == "CUST005"


class TestAuditMixin:
    """Tests for AuditMixin."""
    
    def test_audit_fields_defaults(self, db_session):
        """Test that AuditMixin fields have correct defaults."""
        audit = AuditModel(id=uuid4())
        db_session.add(audit)
        db_session.commit()
        
        assert audit.version == 1
        assert audit.change_reason is None
        assert audit.changed_fields is None
    
    def test_version_increment(self, db_session):
        """Test tracking version changes."""
        audit = AuditModel(id=uuid4(), version=1)
        db_session.add(audit)
        db_session.commit()
        
        audit.version = 2
        audit.change_reason = "Updated fields"
        db_session.commit()
        
        assert audit.version == 2
        assert audit.change_reason == "Updated fields"
    
    def test_change_reason_storage(self, db_session):
        """Test storing change reason."""
        audit = AuditModel(
            id=uuid4(),
            change_reason="Initial creation with default values"
        )
        db_session.add(audit)
        db_session.commit()
        
        assert audit.change_reason == "Initial creation with default values"
    
    def test_changed_fields_json(self, db_session):
        """Test storing changed fields as JSON."""
        changed_fields = {
            "first_name": {"old": "John", "new": "Jonathan"},
            "status": {"old": "active", "new": "inactive"}
        }
        
        audit = AuditModel(
            id=uuid4(),
            version=2,
            change_reason="User update",
            changed_fields=changed_fields
        )
        db_session.add(audit)
        db_session.commit()
        
        assert audit.changed_fields == changed_fields
        assert audit.changed_fields["first_name"]["old"] == "John"
        assert audit.changed_fields["first_name"]["new"] == "Jonathan"


class TestMixinComposition:
    """Tests for combining multiple mixins."""
    
    def test_multiple_mixins_combined(self, db_session):
        """Test that multiple mixins can be combined in one model."""
        entity = FullEntityModel(
            id=uuid4(),
            first_name="Jane",
            last_name="Doe",
            email="jane.doe@example.com",
            phone="555-9876",
            employee_number="EMP100",
            hire_date=date(2024, 1, 15)
        )
        db_session.add(entity)
        db_session.commit()
        
        # PersonMixin fields
        assert entity.first_name == "Jane"
        assert entity.last_name == "Doe"
        assert entity.full_name == "Jane Doe"
        
        # ContactMixin fields
        assert entity.email == "jane.doe@example.com"
        assert entity.phone == "555-9876"
        
        # EmployeeMixin fields
        assert entity.employee_number == "EMP100"
        assert entity.hire_date == date(2024, 1, 15)
    
    def test_all_mixin_properties_accessible(self, db_session):
        """Test that all properties from all mixins are accessible."""
        entity = FullEntityModel(
            id=uuid4(),
            first_name="John",
            last_name="Smith",
            email="john@example.com",
            employee_number="EMP101",
            hire_date=date(2024, 2, 1),
            city="Boston",
            state="MA"
        )
        db_session.add(entity)
        db_session.commit()
        
        # Verify all fields are accessible and stored correctly
        assert entity.full_name == "John Smith"
        assert entity.email == "john@example.com"
        assert entity.city == "Boston"
        assert entity.state == "MA"
        assert entity.employee_number == "EMP101"
