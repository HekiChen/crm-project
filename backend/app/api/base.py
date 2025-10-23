"""
Base CRUD router patterns and helper functions for FastAPI.
"""
from typing import Generic, TypeVar, Type, List, Optional, Callable, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.base import BaseModel
from app.schemas.base import (
    CreateSchema,
    UpdateSchema,
    ResponseSchema,
    ListResponseSchema,
    PaginationParams,
    IDResponse,
    MessageResponse,
)
from app.services.base import BaseService


# Type variables
ModelType = TypeVar("ModelType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=CreateSchema)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=UpdateSchema)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=ResponseSchema)


class BaseCRUDRouter(Generic[ModelType, CreateSchemaType, UpdateSchemaType, ResponseSchemaType]):
    """
    Base CRUD router that generates standard REST endpoints.
    
    Provides standard CRUD operations:
    - POST / - Create new entity
    - GET /{id} - Get entity by ID
    - GET / - List entities (paginated)
    - PUT /{id} - Full update entity
    - PATCH /{id} - Partial update entity
    - DELETE /{id} - Soft delete entity
    - DELETE /{id}/hard - Hard delete entity (optional)
    
    Usage:
        from app.models.user import User
        from app.schemas.user import UserCreate, UserUpdate, UserResponse
        from app.api.base import BaseCRUDRouter
        
        router = BaseCRUDRouter(
            model=User,
            create_schema=UserCreate,
            update_schema=UserUpdate,
            response_schema=UserResponse,
            prefix="/users",
            tags=["users"],
        ).router
    """
    
    def __init__(
        self,
        model: Type[ModelType],
        create_schema: Type[CreateSchemaType],
        update_schema: Type[UpdateSchemaType],
        response_schema: Type[ResponseSchemaType],
        prefix: str,
        tags: Optional[List[str]] = None,
        include_hard_delete: bool = False,
        get_current_user: Optional[Callable] = None,
    ):
        """
        Initialize the CRUD router.
        
        Args:
            model: SQLAlchemy model class
            create_schema: Pydantic schema for creating entities
            update_schema: Pydantic schema for updating entities
            response_schema: Pydantic schema for responses
            prefix: URL prefix for the router (e.g., "/users")
            tags: OpenAPI tags for the router
            include_hard_delete: Whether to include hard delete endpoint
            get_current_user: Optional dependency for authentication
        """
        self.model = model
        self.create_schema = create_schema
        self.update_schema = update_schema
        self.response_schema = response_schema
        self.get_current_user = get_current_user
        self.include_hard_delete = include_hard_delete
        
        # Create router
        self.router = APIRouter(prefix=prefix, tags=tags or [prefix.strip("/").title()])
        
        # Register endpoints
        self._register_endpoints()
    
    def _get_service(self, db: AsyncSession) -> BaseService[ModelType, CreateSchemaType, UpdateSchemaType]:
        """Get service instance."""
        return BaseService(self.model, db)
    
    def _register_endpoints(self) -> None:
        """Register all CRUD endpoints."""
        
        @self.router.post(
            "/",
            response_model=self.response_schema,
            status_code=status.HTTP_201_CREATED,
            summary=f"Create new {self.model.__name__}",
            description=f"Create a new {self.model.__name__} entity in the database.",
        )
        async def create(
            obj_in: self.create_schema,  # type: ignore
            db: AsyncSession = Depends(get_db),
        ) -> Any:
            """Create new entity."""
            service = self._get_service(db)
            
            # Get current user ID if authentication is enabled
            created_by_id = None
            if self.get_current_user:
                # Note: In production, get this from current_user dependency
                pass
            
            obj = await service.create(obj_in, created_by_id=created_by_id)
            return self.response_schema.model_validate(obj)
        
        @self.router.get(
            "/{id}",
            response_model=self.response_schema,
            summary=f"Get {self.model.__name__} by ID",
            description=f"Retrieve a single {self.model.__name__} entity by its ID.",
        )
        async def get_by_id(
            id: UUID,
            db: AsyncSession = Depends(get_db),
        ) -> Any:
            """Get entity by ID."""
            service = self._get_service(db)
            obj = await service.get_by_id(id)
            
            if not obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{self.model.__name__} not found",
                )
            
            return self.response_schema.model_validate(obj)
        
        @self.router.get(
            "/",
            response_model=ListResponseSchema[self.response_schema],  # type: ignore
            summary=f"List {self.model.__name__}s",
            description=f"Retrieve a paginated list of {self.model.__name__} entities.",
        )
        async def get_list(
            pagination: PaginationParams = Depends(),
            db: AsyncSession = Depends(get_db),
        ) -> Any:
            """Get paginated list of entities."""
            service = self._get_service(db)
            result = await service.get_list(pagination=pagination)
            
            # Convert model instances to response schemas
            data = [self.response_schema.model_validate(obj) for obj in result.data]
            
            return ListResponseSchema[self.response_schema].create(  # type: ignore
                data=data,
                total=result.total,
                page=result.page,
                page_size=result.page_size,
            )
        
        @self.router.put(
            "/{id}",
            response_model=self.response_schema,
            summary=f"Update {self.model.__name__}",
            description=f"Update an existing {self.model.__name__} entity (full update).",
        )
        async def update(
            id: UUID,
            obj_in: self.update_schema,  # type: ignore
            db: AsyncSession = Depends(get_db),
        ) -> Any:
            """Update entity (full update)."""
            service = self._get_service(db)
            
            # Get current user ID if authentication is enabled
            updated_by_id = None
            if self.get_current_user:
                pass
            
            obj = await service.update(id, obj_in, updated_by_id=updated_by_id)
            
            if not obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{self.model.__name__} not found",
                )
            
            return self.response_schema.model_validate(obj)
        
        @self.router.patch(
            "/{id}",
            response_model=self.response_schema,
            summary=f"Partial update {self.model.__name__}",
            description=f"Partially update an existing {self.model.__name__} entity.",
        )
        async def partial_update(
            id: UUID,
            obj_in: self.update_schema,  # type: ignore
            db: AsyncSession = Depends(get_db),
        ) -> Any:
            """Partially update entity."""
            service = self._get_service(db)
            
            # Get current user ID if authentication is enabled
            updated_by_id = None
            if self.get_current_user:
                pass
            
            obj = await service.update(id, obj_in, updated_by_id=updated_by_id)
            
            if not obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{self.model.__name__} not found",
                )
            
            return self.response_schema.model_validate(obj)
        
        @self.router.delete(
            "/{id}",
            response_model=MessageResponse,
            summary=f"Delete {self.model.__name__}",
            description=f"Soft delete a {self.model.__name__} entity.",
        )
        async def delete(
            id: UUID,
            db: AsyncSession = Depends(get_db),
        ) -> Any:
            """Soft delete entity."""
            service = self._get_service(db)
            
            # Get current user ID if authentication is enabled
            deleted_by_id = None
            if self.get_current_user:
                pass
            
            success = await service.delete(id, deleted_by_id=deleted_by_id)
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{self.model.__name__} not found",
                )
            
            return MessageResponse(
                message=f"{self.model.__name__} deleted successfully",
                detail={"id": str(id)},
            )
        
        # Optional hard delete endpoint
        if self.include_hard_delete:
            @self.router.delete(
                "/{id}/hard",
                response_model=MessageResponse,
                summary=f"Hard delete {self.model.__name__}",
                description=f"Permanently delete a {self.model.__name__} entity.",
            )
            async def hard_delete(
                id: UUID,
                db: AsyncSession = Depends(get_db),
            ) -> Any:
                """Hard delete entity (permanent)."""
                service = self._get_service(db)
                success = await service.hard_delete(id)
                
                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"{self.model.__name__} not found",
                    )
                
                return MessageResponse(
                    message=f"{self.model.__name__} permanently deleted",
                    detail={"id": str(id)},
                )


# Helper functions for creating individual endpoints

def create_endpoint(
    model: Type[ModelType],
    create_schema: Type[CreateSchemaType],
    response_schema: Type[ResponseSchemaType],
    get_current_user: Optional[Callable] = None,
) -> Callable:
    """
    Create a factory for POST / endpoint.
    
    Args:
        model: Model class
        create_schema: Create schema
        response_schema: Response schema
        get_current_user: Optional auth dependency
    
    Returns:
        FastAPI endpoint function
    """
    async def endpoint(
        obj_in: create_schema,  # type: ignore
        db: AsyncSession = Depends(get_db),
    ) -> Any:
        service = BaseService(model, db)
        created_by_id = None
        obj = await service.create(obj_in, created_by_id=created_by_id)
        return response_schema.model_validate(obj)
    
    return endpoint


def get_by_id_endpoint(
    model: Type[ModelType],
    response_schema: Type[ResponseSchemaType],
    entity_name: str = "Entity",
) -> Callable:
    """
    Create a factory for GET /{id} endpoint.
    
    Args:
        model: Model class
        response_schema: Response schema
        entity_name: Name of entity for error messages
    
    Returns:
        FastAPI endpoint function
    """
    async def endpoint(
        id: UUID,
        db: AsyncSession = Depends(get_db),
    ) -> Any:
        service = BaseService(model, db)
        obj = await service.get_by_id(id)
        
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{entity_name} not found",
            )
        
        return response_schema.model_validate(obj)
    
    return endpoint


def list_endpoint(
    model: Type[ModelType],
    response_schema: Type[ResponseSchemaType],
) -> Callable:
    """
    Create a factory for GET / endpoint.
    
    Args:
        model: Model class
        response_schema: Response schema
    
    Returns:
        FastAPI endpoint function
    """
    async def endpoint(
        pagination: PaginationParams = Depends(),
        db: AsyncSession = Depends(get_db),
    ) -> Any:
        service = BaseService(model, db)
        result = await service.get_list(pagination=pagination)
        
        # Convert to response schemas
        data = [response_schema.model_validate(obj) for obj in result.data]
        
        return ListResponseSchema[response_schema].create(  # type: ignore
            data=data,
            total=result.total,
            page=result.page,
            page_size=result.page_size,
        )
    
    return endpoint


def update_endpoint(
    model: Type[ModelType],
    update_schema: Type[UpdateSchemaType],
    response_schema: Type[ResponseSchemaType],
    entity_name: str = "Entity",
    get_current_user: Optional[Callable] = None,
) -> Callable:
    """
    Create a factory for PUT /{id} or PATCH /{id} endpoint.
    
    Args:
        model: Model class
        update_schema: Update schema
        response_schema: Response schema
        entity_name: Name of entity for error messages
        get_current_user: Optional auth dependency
    
    Returns:
        FastAPI endpoint function
    """
    async def endpoint(
        id: UUID,
        obj_in: update_schema,  # type: ignore
        db: AsyncSession = Depends(get_db),
    ) -> Any:
        service = BaseService(model, db)
        updated_by_id = None
        obj = await service.update(id, obj_in, updated_by_id=updated_by_id)
        
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{entity_name} not found",
            )
        
        return response_schema.model_validate(obj)
    
    return endpoint


def delete_endpoint(
    model: Type[ModelType],
    entity_name: str = "Entity",
    get_current_user: Optional[Callable] = None,
) -> Callable:
    """
    Create a factory for DELETE /{id} endpoint.
    
    Args:
        model: Model class
        entity_name: Name of entity for messages
        get_current_user: Optional auth dependency
    
    Returns:
        FastAPI endpoint function
    """
    async def endpoint(
        id: UUID,
        db: AsyncSession = Depends(get_db),
    ) -> MessageResponse:
        service = BaseService(model, db)
        deleted_by_id = None
        success = await service.delete(id, deleted_by_id=deleted_by_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{entity_name} not found",
            )
        
        return MessageResponse(
            message=f"{entity_name} deleted successfully",
            detail={"id": str(id)},
        )
    
    return endpoint


# OpenAPI documentation helpers

def add_api_metadata(
    router: APIRouter,
    title: str,
    description: str,
    version: str = "1.0.0",
) -> None:
    """
    Add metadata to a router for OpenAPI documentation.
    
    Args:
        router: FastAPI router
        title: API title
        description: API description
        version: API version
    """
    router.title = title  # type: ignore
    router.description = description  # type: ignore
    router.version = version  # type: ignore


def create_tag_metadata(
    name: str,
    description: str,
    external_docs: Optional[dict] = None,
) -> dict:
    """
    Create tag metadata for OpenAPI documentation.
    
    Args:
        name: Tag name
        description: Tag description
        external_docs: Optional external documentation
    
    Returns:
        Tag metadata dict
    """
    metadata = {
        "name": name,
        "description": description,
    }
    
    if external_docs:
        metadata["externalDocs"] = external_docs
    
    return metadata
