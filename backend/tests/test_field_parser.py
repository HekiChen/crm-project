"""
Tests for field definition parser.
"""

import pytest

from cli.field_parser import (
    FieldParser,
    FieldDefinition,
    FieldConstraint,
    parse_field_definitions,
)


class TestFieldParser:
    """Test suite for FieldParser."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = FieldParser()
    
    def test_parse_simple_string_field(self):
        """Test parsing a simple string field."""
        field = self.parser.parse_field("name:str")
        
        assert field.name == "name"
        assert field.type == "str"
        assert field.sqlalchemy_type == "String"
        assert field.python_type == "str"
        assert field.length == 255
        assert not field.is_nullable
        assert not field.is_unique
    
    def test_parse_integer_field(self):
        """Test parsing an integer field."""
        field = self.parser.parse_field("age:int")
        
        assert field.name == "age"
        assert field.type == "int"
        assert field.sqlalchemy_type == "Integer"
        assert field.python_type == "int"
    
    def test_parse_decimal_field(self):
        """Test parsing a decimal field."""
        field = self.parser.parse_field("price:decimal")
        
        assert field.name == "price"
        assert field.type == "decimal"
        assert field.sqlalchemy_type == "Numeric"
        assert field.python_type == "Decimal"
        assert field.precision == 15
        assert field.scale == 2
    
    def test_parse_boolean_field(self):
        """Test parsing a boolean field."""
        field = self.parser.parse_field("is_active:bool")
        
        assert field.name == "is_active"
        assert field.type == "bool"
        assert field.sqlalchemy_type == "Boolean"
        assert field.python_type == "bool"
    
    def test_parse_date_field(self):
        """Test parsing a date field."""
        field = self.parser.parse_field("birth_date:date")
        
        assert field.name == "birth_date"
        assert field.type == "date"
        assert field.sqlalchemy_type == "Date"
        assert field.python_type == "date"
    
    def test_parse_datetime_field(self):
        """Test parsing a datetime field."""
        field = self.parser.parse_field("last_login:datetime")
        
        assert field.name == "last_login"
        assert field.type == "datetime"
        assert field.sqlalchemy_type == "DateTime"
        assert field.python_type == "datetime"
    
    def test_parse_email_field(self):
        """Test parsing an email field (custom type)."""
        field = self.parser.parse_field("email:email")
        
        assert field.name == "email"
        assert field.type == "email"
        assert field.sqlalchemy_type == "EmailType"
        assert field.python_type == "str"
    
    def test_parse_phone_field(self):
        """Test parsing a phone field (custom type)."""
        field = self.parser.parse_field("phone:phone")
        
        assert field.name == "phone"
        assert field.type == "phone"
        assert field.sqlalchemy_type == "PhoneNumberType"
        assert field.python_type == "str"
    
    def test_parse_field_with_unique_constraint(self):
        """Test parsing a field with unique constraint."""
        field = self.parser.parse_field("email:str:unique")
        
        assert field.name == "email"
        assert field.is_unique
        assert len(field.constraints) == 1
        assert field.constraints[0].name == "unique"
    
    def test_parse_field_with_nullable_constraint(self):
        """Test parsing a field with nullable constraint."""
        field = self.parser.parse_field("middle_name:str:nullable")
        
        assert field.name == "middle_name"
        assert field.is_nullable
        assert len(field.constraints) == 1
        assert field.constraints[0].name == "nullable"
    
    def test_parse_field_with_index_constraint(self):
        """Test parsing a field with index constraint."""
        field = self.parser.parse_field("username:str:index")
        
        assert field.name == "username"
        assert field.is_indexed
        assert len(field.constraints) == 1
        assert field.constraints[0].name == "index"
    
    def test_parse_field_with_multiple_constraints(self):
        """Test parsing a field with multiple constraints."""
        field = self.parser.parse_field("username:str:unique:index")
        
        assert field.name == "username"
        assert field.is_unique
        assert field.is_indexed
        assert len(field.constraints) == 2
    
    def test_parse_foreign_key_with_table(self):
        """Test parsing a foreign key field with explicit table."""
        field = self.parser.parse_field("user_id:int:fk:users")
        
        assert field.name == "user_id"
        assert field.is_foreign_key
        assert field.foreign_table == "users"
    
    def test_parse_foreign_key_inferred(self):
        """Test parsing a foreign key field with inferred table."""
        field = self.parser.parse_field("user_id:int:fk")
        
        assert field.name == "user_id"
        assert field.is_foreign_key
        assert field.foreign_table == "users"
    
    def test_parse_multiple_fields(self):
        """Test parsing multiple fields."""
        fields = self.parser.parse_fields("name:str,age:int,email:str:unique")
        
        assert len(fields) == 3
        assert fields[0].name == "name"
        assert fields[1].name == "age"
        assert fields[2].name == "email"
        assert fields[2].is_unique
    
    def test_parse_empty_fields(self):
        """Test parsing empty field string."""
        fields = self.parser.parse_fields("")
        assert len(fields) == 0
        
        fields = self.parser.parse_fields(None)
        assert len(fields) == 0
    
    def test_invalid_field_format(self):
        """Test parsing invalid field format."""
        with pytest.raises(ValueError, match="Invalid field definition"):
            self.parser.parse_field("name")
    
    def test_invalid_field_name(self):
        """Test parsing invalid field name."""
        with pytest.raises(ValueError, match="Invalid field name"):
            self.parser.parse_field("123name:str")
        
        with pytest.raises(ValueError, match="Invalid field name"):
            self.parser.parse_field("my-field:str")
    
    def test_unsupported_type(self):
        """Test parsing unsupported field type."""
        with pytest.raises(ValueError, match="Unsupported field type"):
            self.parser.parse_field("data:blob")
    
    def test_validate_duplicate_names(self):
        """Test validation catches duplicate field names."""
        fields = [
            FieldDefinition("name", "str", "String", "str", [], length=255),
            FieldDefinition("name", "str", "String", "str", [], length=255),
        ]
        
        errors = self.parser.validate_fields(fields)
        assert len(errors) == 1
        assert "Duplicate field name" in errors[0]
    
    def test_validate_reserved_names(self):
        """Test validation catches reserved field names."""
        reserved_fields = ['id', 'created_at', 'updated_at', 'is_deleted']
        
        for reserved in reserved_fields:
            field = FieldDefinition(reserved, "str", "String", "str", [], length=255)
            errors = self.parser.validate_fields([field])
            assert len(errors) == 1
            assert "reserved" in errors[0].lower()
    
    def test_to_sqlalchemy_column_basic(self):
        """Test generating SQLAlchemy column definition."""
        field = FieldDefinition(
            name="name",
            type="str",
            sqlalchemy_type="String",
            python_type="str",
            constraints=[],
            length=255
        )
        
        column_def = field.to_sqlalchemy_column()
        assert "String(255)" in column_def
        assert "nullable=False" in column_def
    
    def test_to_sqlalchemy_column_with_constraints(self):
        """Test generating SQLAlchemy column with constraints."""
        field = FieldDefinition(
            name="email",
            type="str",
            sqlalchemy_type="String",
            python_type="str",
            constraints=[
                FieldConstraint("unique"),
                FieldConstraint("index"),
            ],
            length=255
        )
        
        column_def = field.to_sqlalchemy_column()
        assert "String(255)" in column_def
        assert "unique=True" in column_def
        assert "index=True" in column_def
        assert "nullable=False" in column_def
    
    def test_to_sqlalchemy_column_nullable(self):
        """Test generating nullable SQLAlchemy column."""
        field = FieldDefinition(
            name="middle_name",
            type="str",
            sqlalchemy_type="String",
            python_type="str",
            constraints=[FieldConstraint("nullable")],
            length=255
        )
        
        column_def = field.to_sqlalchemy_column()
        assert "nullable=True" in column_def
    
    def test_to_sqlalchemy_column_foreign_key(self):
        """Test generating foreign key column."""
        field = FieldDefinition(
            name="user_id",
            type="int",
            sqlalchemy_type="Integer",
            python_type="int",
            constraints=[FieldConstraint("foreign_key", "users")],
            is_foreign_key=True,
            foreign_table="users"
        )
        
        column_def = field.to_sqlalchemy_column()
        assert "Integer()" in column_def
        assert "ForeignKey('users.id')" in column_def
    
    def test_parse_field_definitions_convenience(self):
        """Test convenience function for parsing field definitions."""
        fields = parse_field_definitions("name:str,age:int,email:str:unique")
        
        assert len(fields) == 3
        assert fields[0].name == "name"
        assert fields[1].name == "age"
        assert fields[2].name == "email"
        assert fields[2].is_unique
    
    def test_parse_field_definitions_with_validation_error(self):
        """Test convenience function raises on validation error."""
        with pytest.raises(ValueError, match="Invalid field definitions"):
            parse_field_definitions("id:str")  # Reserved name
    
    def test_complex_field_definition(self):
        """Test parsing complex field definition with multiple constraints."""
        field = self.parser.parse_field("salary:decimal:nullable:index")
        
        assert field.name == "salary"
        assert field.type == "decimal"
        assert field.sqlalchemy_type == "Numeric"
        assert field.is_nullable
        assert field.is_indexed
        assert field.precision == 15
        assert field.scale == 2
    
    def test_text_field_type(self):
        """Test parsing text field (for long content)."""
        field = self.parser.parse_field("description:text")
        
        assert field.name == "description"
        assert field.sqlalchemy_type == "Text"
        assert field.python_type == "str"
    
    def test_money_field_type(self):
        """Test parsing money field."""
        field = self.parser.parse_field("price:money")
        
        assert field.name == "price"
        assert field.sqlalchemy_type == "Numeric"
        assert field.precision == 15
        assert field.scale == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
