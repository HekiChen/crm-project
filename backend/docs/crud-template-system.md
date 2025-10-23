# CRUD Template System

The CRUD Template System is an automated code generation tool that scaffolds complete CRUD APIs for CRM entities. It generates database models, service layers, FastAPI routers, Pydantic schemas, comprehensive tests, and database migrations with a single command.

## Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Field Type Syntax](#field-type-syntax)
- [Domain Patterns](#domain-patterns)
- [CLI Options](#cli-options)
- [Examples](#examples)
- [Customization](#customization)
- [Generated Files](#generated-files)
- [Troubleshooting](#troubleshooting)

## Quick Start

Generate a complete CRUD API for a `User` entity:

```bash
crud-generate user --fields "name:str,email:str:unique,age:int"
```

This creates:
- ✅ Database model with SQLAlchemy
- ✅ Service layer with business logic
- ✅ FastAPI router with CRUD endpoints
- ✅ Pydantic schemas for validation
- ✅ Comprehensive test suites
- ✅ Database migration file
- ✅ Automatic router registration

## Installation

The CRUD generator is included in the backend CLI tools. Ensure you have the backend environment activated:

```bash
# Activate conda environment
conda activate crm-backend

# Verify installation
crud-generate --help
```

## Basic Usage

### Generate an Entity

```bash
crud-generate <entity_name> [OPTIONS]
```

**Example:**
```bash
crud-generate product --fields "name:str,price:decimal,stock:int"
```

### Preview Without Creating Files

Use `--dry-run` to see what would be generated:

```bash
crud-generate product --fields "name:str,price:decimal" --dry-run
```

### Specify Output Directory

```bash
crud-generate user --fields "name:str" --output-dir /path/to/backend
```

If not specified, the tool auto-detects the backend directory.

## Field Type Syntax

Fields are defined using the format: `name:type:constraints`

### Supported Types

| Type | SQLAlchemy | Description | Example |
|------|-----------|-------------|---------|
| `str` | String(255) | Variable-length string | `name:str` |
| `text` | Text | Large text field | `description:text` |
| `int` | Integer | Integer number | `quantity:int` |
| `float` | Float | Floating-point number | `rating:float` |
| `decimal` | Numeric(10,2) | Precise decimal (money) | `price:decimal` |
| `money` | Numeric(10,2) | Alias for decimal | `salary:money` |
| `bool` | Boolean | True/False value | `is_active:bool` |
| `date` | Date | Date without time | `birth_date:date` |
| `datetime` | DateTime | Date and time | `created_at:datetime` |
| `time` | Time | Time without date | `start_time:time` |
| `uuid` | UUID | Universally unique ID | `external_id:uuid` |
| `json` | JSON | JSON data | `metadata:json` |
| `email` | String(255) | Email address | `email:email` |
| `phone` | String(20) | Phone number | `phone:phone` |
| `fk` | ForeignKey | Foreign key reference | `user_id:fk:users` |

### Field Constraints

Constraints modify field behavior:

| Constraint | Description | Example |
|------------|-------------|---------|
| `unique` | Ensures uniqueness | `email:str:unique` |
| `nullable` | Allows NULL values | `middle_name:str:nullable` |
| `index` | Creates database index | `username:str:index` |
| `primary` | Primary key (auto for id) | `id:uuid:primary` |

### Multiple Constraints

Combine multiple constraints with colons:

```bash
--fields "username:str:unique:index,bio:text:nullable"
```

### Foreign Keys

Reference other tables:

```bash
# Explicit table reference
--fields "user_id:fk:users"

# Inferred from field name (user_id → users table)
--fields "user_id:fk"
```

## Domain Patterns

Domain patterns apply predefined field sets and behaviors for common CRM entities.

### Available Domains

#### Generic (Default)

No special fields. Use for custom entities.

```bash
crud-generate task --fields "title:str,status:str"
```

#### Employee Domain

Optimized for employee management with CRM-specific fields:

```bash
crud-generate employee --domain employee --fields "first_name:str,last_name:str,hire_date:date"
```

Additional auto-generated fields:
- `position_id` (Foreign key to positions)
- `department_id` (Foreign key to departments)
- `manager_id` (Self-referential foreign key)
- `is_active` (Boolean status)

#### Customer Domain

Optimized for customer management:

```bash
crud-generate customer --domain customer --fields "first_name:str,last_name:str,email:str:unique"
```

Additional auto-generated fields:
- `customer_type` (Enum: individual, business)
- `account_status` (Enum: active, inactive, suspended)
- `tags` (JSON for categorization)

## CLI Options

### Entity Name (Required)

The name of the entity to generate (e.g., `user`, `product`, `order`).

**Rules:**
- Must be a valid Python identifier
- Cannot be a reserved Python keyword (`class`, `def`, etc.)
- Cannot be a reserved name (`model`, `schema`, `service`, etc.)
- Use singular form (e.g., `product` not `products`)

### `--fields` / `-f`

Define custom fields for the entity.

**Format:** `"field1:type,field2:type:constraint,field3:type:constraint1:constraint2"`

**Example:**
```bash
--fields "name:str,email:str:unique,age:int,bio:text:nullable"
```

### `--soft-delete` / `--no-soft-delete`

Enable or disable soft delete functionality (default: enabled).

When enabled, adds:
- `is_deleted` (Boolean, default False)
- `deleted_at` (DateTime, nullable)

**Example:**
```bash
crud-generate task --no-soft-delete
```

### `--timestamps` / `--no-timestamps`

Enable or disable automatic timestamps (default: enabled).

When enabled, adds:
- `created_at` (DateTime, auto-set on creation)
- `updated_at` (DateTime, auto-updated on modification)

**Example:**
```bash
crud-generate log --no-timestamps
```

### `--audit` / `--no-audit`

Enable or disable audit trail fields (default: enabled).

When enabled, adds:
- `created_by_id` (Foreign key to users)
- `updated_by_id` (Foreign key to users)

**Example:**
```bash
crud-generate note --no-audit
```

### `--domain` / `-d`

Specify the CRM domain pattern.

**Values:** `employee`, `customer`, `generic`

**Example:**
```bash
crud-generate staff --domain employee
```

### `--output-dir` / `-o`

Specify the output directory (default: auto-detect).

**Example:**
```bash
crud-generate user --output-dir ./backend
```

### `--dry-run`

Preview what would be generated without creating files.

**Example:**
```bash
crud-generate product --fields "name:str,price:decimal" --dry-run
```

## Examples

### Example 1: Simple Entity

Generate a basic `Product` entity:

```bash
crud-generate product --fields "name:str,description:text,price:decimal,stock:int"
```

### Example 2: Entity with Constraints

Generate a `User` with unique email and indexed username:

```bash
crud-generate user --fields "username:str:index,email:str:unique,full_name:str,bio:text:nullable"
```

### Example 3: Entity with Foreign Keys

Generate an `Order` that references users and products:

```bash
crud-generate order --fields "user_id:fk:users,product_id:fk:products,quantity:int,total:decimal"
```

### Example 4: Employee with CRM Domain

Generate an employee entity with CRM-specific fields:

```bash
crud-generate employee --domain employee \
  --fields "first_name:str,last_name:str,email:str:unique,hire_date:date,salary:money"
```

### Example 5: Minimal Entity (No Timestamps/Audit)

Generate a simple log entity without timestamps or audit fields:

```bash
crud-generate simple_log \
  --fields "message:text,level:str" \
  --no-timestamps \
  --no-audit
```

### Example 6: Customer with Relationships

Generate a customer entity with contact information:

```bash
crud-generate customer --domain customer \
  --fields "first_name:str,last_name:str,email:str:unique,phone:phone,address:text:nullable"
```

## Customization

### Customizing Templates

Templates are located in `backend/templates/crud/`:

- `model.py.jinja2` - SQLAlchemy model
- `service.py.jinja2` - Service layer
- `schemas.py.jinja2` - Pydantic schemas
- `api.py.jinja2` - FastAPI router
- `test_api.py.jinja2` - API tests
- `test_service.py.jinja2` - Service tests
- `migration.py.jinja2` - Alembic migration

To customize:

1. Copy the template you want to modify
2. Edit the Jinja2 template
3. The changes will apply to all future generations

### Template Variables

Templates have access to:

```python
{
    'entity_name': 'product',           # Singular entity name
    'entity_plural': 'products',        # Plural entity name
    'entity_class': 'Product',          # PascalCase class name
    'entity_upper': 'PRODUCT',          # Uppercase constant
    'fields': [FieldDefinition(...)],   # List of field objects
    'soft_delete': True,                # Boolean flags
    'timestamps': True,
    'audit': True,
    'domain': 'employee',               # Domain pattern
    'table_name': 'products',           # Database table name
}
```

### Adding Custom Field Types

Edit `backend/cli/field_parser.py` to add new type mappings:

```python
TYPE_MAPPINGS = {
    "your_type": "sa.YourSQLAlchemyType",
    # ... existing mappings
}
```

## Generated Files

The generator creates 7 files per entity:

### 1. Model (`app/models/{entity}.py`)

SQLAlchemy model with:
- Table definition
- Column definitions
- Relationships
- Indexes
- Constraints

### 2. Service (`app/services/{entity}_service.py`)

Service layer with:
- CRUD operations (create, get, list, update, delete)
- Business logic hooks
- Transaction management
- Error handling

**Note:** Services now require four type parameters:
```python
class ProductService(BaseService[Product, ProductCreate, ProductUpdate, ProductResponse]):
    pass
```

The fourth parameter (`ProductResponse`) is the Pydantic response schema type used for API responses.

### 3. Schemas (`app/schemas/{entity}_schemas.py`)

Pydantic schemas:
- `{Entity}Base` - Shared fields
- `{Entity}Create` - Creation payload
- `{Entity}Update` - Update payload
- `{Entity}InDB` - Database representation
- `{Entity}` - Public API response

### 4. API Router (`app/api/{entity}s.py`)

FastAPI endpoints:
- `POST /api/v1/{entities}` - Create
- `GET /api/v1/{entities}` - List with pagination
- `GET /api/v1/{entities}/{id}` - Get by ID
- `PUT /api/v1/{entities}/{id}` - Update
- `DELETE /api/v1/{entities}/{id}` - Delete

### 5. API Tests (`tests/test_{entity}s_api.py`)

Integration tests for all endpoints with:
- Success scenarios
- Error handling
- Validation tests
- Authentication tests

### 6. Service Tests (`tests/test_{entity}s_service.py`)

Unit tests for service layer with:
- CRUD operation tests
- Business logic tests
- Edge case handling

### 7. Migration (`alembic/versions/{rev}_{operation}_{entity}_table.py`)

Alembic migration with:
- `upgrade()` - Create table
- `downgrade()` - Drop table
- Automatic revision chaining

## Next Steps After Generation

After running the generator:

### 1. Apply Database Migration

```bash
alembic upgrade head
```

### 2. Start Development Server

```bash
uvicorn app.main:app --reload
```

### 3. Test API Endpoints

```bash
# List entities
curl http://localhost:8000/api/v1/products

# Create entity
curl -X POST http://localhost:8000/api/v1/products \
  -H "Content-Type: application/json" \
  -d '{"name":"Widget","price":19.99}'

# Get entity
curl http://localhost:8000/api/v1/products/{id}
```

### 4. View Interactive Documentation

Open in browser: http://localhost:8000/docs

### 5. Run Tests

```bash
# Run all tests
pytest

# Run specific entity tests
pytest tests/test_products_api.py -v
```

## Troubleshooting

### Error: "Invalid entity name"

**Cause:** Entity name is not a valid Python identifier.

**Solution:** Use lowercase names without spaces or special characters:
```bash
# ❌ Bad
crud-generate user-account
crud-generate User Account

# ✅ Good
crud-generate user_account
crud-generate useraccount
```

### Error: "Reserved Python keyword"

**Cause:** Entity name is a Python keyword (`class`, `def`, etc.).

**Solution:** Use a different name:
```bash
# ❌ Bad
crud-generate class

# ✅ Good
crud-generate course
crud-generate training_class
```

### Error: "Could not auto-detect backend directory"

**Cause:** Running from wrong directory or invalid project structure.

**Solution:** Specify output directory explicitly:
```bash
crud-generate user --output-dir ./backend
```

### Error: "Missing required dependencies"

**Cause:** Required packages not installed.

**Solution:** Install missing dependencies:
```bash
pip install alembic jinja2 sqlalchemy fastapi
```

### Error: "Could not find router registration section"

**Cause:** `app/main.py` missing required comment marker.

**Solution:** Add this comment to `app/main.py`:
```python
# Include routers
```

### Generated Tests Fail

**Cause:** Database not configured or migrations not applied.

**Solution:**
1. Configure database connection in `.env`
2. Run migrations: `alembic upgrade head`
3. Ensure test database is accessible

## Best Practices

### Entity Naming

- Use singular names (product, not products)
- Use snake_case for multi-word names (work_log, not workLog)
- Keep names concise but descriptive

### Field Design

- Always include unique constraints for natural keys (email, username)
- Use appropriate types (decimal for money, not float)
- Add indexes for frequently queried fields
- Use foreign keys for relationships
- Mark optional fields as nullable

### Domain Patterns

- Use `employee` domain for staff/team management
- Use `customer` domain for client/customer management
- Use generic domain for custom entities

### Version Control

- Commit generated files together as a logical unit
- Review generated code before committing
- Keep templates in version control
- Track migration files in Git

## Advanced Topics

### Batch Generation

Generate multiple entities in sequence:

```bash
crud-generate product --fields "name:str,price:decimal"
crud-generate category --fields "name:str,description:text"
crud-generate order --fields "product_id:fk,quantity:int"
```

### Custom Base Classes

Edit templates to inherit from custom base classes instead of the default ones.

### Multi-Tenancy

Add tenant_id foreign key to all entities:

```bash
crud-generate resource --fields "tenant_id:fk:tenants,name:str,data:json"
```

### Soft Delete Behavior

When soft delete is enabled:
- Delete operations set `is_deleted=True` instead of removing records
- List operations automatically filter deleted records
- Restore is possible by setting `is_deleted=False`

## Support

For issues or questions:
- Check the troubleshooting section above
- Review generated code and tests
- Consult the FastAPI and SQLAlchemy documentation
- Ask in the team Slack channel

## Version History

- **v1.0.0** - Initial release
  - CLI framework with Typer
  - 15 field types
  - 3 domain patterns
  - 7 file templates
  - Comprehensive test generation
  - 109 tests with 87% coverage
