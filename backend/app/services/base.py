"""
Base service class with generic CRUD operations.
"""
from typing import Generic, TypeVar, Type, List, Optional, Any, Dict
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import BaseModel
from app.schemas.base import BaseSchema, CreateSchema, UpdateSchema, ListResponseSchema, PaginationParams


# Type variables for generic service
ModelType = TypeVar("ModelType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=CreateSchema)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=UpdateSchema)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseSchema)


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType, ResponseSchemaType]):
    """
    Base service class with generic CRUD operations.
    
    Provides common database operations for models:
    - create: Create a new record
    - get_by_id: Get a single record by ID
    - get_list: Get a paginated list of records
    - update: Update an existing record
    - delete: Soft delete a record
    - hard_delete: Permanently delete a record
    
    Usage:
        class UserService(BaseService[User, UserCreate, UserUpdate, UserResponse]):
            pass
    """
    
    def __init__(self, model: Type[ModelType], db: AsyncSession, response_schema: Optional[Type[ResponseSchemaType]] = None):
        """
        Initialize the service.
        
        Args:
            model: The SQLAlchemy model class
            db: The database session
            response_schema: The response schema class (optional, for proper type conversion)
        """
        self.model = model
        self.db = db
        self.response_schema = response_schema
    
    async def create(
        self,
        obj_in: CreateSchemaType,
        *,
        created_by_id: Optional[UUID] = None,
        commit: bool = True,
    ) -> ModelType:
        """
        Create a new record.
        
        Args:
            obj_in: The create schema with data
            created_by_id: ID of the user creating the record
            commit: Whether to commit the transaction
        
        Returns:
            The created model instance
        """
        # Convert Pydantic model to dict
        obj_data = obj_in.model_dump(exclude_unset=True)
        
        # Add audit field
        if created_by_id:
            obj_data["created_by_id"] = created_by_id
        
        # Create model instance
        db_obj = self.model(**obj_data)
        
        # Add to session
        self.db.add(db_obj)
        
        if commit:
            await self.db.commit()
            await self.db.refresh(db_obj)
        
        return db_obj
    
    async def get_by_id(
        self,
        id: UUID,
        *,
        include_deleted: bool = False,
    ) -> Optional[ModelType]:
        """
        Get a single record by ID.
        
        Args:
            id: The record ID
            include_deleted: Whether to include soft-deleted records
        
        Returns:
            The model instance or None if not found
        """
        # Use the model's built-in method
        return await self.model.get_by_id(self.db, id, include_deleted=include_deleted)
    
    async def get_list(
        self,
        *,
        pagination: PaginationParams,
        filters: Optional[Dict[str, Any]] = None,
        include_deleted: bool = False,
    ) -> ListResponseSchema[ResponseSchemaType]:
        """
        Get a paginated list of records.
        
        Args:
            pagination: Pagination parameters
            filters: Optional filters as dict (field: value)
            include_deleted: Whether to include soft-deleted records
        
        Returns:
            ListResponseSchema with data and pagination metadata
        """
        # Build base query
        query = select(self.model)
        
        # Apply soft-delete filter
        if not include_deleted:
            query = query.where(self.model.is_deleted == False)  # noqa: E712
        
        # Apply filters
        if filters:
            conditions = []
            for field, value in filters.items():
                if hasattr(self.model, field):
                    if isinstance(value, list):
                        # Support for IN queries
                        conditions.append(getattr(self.model, field).in_(value))
                    else:
                        conditions.append(getattr(self.model, field) == value)
            
            if conditions:
                query = query.where(and_(*conditions))
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        result = await self.db.execute(count_query)
        total = result.scalar() or 0
        
        # Apply sorting
        if pagination.sort_by and hasattr(self.model, pagination.sort_by):
            sort_column = getattr(self.model, pagination.sort_by)
            if pagination.sort_order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        else:
            # Default sort by created_at desc
            query = query.order_by(self.model.created_at.desc())
        
        # Apply pagination
        query = query.offset(pagination.skip).limit(pagination.limit)
        
        # Execute query
        result = await self.db.execute(query)
        db_objects = list(result.scalars().all())
        
        # Convert SQLAlchemy models to Pydantic response schemas
        if self.response_schema:
            response_data = [self.response_schema.model_validate(obj) for obj in db_objects]
        else:
            # Fallback: return raw objects if no response schema provided
            response_data = db_objects
        
        # Return paginated response
        return ListResponseSchema[ResponseSchemaType].create(
            data=response_data,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )
    
    async def update(
        self,
        id: UUID,
        obj_in: UpdateSchemaType,
        *,
        updated_by_id: Optional[UUID] = None,
        commit: bool = True,
    ) -> Optional[ModelType]:
        """
        Update an existing record.
        
        Args:
            id: The record ID
            obj_in: The update schema with data
            updated_by_id: ID of the user updating the record
            commit: Whether to commit the transaction
        
        Returns:
            The updated model instance or None if not found
        """
        # Get existing record
        db_obj = await self.get_by_id(id)
        if not db_obj:
            return None
        
        # Convert Pydantic model to dict, excluding unset fields
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # Add audit field
        if updated_by_id:
            update_data["updated_by_id"] = updated_by_id
        
        # Update fields
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        if commit:
            await self.db.commit()
            await self.db.refresh(db_obj)
        
        return db_obj
    
    async def delete(
        self,
        id: UUID,
        *,
        deleted_by_id: Optional[UUID] = None,
        commit: bool = True,
    ) -> bool:
        """
        Soft delete a record.
        
        Args:
            id: The record ID
            deleted_by_id: ID of the user deleting the record
            commit: Whether to commit the transaction
        
        Returns:
            True if deleted, False if not found
        """
        # Get existing record
        db_obj = await self.get_by_id(id)
        if not db_obj:
            return False
        
        # Soft delete
        db_obj.soft_delete(deleted_by_id=deleted_by_id)
        
        if commit:
            await self.db.commit()
            await self.db.refresh(db_obj)
        
        return True
    
    async def hard_delete(
        self,
        id: UUID,
        *,
        commit: bool = True,
    ) -> bool:
        """
        Permanently delete a record.
        
        Args:
            id: The record ID
            commit: Whether to commit the transaction
        
        Returns:
            True if deleted, False if not found
        """
        # Get existing record (including soft-deleted)
        db_obj = await self.get_by_id(id, include_deleted=True)
        if not db_obj:
            return False
        
        # Hard delete
        await self.db.delete(db_obj)
        
        if commit:
            await self.db.commit()
        
        return True
    
    async def restore(
        self,
        id: UUID,
        *,
        commit: bool = True,
    ) -> Optional[ModelType]:
        """
        Restore a soft-deleted record.
        
        Args:
            id: The record ID
            commit: Whether to commit the transaction
        
        Returns:
            The restored model instance or None if not found
        """
        # Get soft-deleted record
        db_obj = await self.get_by_id(id, include_deleted=True)
        if not db_obj or not db_obj.is_deleted:
            return None
        
        # Restore
        db_obj.restore()
        
        if commit:
            await self.db.commit()
            await self.db.refresh(db_obj)
        
        return db_obj
    
    async def exists(
        self,
        *,
        filters: Dict[str, Any],
        include_deleted: bool = False,
    ) -> bool:
        """
        Check if a record exists matching the filters.
        
        Args:
            filters: Filters as dict (field: value)
            include_deleted: Whether to include soft-deleted records
        
        Returns:
            True if exists, False otherwise
        """
        # Build query
        query = select(self.model)
        
        # Apply soft-delete filter
        if not include_deleted:
            query = query.where(self.model.is_deleted == False)  # noqa: E712
        
        # Apply filters
        conditions = []
        for field, value in filters.items():
            if hasattr(self.model, field):
                conditions.append(getattr(self.model, field) == value)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Limit to 1
        query = query.limit(1)
        
        # Execute
        result = await self.db.execute(query)
        return result.scalar() is not None
    
    async def count(
        self,
        *,
        filters: Optional[Dict[str, Any]] = None,
        include_deleted: bool = False,
    ) -> int:
        """
        Count records matching the filters.
        
        Args:
            filters: Optional filters as dict (field: value)
            include_deleted: Whether to include soft-deleted records
        
        Returns:
            The count of matching records
        """
        # Build base query
        query = select(func.count()).select_from(self.model)
        
        # Apply soft-delete filter
        if not include_deleted:
            query = query.where(self.model.is_deleted == False)  # noqa: E712
        
        # Apply filters
        if filters:
            conditions = []
            for field, value in filters.items():
                if hasattr(self.model, field):
                    conditions.append(getattr(self.model, field) == value)
            
            if conditions:
                query = query.where(and_(*conditions))
        
        # Execute
        result = await self.db.execute(query)
        return result.scalar() or 0
