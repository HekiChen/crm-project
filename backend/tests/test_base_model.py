"""
Tests for base model functionality.
"""
import pytest
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel
from app.core.database import get_db


# Test model for testing base functionality
class TestUser(BaseModel):
    """Test user model."""
    __tablename__ = "test_users"
    
    username: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)


@pytest.fixture
async def test_user(db_session):
    """Create a test user."""
    user = TestUser(
        username="testuser",
        email="test@example.com",
        created_by_id=uuid4()
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
class TestBaseModel:
    """Test cases for BaseModel."""
    
    async def test_create_model_with_defaults(self, db_session):
        """Test creating a model instance with default values."""
        user = TestUser(username="john", email="john@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Check that defaults are set
        assert isinstance(user.id, UUID)
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
        assert user.is_deleted is False
        assert user.deleted_at is None
        assert user.created_by_id is None
        assert user.updated_by_id is None
    
    async def test_create_model_with_audit_fields(self, db_session):
        """Test creating a model with audit fields."""
        creator_id = uuid4()
        user = TestUser(
            username="jane",
            email="jane@example.com",
            created_by_id=creator_id
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.created_by_id == creator_id
        assert user.updated_by_id is None
    
    async def test_soft_delete(self, test_user, db_session):
        """Test soft delete functionality."""
        deleter_id = uuid4()
        
        # Soft delete the user
        test_user.soft_delete(deleted_by_id=deleter_id)
        await db_session.commit()
        await db_session.refresh(test_user)
        
        # Verify soft delete fields
        assert test_user.is_deleted is True
        assert isinstance(test_user.deleted_at, datetime)
        assert test_user.updated_by_id == deleter_id
    
    async def test_restore_deleted(self, test_user, db_session):
        """Test restoring a soft-deleted record."""
        # First soft delete
        test_user.soft_delete()
        await db_session.commit()
        
        # Then restore
        restorer_id = uuid4()
        test_user.restore(restored_by_id=restorer_id)
        await db_session.commit()
        await db_session.refresh(test_user)
        
        # Verify restoration
        assert test_user.is_deleted is False
        assert test_user.deleted_at is None
        assert test_user.updated_by_id == restorer_id
    
    async def test_query_active_records(self, db_session):
        """Test querying only active records."""
        # Create active and deleted users
        user1 = TestUser(username="active1", email="active1@example.com")
        user2 = TestUser(username="active2", email="active2@example.com")
        user3 = TestUser(username="deleted1", email="deleted1@example.com")
        
        db_session.add_all([user1, user2, user3])
        await db_session.commit()
        
        # Soft delete user3
        user3.soft_delete()
        await db_session.commit()
        
        # Query active users
        active_users = await TestUser.active(db_session)
        
        # Should only return active users
        assert len(active_users) == 2
        assert all(not user.is_deleted for user in active_users)
    
    async def test_query_with_deleted(self, db_session):
        """Test querying all records including deleted."""
        # Create active and deleted users
        user1 = TestUser(username="user1", email="user1@example.com")
        user2 = TestUser(username="user2", email="user2@example.com")
        
        db_session.add_all([user1, user2])
        await db_session.commit()
        
        # Soft delete user2
        user2.soft_delete()
        await db_session.commit()
        
        # Query all users
        all_users = await TestUser.with_deleted(db_session)
        
        # Should return both users
        assert len(all_users) == 2
    
    async def test_query_deleted_only(self, db_session):
        """Test querying only deleted records."""
        # Create active and deleted users
        user1 = TestUser(username="keep1", email="keep1@example.com")
        user2 = TestUser(username="delete1", email="delete1@example.com")
        user3 = TestUser(username="delete2", email="delete2@example.com")
        
        db_session.add_all([user1, user2, user3])
        await db_session.commit()
        
        # Soft delete user2 and user3
        user2.soft_delete()
        user3.soft_delete()
        await db_session.commit()
        
        # Query deleted users
        deleted_users = await TestUser.deleted_only(db_session)
        
        # Should only return deleted users
        assert len(deleted_users) == 2
        assert all(user.is_deleted for user in deleted_users)
    
    async def test_count_active_records(self, db_session):
        """Test counting active records."""
        # Create users
        user1 = TestUser(username="count1", email="count1@example.com")
        user2 = TestUser(username="count2", email="count2@example.com")
        user3 = TestUser(username="count3", email="count3@example.com")
        
        db_session.add_all([user1, user2, user3])
        await db_session.commit()
        
        # Soft delete one user
        user3.soft_delete()
        await db_session.commit()
        
        # Count active users
        count = await TestUser.count_active(db_session)
        
        assert count == 2
    
    async def test_get_by_id(self, test_user, db_session):
        """Test getting a record by ID."""
        # Get existing user
        found_user = await TestUser.get_by_id(db_session, test_user.id)
        
        assert found_user is not None
        assert found_user.id == test_user.id
        assert found_user.username == test_user.username
    
    async def test_get_by_id_not_found(self, db_session):
        """Test getting a non-existent record."""
        fake_id = uuid4()
        found_user = await TestUser.get_by_id(db_session, fake_id)
        
        assert found_user is None
    
    async def test_get_by_id_exclude_deleted(self, test_user, db_session):
        """Test that soft-deleted records are excluded by default."""
        # Soft delete the user
        test_user.soft_delete()
        await db_session.commit()
        
        # Try to get the deleted user (should return None)
        found_user = await TestUser.get_by_id(db_session, test_user.id)
        
        assert found_user is None
    
    async def test_get_by_id_include_deleted(self, test_user, db_session):
        """Test getting soft-deleted records when explicitly requested."""
        # Soft delete the user
        test_user.soft_delete()
        await db_session.commit()
        
        # Get the deleted user with include_deleted=True
        found_user = await TestUser.get_by_id(
            db_session,
            test_user.id,
            include_deleted=True
        )
        
        assert found_user is not None
        assert found_user.id == test_user.id
        assert found_user.is_deleted is True
    
    async def test_updated_at_auto_update(self, test_user, db_session):
        """Test that updated_at is automatically updated on modifications."""
        original_updated_at = test_user.updated_at
        
        # Wait a moment and update
        import asyncio
        await asyncio.sleep(0.1)
        
        test_user.username = "updated_username"
        await db_session.commit()
        await db_session.refresh(test_user)
        
        # updated_at should be newer
        assert test_user.updated_at > original_updated_at
    
    async def test_repr(self, test_user):
        """Test string representation."""
        repr_str = repr(test_user)
        
        assert "TestUser" in repr_str
        assert str(test_user.id) in repr_str
    
    async def test_tablename_generation(self):
        """Test automatic table name generation."""
        # The TestUser class explicitly sets __tablename__
        # But BaseModel provides a method for auto-generation
        
        # Test the _get_tablename method directly
        assert TestUser._get_tablename() == "test_users"
