"""
Tests for base service class.
"""
import pytest
from uuid import uuid4, UUID

from sqlalchemy import select

from app.models.base import BaseModel
from app.schemas.base import CreateSchema, UpdateSchema, ResponseSchema, PaginationParams
from app.services.base import BaseService


# Test model for testing
class TestUser(BaseModel):
    """Test user model."""
    __tablename__ = "test_users"
    
    from sqlalchemy.orm import Mapped, mapped_column
    from sqlalchemy import String
    
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)


# Test schemas
class TestUserCreate(CreateSchema):
    """Test user create schema."""
    username: str
    email: str


class TestUserUpdate(UpdateSchema):
    """Test user update schema."""
    username: str | None = None
    email: str | None = None


class TestUserResponse(ResponseSchema):
    """Test user response schema."""
    username: str
    email: str


# Test service
class TestUserService(BaseService[TestUser, TestUserCreate, TestUserUpdate, TestUserResponse]):
    """Test user service."""
    pass


@pytest.fixture
async def service(db_session):
    """Create test service."""
    # Create table
    from app.core.database import Base
    async with db_session.bind.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    return TestUserService(TestUser, db_session)


@pytest.fixture
def user_create():
    """Create user data."""
    return TestUserCreate(
        username="testuser",
        email="test@example.com",
    )


@pytest.fixture
def admin_id():
    """Admin user ID."""
    return uuid4()


class TestServiceCreate:
    """Test cases for service create method."""
    
    async def test_create_basic(self, service, user_create):
        """Test basic create operation."""
        user = await service.create(user_create)
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.created_at is not None
        assert user.updated_at is not None
        assert user.is_deleted is False
    
    async def test_create_with_audit(self, service, user_create, admin_id):
        """Test create with audit trail."""
        user = await service.create(user_create, created_by_id=admin_id)
        
        assert user.created_by_id == admin_id
        assert user.updated_by_id is None
    
    async def test_create_no_commit(self, service, user_create):
        """Test create without committing."""
        user = await service.create(user_create, commit=False)
        
        # Should be in session but not committed
        assert user.id is not None
        
        # Rollback
        await service.db.rollback()
        
        # Should not exist after rollback
        result = await service.db.execute(select(TestUser))
        users = result.scalars().all()
        assert len(users) == 0


class TestServiceGetById:
    """Test cases for service get_by_id method."""
    
    async def test_get_by_id_existing(self, service, user_create):
        """Test get by ID for existing record."""
        # Create user
        user = await service.create(user_create)
        user_id = user.id
        
        # Get user
        retrieved_user = await service.get_by_id(user_id)
        
        assert retrieved_user is not None
        assert retrieved_user.id == user_id
        assert retrieved_user.username == "testuser"
    
    async def test_get_by_id_not_found(self, service):
        """Test get by ID for non-existent record."""
        user = await service.get_by_id(uuid4())
        
        assert user is None
    
    async def test_get_by_id_soft_deleted(self, service, user_create):
        """Test get by ID for soft-deleted record."""
        # Create and soft delete user
        user = await service.create(user_create)
        user_id = user.id
        await service.delete(user_id)
        
        # Should not be found by default
        user = await service.get_by_id(user_id)
        assert user is None
        
        # Should be found with include_deleted
        user = await service.get_by_id(user_id, include_deleted=True)
        assert user is not None
        assert user.is_deleted is True


class TestServiceGetList:
    """Test cases for service get_list method."""
    
    async def test_get_list_empty(self, service):
        """Test get list with no records."""
        pagination = PaginationParams(page=1, page_size=10)
        result = await service.get_list(pagination=pagination)
        
        assert result.total == 0
        assert len(result.data) == 0
        assert result.page == 1
        assert result.total_pages == 0
    
    async def test_get_list_with_data(self, service):
        """Test get list with multiple records."""
        # Create multiple users
        for i in range(5):
            user_create = TestUserCreate(
                username=f"user{i}",
                email=f"user{i}@example.com",
            )
            await service.create(user_create)
        
        # Get list
        pagination = PaginationParams(page=1, page_size=10)
        result = await service.get_list(pagination=pagination)
        
        assert result.total == 5
        assert len(result.data) == 5
        assert result.has_next is False
        assert result.has_previous is False
    
    async def test_get_list_pagination(self, service):
        """Test get list with pagination."""
        # Create 25 users
        for i in range(25):
            user_create = TestUserCreate(
                username=f"user{i}",
                email=f"user{i}@example.com",
            )
            await service.create(user_create)
        
        # Get first page
        pagination = PaginationParams(page=1, page_size=10)
        result = await service.get_list(pagination=pagination)
        
        assert result.total == 25
        assert len(result.data) == 10
        assert result.page == 1
        assert result.total_pages == 3
        assert result.has_next is True
        assert result.has_previous is False
        
        # Get second page
        pagination = PaginationParams(page=2, page_size=10)
        result = await service.get_list(pagination=pagination)
        
        assert len(result.data) == 10
        assert result.has_next is True
        assert result.has_previous is True
    
    async def test_get_list_with_filters(self, service):
        """Test get list with filters."""
        # Create users
        user1 = await service.create(TestUserCreate(username="john", email="john@example.com"))
        user2 = await service.create(TestUserCreate(username="jane", email="jane@example.com"))
        
        # Filter by username
        pagination = PaginationParams(page=1, page_size=10)
        result = await service.get_list(
            pagination=pagination,
            filters={"username": "john"},
        )
        
        assert result.total == 1
        assert result.data[0].username == "john"
    
    async def test_get_list_exclude_deleted(self, service, user_create):
        """Test get list excludes soft-deleted records."""
        # Create and soft delete one user
        user1 = await service.create(user_create)
        await service.delete(user1.id)
        
        # Create another user
        user2 = await service.create(TestUserCreate(username="active", email="active@example.com"))
        
        # Get list (should only have active user)
        pagination = PaginationParams(page=1, page_size=10)
        result = await service.get_list(pagination=pagination)
        
        assert result.total == 1
        assert result.data[0].username == "active"
        
        # Get list with deleted
        result = await service.get_list(pagination=pagination, include_deleted=True)
        assert result.total == 2
    
    async def test_get_list_sorting(self, service):
        """Test get list with sorting."""
        # Create users
        await service.create(TestUserCreate(username="charlie", email="charlie@example.com"))
        await service.create(TestUserCreate(username="alice", email="alice@example.com"))
        await service.create(TestUserCreate(username="bob", email="bob@example.com"))
        
        # Sort by username ascending
        pagination = PaginationParams(page=1, page_size=10, sort_by="username", sort_order="asc")
        result = await service.get_list(pagination=pagination)
        
        assert result.data[0].username == "alice"
        assert result.data[1].username == "bob"
        assert result.data[2].username == "charlie"


class TestServiceUpdate:
    """Test cases for service update method."""
    
    async def test_update_basic(self, service, user_create):
        """Test basic update operation."""
        # Create user
        user = await service.create(user_create)
        user_id = user.id
        original_updated_at = user.updated_at
        
        # Update user
        update_data = TestUserUpdate(username="newname")
        updated_user = await service.update(user_id, update_data)
        
        assert updated_user is not None
        assert updated_user.username == "newname"
        assert updated_user.email == "test@example.com"  # Unchanged
        assert updated_user.updated_at > original_updated_at
    
    async def test_update_with_audit(self, service, user_create, admin_id):
        """Test update with audit trail."""
        user = await service.create(user_create)
        
        update_data = TestUserUpdate(email="new@example.com")
        updated_user = await service.update(user.id, update_data, updated_by_id=admin_id)
        
        assert updated_user.email == "new@example.com"
        assert updated_user.updated_by_id == admin_id
    
    async def test_update_not_found(self, service):
        """Test update for non-existent record."""
        update_data = TestUserUpdate(username="test")
        result = await service.update(uuid4(), update_data)
        
        assert result is None
    
    async def test_update_partial(self, service, user_create):
        """Test partial update (only some fields)."""
        user = await service.create(user_create)
        
        # Only update email
        update_data = TestUserUpdate(email="newemail@example.com")
        updated_user = await service.update(user.id, update_data)
        
        assert updated_user.username == "testuser"  # Unchanged
        assert updated_user.email == "newemail@example.com"


class TestServiceDelete:
    """Test cases for service delete methods."""
    
    async def test_soft_delete(self, service, user_create):
        """Test soft delete operation."""
        user = await service.create(user_create)
        user_id = user.id
        
        # Soft delete
        result = await service.delete(user_id)
        
        assert result is True
        
        # Verify soft deleted
        user = await service.get_by_id(user_id, include_deleted=True)
        assert user is not None
        assert user.is_deleted is True
        assert user.deleted_at is not None
    
    async def test_soft_delete_with_audit(self, service, user_create, admin_id):
        """Test soft delete with audit trail."""
        user = await service.create(user_create)
        
        await service.delete(user.id, deleted_by_id=admin_id)
        
        user = await service.get_by_id(user.id, include_deleted=True)
        assert user.updated_by_id == admin_id
    
    async def test_soft_delete_not_found(self, service):
        """Test soft delete for non-existent record."""
        result = await service.delete(uuid4())
        
        assert result is False
    
    async def test_hard_delete(self, service, user_create):
        """Test hard delete operation."""
        user = await service.create(user_create)
        user_id = user.id
        
        # Hard delete
        result = await service.hard_delete(user_id)
        
        assert result is True
        
        # Verify completely deleted
        user = await service.get_by_id(user_id, include_deleted=True)
        assert user is None
    
    async def test_hard_delete_not_found(self, service):
        """Test hard delete for non-existent record."""
        result = await service.hard_delete(uuid4())
        
        assert result is False


class TestServiceRestore:
    """Test cases for service restore method."""
    
    async def test_restore(self, service, user_create):
        """Test restore soft-deleted record."""
        user = await service.create(user_create)
        user_id = user.id
        
        # Soft delete
        await service.delete(user_id)
        
        # Restore
        restored_user = await service.restore(user_id)
        
        assert restored_user is not None
        assert restored_user.is_deleted is False
        assert restored_user.deleted_at is None
    
    async def test_restore_not_deleted(self, service, user_create):
        """Test restore for non-deleted record."""
        user = await service.create(user_create)
        
        # Try to restore (should return None since not deleted)
        result = await service.restore(user.id)
        
        assert result is None
    
    async def test_restore_not_found(self, service):
        """Test restore for non-existent record."""
        result = await service.restore(uuid4())
        
        assert result is None


class TestServiceUtilities:
    """Test cases for service utility methods."""
    
    async def test_exists_true(self, service, user_create):
        """Test exists method returns True."""
        user = await service.create(user_create)
        
        result = await service.exists(filters={"username": "testuser"})
        
        assert result is True
    
    async def test_exists_false(self, service):
        """Test exists method returns False."""
        result = await service.exists(filters={"username": "nonexistent"})
        
        assert result is False
    
    async def test_exists_soft_deleted(self, service, user_create):
        """Test exists excludes soft-deleted by default."""
        user = await service.create(user_create)
        await service.delete(user.id)
        
        result = await service.exists(filters={"username": "testuser"})
        assert result is False
        
        result = await service.exists(filters={"username": "testuser"}, include_deleted=True)
        assert result is True
    
    async def test_count_empty(self, service):
        """Test count with no records."""
        count = await service.count()
        
        assert count == 0
    
    async def test_count_with_data(self, service):
        """Test count with multiple records."""
        for i in range(5):
            await service.create(TestUserCreate(username=f"user{i}", email=f"user{i}@example.com"))
        
        count = await service.count()
        
        assert count == 5
    
    async def test_count_with_filters(self, service):
        """Test count with filters."""
        await service.create(TestUserCreate(username="john", email="john@example.com"))
        await service.create(TestUserCreate(username="jane", email="jane@example.com"))
        
        count = await service.count(filters={"username": "john"})
        
        assert count == 1
    
    async def test_count_exclude_deleted(self, service, user_create):
        """Test count excludes soft-deleted records."""
        user = await service.create(user_create)
        await service.create(TestUserCreate(username="active", email="active@example.com"))
        await service.delete(user.id)
        
        count = await service.count()
        assert count == 1
        
        count = await service.count(include_deleted=True)
        assert count == 2
