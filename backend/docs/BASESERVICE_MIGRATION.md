# BaseService Type System Migration Guide

## Overview

The `BaseService` generic class has been updated to use four type parameters instead of three. This change fixes a critical bug where SQLAlchemy ORM models were incorrectly used as Pydantic generic type parameters, causing `PydanticSchemaGenerationError` on application startup.

## What Changed

### Before (3 type parameters)
```python
class EmployeeService(BaseService[Employee, EmployeeCreate, EmployeeUpdate]):
    pass
```

### After (4 type parameters)
```python
class EmployeeService(BaseService[Employee, EmployeeCreate, EmployeeUpdate, EmployeeResponse]):
    pass
```

## Why This Change

The `get_list()` method returns `ListResponseSchema[T]` where `T` must be a Pydantic schema (not a SQLAlchemy model). The previous implementation tried to use `ModelType` (SQLAlchemy) as the generic parameter for `ListResponseSchema`, which caused Pydantic to fail during schema generation.

The new fourth type parameter (`ResponseSchemaType`) separates:
- **Internal data**: SQLAlchemy models (`ModelType`)
- **API responses**: Pydantic schemas (`ResponseSchemaType`)

## Migration Steps

### Step 1: Update Service Class Definition

Add the response schema as the fourth type parameter:

```python
# File: app/services/your_entity_service.py

from app.models.your_entity import YourEntity
from app.schemas.your_entity_schemas import (
    YourEntityCreate,
    YourEntityUpdate,
    YourEntityResponse,  # Add this import
)
from app.services.base import BaseService


class YourEntityService(
    BaseService[
        YourEntity,           # Model (SQLAlchemy)
        YourEntityCreate,     # Create schema (Pydantic)
        YourEntityUpdate,     # Update schema (Pydantic)
        YourEntityResponse,   # Response schema (Pydantic) - NEW
    ]
):
    """Service for your_entity operations."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(YourEntity, db)
```

### Step 2: Update Tests (If Applicable)

If your tests check the type of items returned by `get_list()`, update them:

```python
# Before
result = await service.get_list(pagination=pagination)
assert isinstance(result.data[0], YourEntity)  # SQLAlchemy model

# After
result = await service.get_list(pagination=pagination)
assert isinstance(result.data[0], YourEntityResponse)  # Pydantic schema
```

Most tests only check attributes (e.g., `result.data[0].name`), which work the same way.

### Step 3: Verify No Import Errors

Test that your service imports without errors:

```bash
python -c "from app.services.your_entity_service import YourEntityService; print('✅ Import successful')"
```

### Step 4: Verify Application Startup

```bash
python -c "from app.main import app; print('✅ Application imports successfully')"
```

## Generated Files

**Good news**: If you use the CRUD generator, new entities will automatically use the correct 4-parameter signature. The template has been updated.

## Query Builder Changes

The following internal changes were also made to fix query builder bugs:

### Before (Invalid)
```python
# This didn't work - .active() and .with_deleted() don't exist on Select objects
query = select(self.model).active()
query = select(self.model).with_deleted()
```

### After (Correct)
```python
# Proper SQLAlchemy syntax
query = select(self.model)
if not include_deleted:
    query = query.where(self.model.is_deleted == False)
```

**Note**: This change is internal to `BaseService` - you don't need to update your service classes for this fix.

## Benefits

1. **Application starts**: Fixes `PydanticSchemaGenerationError` on import
2. **Proper types**: Separates SQLAlchemy models from Pydantic schemas
3. **Better IDE support**: Type hints work correctly for API responses
4. **No data loss**: Existing data and functionality remain unchanged

## Troubleshooting

### Error: "Too few arguments for BaseService"

**Cause**: Service class still uses 3 type parameters.

**Solution**: Add the response schema as the fourth parameter (see Step 1).

### Error: "Cannot import ResponseSchema"

**Cause**: Response schema not imported.

**Solution**: Add the import:
```python
from app.schemas.your_entity_schemas import YourEntityResponse
```

### Error: "TypeError: 'ResponseSchemaType' object is not callable"

**Cause**: This error should not occur with correct implementation.

**Solution**: Verify you're passing the response schema class, not an instance:
```python
# Correct
BaseService[Model, Create, Update, ResponseClass]

# Wrong
BaseService[Model, Create, Update, ResponseClass()]
```

## Example: Complete Migration

```python
# Before
"""employee service."""
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.schemas.employee_schemas import EmployeeCreate, EmployeeUpdate
from app.services.base import BaseService


class EmployeeService(BaseService[Employee, EmployeeCreate, EmployeeUpdate]):
    """Service for employee operations."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Employee, db)
```

```python
# After
"""employee service."""
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.schemas.employee_schemas import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,  # Added
)
from app.services.base import BaseService


class EmployeeService(
    BaseService[Employee, EmployeeCreate, EmployeeUpdate, EmployeeResponse]  # Added 4th param
):
    """Service for employee operations."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Employee, db)
```

## Questions?

- Check the [OpenSpec proposal](../../openspec/changes/fix-service-type-system/proposal.md)
- Review the [bug analysis](../../LOCAL_SERVICE_STARTUP_BUGS.md)
- Check BaseService implementation: `app/services/base.py`

## Version

- **Updated**: 2024-10-22
- **Change ID**: `fix-service-type-system`
- **Breaking Change**: Yes (requires code updates)
