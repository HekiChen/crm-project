"""
Position service for job role management.

Provides business logic and database operations for Position entities.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.position import Position
from app.schemas.position_schemas import PositionCreate, PositionUpdate, PositionResponse
from app.services.base import BaseService


class PositionService(BaseService[Position, PositionCreate, PositionUpdate, PositionResponse]):
    """
    Service for position/job role operations.
    
    Provides business logic and database operations for Position entities.
    Inherits standard CRUD operations from BaseService and adds custom methods
    for position-specific queries and validations.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize Position service.
        
        Args:
            db: Database session
        """
        super().__init__(Position, db, PositionResponse)
    
    async def create(
        self,
        obj_in: PositionCreate,
        *,
        created_by_id: Optional[UUID] = None,
        commit: bool = True,
    ) -> Position:
        """
        Create a new position with validation.
        Also validates department_id if provided.
        """
        # Check if code already exists (case-insensitive)
        existing_position = await self.get_by_code(obj_in.code)
        if existing_position:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Position with code '{obj_in.code}' already exists"
            )

        # Validate department_id if provided
        if hasattr(obj_in, "department_id") and obj_in.department_id is not None:
            from app.models.department import Department
            stmt = select(Department).where(Department.id == obj_in.department_id, Department.is_deleted == False)
            result = await self.db.execute(stmt)
            dept = result.scalar_one_or_none()
            if dept is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Department not found or inactive"
                )

        # Create the position using base service method
        return await super().create(obj_in, created_by_id=created_by_id, commit=commit)
    
    async def get_by_code(self, code: str) -> Optional[Position]:
        """
        Get a position by its unique code (case-insensitive).
        
        Args:
            code: The position code to search for
        
        Returns:
            The position instance or None if not found
        """
        # Normalize code to uppercase (as per validator in schema)
        code_upper = code.upper()
        
        stmt = select(Position).where(
            Position.code == code_upper,
            Position.is_deleted == False  # noqa: E712
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_active_positions(self) -> List[Position]:
        """
        Get all active (non-deleted, is_active=True) positions.
        
        Returns:
            List of active position instances
        """
        stmt = select(Position).where(
            Position.is_active == True,  # noqa: E712
            Position.is_deleted == False  # noqa: E712
        ).order_by(Position.name)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def update(
        self,
        id: UUID,
        obj_in: PositionUpdate,
        *,
        updated_by_id: Optional[UUID] = None,
        commit: bool = True,
    ) -> Optional[Position]:
        """
        Update an existing position with validation.
        Also validates department_id if provided.
        """
        # Check if position exists
        existing_position = await self.get_by_id(id)
        if not existing_position:
            return None

        # If code is being updated, check for conflicts
        if obj_in.code is not None and obj_in.code != existing_position.code:
            conflicting_position = await self.get_by_code(obj_in.code)
            if conflicting_position and conflicting_position.id != id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Position with code '{obj_in.code}' already exists"
                )

        # Validate department_id if provided
        if hasattr(obj_in, "department_id") and obj_in.department_id is not None:
            from app.models.department import Department
            stmt = select(Department).where(Department.id == obj_in.department_id, Department.is_deleted == False)
            result = await self.db.execute(stmt)
            dept = result.scalar_one_or_none()
            if dept is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Department not found or inactive"
                )

        # Update using base service method
        return await super().update(id, obj_in, updated_by_id=updated_by_id, commit=commit)
    
    async def delete(
        self,
        id: UUID,
        *,
        deleted_by_id: Optional[UUID] = None,
        commit: bool = True,
    ) -> bool:
        """
        Soft delete a position.
        
        When a position is deleted, employees assigned to it will have their
        position_id set to NULL due to the ON DELETE SET NULL constraint.
        
        Args:
            id: The position ID
            deleted_by_id: ID of the user deleting the position
            commit: Whether to commit the transaction
        
        Returns:
            True if deleted, False if not found
        """
        return await super().delete(id, deleted_by_id=deleted_by_id, commit=commit)
