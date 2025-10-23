"""
Menu model for CRM system.

Represents navigation structure and permission boundaries.
"""
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.role_menu_perm import RoleMenuPerm


class Menu(BaseModel):
    """
    Menu model representing navigation items and permission boundaries.
    
    Menus define the structure of UI navigation and API endpoints.
    They support hierarchical nesting via parent_id and can have different types.
    """
    __tablename__ = "menus"
    
    # Core fields
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Menu item name displayed in UI (e.g., 'Employee Management')"
    )
    
    path: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="URL path or route identifier (e.g., '/employees', '/api/v1/employees')"
    )
    
    icon: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Icon identifier for UI display (e.g., 'user-icon', 'dashboard-icon')"
    )
    
    # Hierarchical structure - self-referential
    parent_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("menus.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Reference to parent menu for nested structure"
    )
    
    # Ordering and type
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        index=True,
        doc="Display order within same parent (lower = higher priority)"
    )
    
    menu_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="frontend",
        doc="Menu type: 'frontend', 'backend', or 'api'"
    )
    
    # Status field
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Whether menu item is active and visible"
    )
    
    # Relationships
    # Hierarchical relationships
    parent: Mapped[Optional["Menu"]] = relationship(
        "Menu",
        remote_side="[Menu.id]",
        back_populates="children",
        foreign_keys=[parent_id],
        lazy="select",
        doc="Parent menu in hierarchy"
    )
    
    children: Mapped[list["Menu"]] = relationship(
        "Menu",
        back_populates="parent",
        foreign_keys=[parent_id],
        lazy="select",
        doc="Child menus in hierarchy"
    )
    
    # Role permissions
    role_permissions: Mapped[list["RoleMenuPerm"]] = relationship(
        "RoleMenuPerm",
        back_populates="menu",
        cascade="all, delete-orphan",
        lazy="select",
        doc="Role permissions for this menu (many-to-many via junction table)"
    )
    
    def __repr__(self) -> str:
        """String representation of Menu."""
        return f"<Menu(id={self.id}, name='{self.name}', path='{self.path}', type='{self.menu_type}')>"
