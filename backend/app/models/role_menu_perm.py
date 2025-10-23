"""
RoleMenuPerm model for CRM system.

Junction table for many-to-many relationship between Role and Menu with granular permissions.
"""
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.role import Role
    from app.models.menu import Menu


class RoleMenuPerm(BaseModel):
    """
    RoleMenuPerm junction table for Role-Menu with granular permissions.
    
    Defines what actions a role can perform on each menu item.
    Includes soft delete and audit trail for permission change tracking.
    """
    __tablename__ = "role_menu_perms"
    __table_args__ = (
        UniqueConstraint("role_id", "menu_id", name="uq_role_menu"),
    )
    
    # Foreign keys
    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Role receiving these permissions"
    )
    
    menu_id: Mapped[UUID] = mapped_column(
        ForeignKey("menus.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Menu item being accessed"
    )
    
    # Permission flags
    can_read: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Permission to read/view this menu item"
    )
    
    can_write: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Permission to create/update via this menu item"
    )
    
    can_delete: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Permission to delete via this menu item"
    )
    
    # Relationships
    role: Mapped["Role"] = relationship(
        "Role",
        back_populates="menu_permissions",
        foreign_keys=[role_id],
        lazy="select"
    )
    
    menu: Mapped["Menu"] = relationship(
        "Menu",
        back_populates="role_permissions",
        foreign_keys=[menu_id],
        lazy="select"
    )
    
    def __repr__(self) -> str:
        """String representation of RoleMenuPerm."""
        perms = []
        if self.can_read:
            perms.append("R")
        if self.can_write:
            perms.append("W")
        if self.can_delete:
            perms.append("D")
        perm_str = "".join(perms) if perms else "NONE"
        return f"<RoleMenuPerm(id={self.id}, role_id={self.role_id}, menu_id={self.menu_id}, perms='{perm_str}')>"
