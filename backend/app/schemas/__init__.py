"""
Pydantic schemas for API request/response models.
"""
from app.schemas.base import (
    BaseSchema,
    CreateSchema,
    UpdateSchema,
    ResponseSchema,
    IDResponse,
    ListResponseSchema,
    PaginationParams,
    MessageResponse,
    ErrorDetail,
    ErrorResponse,
)
from app.schemas.position_schemas import (
    PositionCreate,
    PositionUpdate,
    PositionResponse,
    PositionListResponse,
)
from app.schemas.department_schemas import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentListResponse,
)
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    RoleInfo,
    UserInfo,
)
from app.schemas.stats import (
    DashboardStatsResponse,
)

__all__ = [
    "BaseSchema",
    "CreateSchema",
    "UpdateSchema",
    "ResponseSchema",
    "IDResponse",
    "ListResponseSchema",
    "PaginationParams",
    "MessageResponse",
    "ErrorDetail",
    "ErrorResponse",
    "PositionCreate",
    "PositionUpdate",
    "PositionResponse",
    "PositionListResponse",
    "DepartmentCreate",
    "DepartmentUpdate",
    "DepartmentResponse",
    "DepartmentListResponse",
    "LoginRequest",
    "TokenResponse",
    "RefreshRequest",
    "RoleInfo",
    "UserInfo",
    "DashboardStatsResponse",
]
