"""
Base model classes for all database models.
"""
from datetime import datetime
from typing import Optional, Type, TypeVar, Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase

from app.core.database import Base as CoreBase


ModelType = TypeVar("ModelType", bound="BaseModel")

class BaseModel(CoreBase):
    """
    Base model class with common fields and functionality.
    
    Provides:
    - UUID primary key
    - Timestamp fields (created_at, updated_at)
    - Soft delete support (is_deleted, deleted_at)
    - Audit trail (created_by_id, updated_by_id)
    - Table name auto-generation
    - Common query class methods
    """
    __abstract__ = True
    
    # Primary key
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        index=True,
        doc="Unique identifier"
    )
    
    # Timestamp fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        doc="Timestamp when record was created"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        doc="Timestamp when record was last updated"
    )
    
    # Soft delete fields
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Soft delete flag"
    )
    
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        doc="Timestamp when record was deleted"
    )
    
    # Audit trail fields
    created_by_id: Mapped[Optional[UUID]] = mapped_column(
        nullable=True,
        doc="ID of user who created this record"
    )
    
    updated_by_id: Mapped[Optional[UUID]] = mapped_column(
        nullable=True,
        doc="ID of user who last updated this record"
    )
    
    @classmethod
    def _get_tablename(cls) -> str:
        """
        Generate table name from class name.
        Converts PascalCase to snake_case and pluralizes.
        
        Examples:
            User -> users
            EmployeePosition -> employee_positions
        """
        import re
        # Convert PascalCase to snake_case
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
        
        # Simple pluralization
        if name.endswith('s'):
            return f"{name}es"
        elif name.endswith('y'):
            return f"{name[:-1]}ies"
        else:
            return f"{name}s"
    
    @classmethod
    async def active(cls: Type[ModelType], db: AsyncSession) -> list[ModelType]:
        """
        Query all active (not soft-deleted) records.
        
        Args:
            db: Database session
            
        Returns:
            List of active records
        """
        stmt = select(cls).where(cls.is_deleted == False)  # noqa: E712
        result = await db.execute(stmt)
        return list(result.scalars().all())
    
    @classmethod
    async def with_deleted(cls: Type[ModelType], db: AsyncSession) -> list[ModelType]:
        """
        Query all records including soft-deleted ones.
        
        Args:
            db: Database session
            
        Returns:
            List of all records
        """
        stmt = select(cls)
        result = await db.execute(stmt)
        return list(result.scalars().all())
    
    @classmethod
    async def deleted_only(cls: Type[ModelType], db: AsyncSession) -> list[ModelType]:
        """
        Query only soft-deleted records.
        
        Args:
            db: Database session
            
        Returns:
            List of deleted records
        """
        stmt = select(cls).where(cls.is_deleted == True)  # noqa: E712
        result = await db.execute(stmt)
        return list(result.scalars().all())
    
    @classmethod
    async def count_active(cls, db: AsyncSession) -> int:
        """
        Count active (not soft-deleted) records.
        
        Args:
            db: Database session
            
        Returns:
            Count of active records
        """
        stmt = select(func.count()).select_from(cls).where(cls.is_deleted == False)  # noqa: E712
        result = await db.execute(stmt)
        return result.scalar_one()
    
    @classmethod
    async def get_by_id(
        cls: Type[ModelType],
        db: AsyncSession,
        record_id: UUID,
        include_deleted: bool = False
    ) -> Optional[ModelType]:
        """
        Get a single record by ID.
        
        Args:
            db: Database session
            record_id: UUID of the record
            include_deleted: Whether to include soft-deleted records
            
        Returns:
            Record if found, None otherwise
        """
        stmt = select(cls).where(cls.id == record_id)
        if not include_deleted:
            stmt = stmt.where(cls.is_deleted == False)  # noqa: E712
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    def soft_delete(self, deleted_by_id: Optional[UUID] = None) -> None:
        """
        Mark this record as soft-deleted.
        
        Args:
            deleted_by_id: ID of user performing the deletion
        """
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.updated_by_id = deleted_by_id
        self.updated_at = datetime.utcnow()
    
    def restore(self, restored_by_id: Optional[UUID] = None) -> None:
        """
        Restore a soft-deleted record.
        
        Args:
            restored_by_id: ID of user performing the restoration
        """
        self.is_deleted = False
        self.deleted_at = None
        self.updated_by_id = restored_by_id
        self.updated_at = datetime.utcnow()
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"
