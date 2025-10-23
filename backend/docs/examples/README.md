# CRUD Template System - Usage Examples

This directory contains practical examples of using the CRUD template system for common scenarios.

## Running the Examples

Each example can be executed directly from the command line. Make sure you're in the backend directory with the conda environment activated.

## Example 1: Basic User Entity

**Scenario:** Create a simple user management system.

### Command

```bash
crud-generate user \
  --fields "username:str:unique:index,email:str:unique,full_name:str,bio:text:nullable,is_active:bool"
```

### What It Generates

- User model with unique constraints on username and email
- Index on username for fast lookups
- Optional bio field
- Boolean status flag
- Full CRUD API with authentication ready

### Generated Endpoints

- `POST /api/v1/users` - Create user
- `GET /api/v1/users` - List users (paginated)
- `GET /api/v1/users/{id}` - Get user by ID
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user (soft delete)

### Testing

```bash
# Run generated tests
pytest tests/test_users_api.py -v
pytest tests/test_users_service.py -v

# Apply migration
alembic upgrade head

# Test API
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "is_active": true
  }'
```

### Use Cases

- User authentication systems
- Profile management
- Access control
- Account management

---

## Example 2: Employee with CRM Domain

**Scenario:** Create an employee management system with CRM-specific features.

### Command

```bash
crud-generate employee \
  --domain employee \
  --fields "first_name:str,last_name:str,email:str:unique,phone:phone,hire_date:date,salary:money,job_title:str"
```

### What It Generates

All standard files PLUS domain-specific enhancements:

- Automatic `position_id` foreign key
- Automatic `department_id` foreign key
- Self-referential `manager_id` for hierarchy
- `is_active` status flag
- Integration with CRM employee patterns

### Generated Endpoints

- `POST /api/v1/employees` - Hire employee
- `GET /api/v1/employees` - List employees (with filters)
- `GET /api/v1/employees/{id}` - Get employee details
- `PUT /api/v1/employees/{id}` - Update employee
- `DELETE /api/v1/employees/{id}` - Terminate (soft delete)

### Testing

```bash
# Run tests
pytest tests/test_employees_api.py -v

# Apply migration
alembic upgrade head

# Create employee
curl -X POST http://localhost:8000/api/v1/employees \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane.smith@company.com",
    "phone": "+1-555-0123",
    "hire_date": "2025-01-15",
    "salary": 75000.00,
    "job_title": "Senior Developer"
  }'
```

### Use Cases

- HR management systems
- Employee directories
- Organizational charts
- Payroll systems
- Time tracking

---

## Example 3: Customer with Relationships

**Scenario:** Create a customer management system with contact information and relationships.

### Command

```bash
crud-generate customer \
  --domain customer \
  --fields "first_name:str,last_name:str,email:str:unique,phone:phone,company:str:nullable,address:text:nullable,city:str:nullable,state:str:nullable,zip_code:str:nullable,notes:text:nullable"
```

### What It Generates

Customer entity with CRM domain features:

- Automatic `customer_type` field (individual/business)
- Automatic `account_status` field (active/inactive/suspended)
- Automatic `tags` JSON field for categorization
- Full contact information
- Address fields
- Internal notes

### Generated Endpoints

- `POST /api/v1/customers` - Create customer
- `GET /api/v1/customers` - List customers (with filters)
- `GET /api/v1/customers/{id}` - Get customer details
- `PUT /api/v1/customers/{id}` - Update customer
- `DELETE /api/v1/customers/{id}` - Archive customer

### Testing

```bash
# Run tests
pytest tests/test_customers_api.py -v

# Apply migration
alembic upgrade head

# Create customer
curl -X POST http://localhost:8000/api/v1/customers \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Alice",
    "last_name": "Johnson",
    "email": "alice@example.com",
    "phone": "+1-555-0199",
    "company": "Acme Corp",
    "address": "123 Main St",
    "city": "New York",
    "state": "NY",
    "zip_code": "10001",
    "notes": "Preferred customer, VIP status"
  }'
```

### Use Cases

- CRM systems
- Customer support
- Sales tracking
- Marketing campaigns
- Client management

---

## Example 4: Work Log Entity

**Scenario:** Track daily work activities with minimal overhead.

### Command

```bash
crud-generate work_log \
  --fields "employee_id:fk:employees,date:date,hours:float,task_description:text,project:str:nullable" \
  --no-soft-delete
```

### What It Generates

Streamlined work log entity:

- Links to employees table
- Date tracking
- Hours worked (decimal)
- Task description
- Optional project reference
- NO soft delete (permanent records)
- Automatic timestamps for audit trail

### Generated Endpoints

- `POST /api/v1/work_logs` - Log work entry
- `GET /api/v1/work_logs` - List work logs (filtered by date/employee)
- `GET /api/v1/work_logs/{id}` - Get specific log
- `PUT /api/v1/work_logs/{id}` - Update log entry
- `DELETE /api/v1/work_logs/{id}` - Delete log (hard delete)

### Testing

```bash
# Run tests
pytest tests/test_work_logs_api.py -v

# Apply migration
alembic upgrade head

# Create work log
curl -X POST http://localhost:8000/api/v1/work_logs \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "uuid-here",
    "date": "2025-10-22",
    "hours": 8.5,
    "task_description": "Implemented CRUD template system",
    "project": "CRM Platform"
  }'

# Query by employee and date range
curl "http://localhost:8000/api/v1/work_logs?employee_id=uuid&start_date=2025-10-01&end_date=2025-10-31"
```

### Use Cases

- Time tracking systems
- Project management
- Billing and invoicing
- Activity logging
- Performance tracking

---

## Example 5: Product Catalog

**Scenario:** E-commerce product catalog with inventory.

### Command

```bash
crud-generate product \
  --fields "name:str:index,description:text,price:decimal,cost:decimal,sku:str:unique,barcode:str:unique:nullable,stock_quantity:int,reorder_level:int,category:str:index,is_active:bool"
```

### What It Generates

- Product model with pricing
- Inventory tracking
- SKU and barcode unique constraints
- Category indexing for fast filtering
- Stock level management
- Active/inactive status

### Generated Endpoints

- `POST /api/v1/products` - Create product
- `GET /api/v1/products` - List products (with category filter)
- `GET /api/v1/products/{id}` - Get product details
- `PUT /api/v1/products/{id}` - Update product
- `DELETE /api/v1/products/{id}` - Discontinue product

### Testing

```bash
# Run tests
pytest tests/test_products_api.py -v

# Create product
curl -X POST http://localhost:8000/api/v1/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Widget Pro",
    "description": "Professional grade widget",
    "price": 49.99,
    "cost": 25.00,
    "sku": "WID-PRO-001",
    "barcode": "123456789012",
    "stock_quantity": 100,
    "reorder_level": 20,
    "category": "Electronics",
    "is_active": true
  }'
```

### Use Cases

- E-commerce platforms
- Inventory management
- Point of sale systems
- Warehouse management
- Product catalogs

---

## Example 6: Order Management

**Scenario:** Order processing with line items.

### Command

```bash
# First generate the order
crud-generate order \
  --fields "customer_id:fk:customers,order_date:datetime,status:str,total_amount:decimal,shipping_address:text,notes:text:nullable"

# Then generate order items
crud-generate order_item \
  --fields "order_id:fk:orders,product_id:fk:products,quantity:int,unit_price:decimal,subtotal:decimal" \
  --no-soft-delete
```

### What It Generates

Two related entities:

**Order:**
- Links to customer
- Order status tracking
- Total amount
- Shipping information
- Internal notes

**Order Item:**
- Links to order and product
- Quantity and pricing
- Calculated subtotal
- No soft delete (permanent records)

### Testing

```bash
# Create order
curl -X POST http://localhost:8000/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "customer-uuid",
    "order_date": "2025-10-22T14:30:00",
    "status": "pending",
    "total_amount": 149.97,
    "shipping_address": "456 Oak Ave, Boston, MA 02101"
  }'

# Add order items
curl -X POST http://localhost:8000/api/v1/order_items \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "order-uuid",
    "product_id": "product-uuid",
    "quantity": 3,
    "unit_price": 49.99,
    "subtotal": 149.97
  }'
```

### Use Cases

- Order management
- E-commerce checkouts
- Purchase orders
- Invoice generation
- Sales tracking

---

## Complex Scenarios

### Multi-Entity System

Generate a complete related system:

```bash
# Core entities
crud-generate category --fields "name:str:unique,description:text:nullable"
crud-generate product --fields "category_id:fk:categories,name:str,price:decimal"
crud-generate customer --domain customer --fields "first_name:str,last_name:str,email:str:unique"

# Transactional entities
crud-generate order --fields "customer_id:fk:customers,order_date:datetime,status:str"
crud-generate order_item --fields "order_id:fk:orders,product_id:fk:products,quantity:int,price:decimal" --no-soft-delete

# Supporting entities
crud-generate review --fields "product_id:fk:products,customer_id:fk:customers,rating:int,comment:text"
```

### Migration Strategy

When generating multiple related entities:

1. Generate independent entities first (no foreign keys)
2. Apply migrations: `alembic upgrade head`
3. Generate dependent entities (with foreign keys)
4. Apply new migrations: `alembic upgrade head`
5. Test relationships

---

## Tips and Best Practices

### Naming Conventions

- Use singular entity names (product, not products)
- Use snake_case for multi-word entities (work_log, not workLog)
- Foreign keys should match table names (user_id for users table)

### Field Selection

- Always add unique constraints where appropriate
- Use indexes on frequently queried fields
- Consider nullable for optional fields
- Use appropriate types (decimal for money, text for long content)

### Testing Workflow

1. Run `--dry-run` first to preview
2. Generate the entity
3. Review generated code
4. Run tests: `pytest tests/test_{entity}s_api.py -v`
5. Apply migration: `alembic upgrade head`
6. Test endpoints manually or with curl
7. Check OpenAPI docs: http://localhost:8000/docs

### Performance

- Add indexes to foreign keys (auto-generated)
- Add indexes to fields used in WHERE clauses
- Use pagination for list endpoints (auto-generated)
- Consider soft delete vs hard delete based on compliance needs

---

## Getting Help

- Review documentation: `docs/crud-template-system.md`
- Check generated test files for usage examples
- View OpenAPI docs after generation: http://localhost:8000/docs
- Run with `--dry-run` to preview before generating

## Next Steps

After running these examples:

1. Explore generated files to understand the patterns
2. Customize templates for your specific needs
3. Add business logic to service layers
4. Enhance API endpoints with custom filters
5. Extend test coverage for edge cases
