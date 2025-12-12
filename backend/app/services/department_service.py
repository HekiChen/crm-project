"""
Department service implementing business rules and hierarchy helpers.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload, selectinload

from app.models.department import Department
from app.models.employee import Employee
from app.schemas.department_schemas import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentListResponse,
    ManagerSummary,
)
from app.schemas.base import PaginationParams
from app.services.base import BaseService


class DepartmentService(BaseService[Department, DepartmentCreate, DepartmentUpdate, DepartmentResponse]):
    def __init__(self, db: AsyncSession):
        super().__init__(Department, db, DepartmentResponse)

    def _to_response_with_manager(self, department: Department) -> DepartmentResponse:
        """
        Transform Department model to DepartmentResponse with manager filtering.
        Only includes manager details if the manager is active and not deleted.
        """
        # Filter manager: only include if active and not deleted
        manager_summary = None
        if (department.manager_employee and 
            not department.manager_employee.is_deleted and 
            department.manager_employee.is_active):
            manager_summary = ManagerSummary.model_validate(department.manager_employee)
        
        # Use model_validate with from_attributes, then set manager field
        response = DepartmentResponse.model_validate(department, from_attributes=True)
        response.manager = manager_summary
        response.children = None
        return response

    async def get_by_id(
        self,
        id: UUID,
        *,
        include_deleted: bool = False,
    ) -> Optional[Department]:
        """
        Get department by ID with relationships noload to prevent lazy loading.
        """
        stmt = select(Department).where(Department.id == id).options(
            selectinload(Department.manager_employee),
            noload(Department.children),
            noload(Department.parent),
            noload(Department.employees),
            noload(Department.positions)
        )
        if not include_deleted:
            stmt = stmt.where(Department.is_deleted == False)  # noqa: E712
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[Department]:
        stmt = select(Department).where(Department.code == code, Department.is_deleted == False)  # noqa: E712
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def create(self, obj_in: DepartmentCreate, *, created_by_id: Optional[UUID] = None, commit: bool = True) -> Department:
        # Check unique code
        existing = await self.get_by_code(obj_in.code)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Department with code '{obj_in.code}' already exists")

        # Validate manager exists if provided
        if obj_in.manager_id is not None:
            stmt = select(Employee).where(Employee.id == obj_in.manager_id, Employee.is_deleted == False)  # noqa: E712
            r = await self.db.execute(stmt)
            if r.scalar_one_or_none() is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Manager employee not found")

        # Validate parent exists if provided
        if obj_in.parent_id is not None:
            parent = await self.get_by_id(obj_in.parent_id)
            if parent is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parent department not found")

        # Create the object
        obj_data = obj_in.model_dump(exclude_unset=True)
        if created_by_id:
            obj_data["created_by_id"] = created_by_id
        
        db_obj = Department(**obj_data)
        self.db.add(db_obj)
        
        if commit:
            await self.db.commit()
            # Re-query with noload to prevent lazy loading during serialization
            # Using refresh() still triggers lazy loads, so we re-query instead
            db_obj = await self.get_by_id(db_obj.id)
        
        return db_obj

    async def update(self, id: UUID, obj_in: DepartmentUpdate, *, updated_by_id: Optional[UUID] = None, commit: bool = True) -> Optional[Department]:
        existing = await self.get_by_id(id)
        if not existing:
            return None

        # If code changes, ensure uniqueness
        if obj_in.code is not None and obj_in.code != existing.code:
            conflict = await self.get_by_code(obj_in.code)
            if conflict and conflict.id != id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Department with code '{obj_in.code}' already exists")

        # Validate manager
        if obj_in.manager_id is not None:
            stmt = select(Employee).where(Employee.id == obj_in.manager_id, Employee.is_deleted == False)  # noqa: E712
            r = await self.db.execute(stmt)
            if r.scalar_one_or_none() is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Manager employee not found")

        # Validate parent and prevent cycles
        if obj_in.parent_id is not None:
            if obj_in.parent_id == id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department cannot be its own parent")
            parent = await self.get_by_id(obj_in.parent_id)
            if parent is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parent department not found")
            # Simple cycle prevention: check parent chain
            ancestor = parent
            while ancestor:
                if ancestor.id == id:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parent assignment would create cycle")
                ancestor = await self.get_by_id(ancestor.parent_id) if ancestor.parent_id else None

        # Update fields
        update_data = obj_in.model_dump(exclude_unset=True)
        if updated_by_id:
            update_data["updated_by_id"] = updated_by_id
        
        for field, value in update_data.items():
            if hasattr(existing, field):
                setattr(existing, field, value)
        
        if commit:
            await self.db.commit()
            # Re-query with noload to prevent lazy loading during serialization
            # Using refresh() still triggers lazy loads, so we re-query instead
            existing = await self.get_by_id(existing.id)
        
        return existing

    async def get_children(self, id: UUID) -> List[Department]:
        stmt = select(Department).where(
            Department.parent_id == id, 
            Department.is_deleted == False  # noqa: E712
        ).options(
            selectinload(Department.manager_employee),
            noload(Department.children),
            noload(Department.parent),
            noload(Department.employees),
            noload(Department.positions)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_parent(self, id: UUID) -> Optional[Department]:
        dept = await self.get_by_id(id)
        if not dept or not dept.parent_id:
            return None
        return await self.get_by_id(dept.parent_id)

    async def get_list(
        self,
        *,
        pagination: PaginationParams,
        filters: Optional[Dict[str, Any]] = None,
        search: Optional[str] = None,
        include_deleted: bool = False,
    ) -> DepartmentListResponse:
        """
        Get paginated list of departments with optional filtering and search.
        
        Supports filtering by any department field via filters dict.
        Supports searching by department name, code, or description.
        """
        # Build base query with noload for relationships (except manager_employee which uses selectinload)
        query = select(Department).options(
            selectinload(Department.manager_employee),
            noload(Department.children),
            noload(Department.parent),
            noload(Department.employees),
            noload(Department.positions)
        )
        
        # Apply soft-delete filter
        if not include_deleted:
            query = query.where(Department.is_deleted == False)  # noqa: E712
        
        # Apply search
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Department.name.ilike(search_term),
                    Department.code.ilike(search_term),
                    Department.description.ilike(search_term)
                )
            )
        
        # Apply filters
        if filters:
            conditions = []
            for field, value in filters.items():
                if hasattr(Department, field):
                    if isinstance(value, list):
                        conditions.append(getattr(Department, field).in_(value))
                    else:
                        conditions.append(getattr(Department, field) == value)
            
            if conditions:
                query = query.where(and_(*conditions))
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        result = await self.db.execute(count_query)
        total = result.scalar() or 0
        
        # Apply sorting
        if pagination.sort_by and hasattr(Department, pagination.sort_by):
            sort_column = getattr(Department, pagination.sort_by)
            if pagination.sort_order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        else:
            # Default sort by created_at desc
            query = query.order_by(Department.created_at.desc())
        
        # Apply pagination
        query = query.offset(pagination.skip).limit(pagination.limit)
        
        # Execute query
        result = await self.db.execute(query)
        db_objects = list(result.scalars().all())
        
        # Convert to response schemas with manager filtering
        response_data = [self._to_response_with_manager(obj) for obj in db_objects]
        
        # Explicitly set children to None to avoid any lazy loading attempts
        for item in response_data:
            item.children = None
        
        # Return paginated response
        return DepartmentListResponse.create(
            data=response_data,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def get_employees(self, department_id: UUID) -> List[Employee]:
        """
        Get all employees in a department with position eager loading.
        
        Args:
            department_id: Department UUID
            
        Returns:
            List of Employee objects with position relationship loaded
        """
        from sqlalchemy.orm import joinedload
        
        # Verify department exists
        dept = await self.get_by_id(department_id)
        if not dept:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found"
            )
        
        # Fetch employees with position eager loading
        stmt = (
            select(Employee)
            .where(
                Employee.department_id == department_id,
                Employee.is_deleted == False  # noqa: E712
            )
            .options(joinedload(Employee.position))
            .order_by(Employee.employee_number)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
