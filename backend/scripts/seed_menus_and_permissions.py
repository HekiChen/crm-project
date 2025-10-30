"""
Seed menus and role-menu permissions for CRM system.

Run this script to populate the database with menu items and default permissions.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.core.database import get_db
from app.models.menu import Menu
from app.models.role import Role
from app.models.role_menu_perm import RoleMenuPerm


async def seed_menus_and_permissions():
    """Seed menus and permissions."""
    print("🌱 Starting database seeding...")
    
    # Get database session
    async for db in get_db():
        # Define menus to create
        menus_data = [
            {
                "name": "Dashboard",
                "path": "/dashboard",
                "icon": "dashboard",
                "menu_type": "frontend",
                "sort_order": 1,
                "is_active": True,
            },
            {
                "name": "Employees",
                "path": "/employees",
                "icon": "user",
                "menu_type": "frontend",
                "sort_order": 2,
                "is_active": True,
            },
            {
                "name": "Departments",
                "path": "/departments",
                "icon": "office-building",
                "menu_type": "frontend",
                "sort_order": 3,
                "is_active": True,
            },
            {
                "name": "Roles",
                "path": "/roles",
                "icon": "avatar",
                "menu_type": "frontend",
                "sort_order": 4,
                "is_active": True,
            },
            {
                "name": "Work Logs",
                "path": "/work-logs",
                "icon": "calendar",
                "menu_type": "frontend",
                "sort_order": 5,
                "is_active": True,
            },
        ]
        
        # Check existing menus
        result = await db.execute(select(Menu).where(Menu.is_deleted == False))
        existing_menus = {menu.path: menu for menu in result.scalars().all()}
        
        # Create or update menus
        created_menus = {}
        for menu_data in menus_data:
            if menu_data["path"] in existing_menus:
                menu = existing_menus[menu_data["path"]]
                print(f"✓ Menu exists: {menu.name} ({menu.path})")
            else:
                menu = Menu(**menu_data)
                db.add(menu)
                await db.flush()
                print(f"✓ Created menu: {menu.name} ({menu.path})")
            
            created_menus[menu.path] = menu
        
        await db.commit()
        
        # Get all roles
        result = await db.execute(select(Role))
        roles = {role.code: role for role in result.scalars().all()}
        
        # Define default permissions for each role
        # Format: role_code -> [(menu_path, can_read, can_write, can_delete)]
        default_permissions = {
            "ADMIN": [
                # Admin has full access to everything
                ("/dashboard", True, True, True),
                ("/employees", True, True, True),
                ("/departments", True, True, True),
                ("/roles", True, True, True),
                ("/work-logs", True, True, True),
            ],
            "MANAGER": [
                # Manager has full access except roles (read-only)
                ("/dashboard", True, True, True),
                ("/employees", True, True, True),
                ("/departments", True, True, True),
                ("/roles", True, False, False),  # Read-only
                ("/work-logs", True, True, True),
            ],
            "LEADER": [
                # Leader has read/write access, limited delete
                ("/dashboard", True, True, False),
                ("/employees", True, True, False),
                ("/departments", True, False, False),  # Read-only
                ("/roles", True, False, False),  # Read-only
                ("/work-logs", True, True, False),
            ],
            "STAFF": [
                # Staff has mostly read-only access
                ("/dashboard", True, False, False),
                ("/employees", True, False, False),  # Read-only
                ("/departments", True, False, False),  # Read-only
                ("/roles", False, False, False),  # No access
                ("/work-logs", True, True, False),  # Can edit their own logs
            ],
        }
        
        # Get existing permissions
        result = await db.execute(
            select(RoleMenuPerm).where(RoleMenuPerm.is_deleted == False)
        )
        existing_perms = {
            (perm.role_id, perm.menu_id): perm 
            for perm in result.scalars().all()
        }
        
        # Create permissions
        total_created = 0
        total_updated = 0
        total_skipped = 0
        
        for role_code, perms_list in default_permissions.items():
            if role_code not in roles:
                print(f"⚠️  Role not found: {role_code}")
                continue
            
            role = roles[role_code]
            print(f"\n📋 Processing role: {role.name} ({role.code})")
            
            for menu_path, can_read, can_write, can_delete in perms_list:
                if menu_path not in created_menus:
                    print(f"  ⚠️  Menu not found: {menu_path}")
                    continue
                
                menu = created_menus[menu_path]
                perm_key = (role.id, menu.id)
                
                if perm_key in existing_perms:
                    # Update existing permission
                    perm = existing_perms[perm_key]
                    if (perm.can_read != can_read or 
                        perm.can_write != can_write or 
                        perm.can_delete != can_delete):
                        perm.can_read = can_read
                        perm.can_write = can_write
                        perm.can_delete = can_delete
                        print(f"  ↻ Updated: {menu.name} (R:{can_read} W:{can_write} D:{can_delete})")
                        total_updated += 1
                    else:
                        print(f"  ✓ Unchanged: {menu.name}")
                        total_skipped += 1
                else:
                    # Create new permission
                    perm = RoleMenuPerm(
                        role_id=role.id,
                        menu_id=menu.id,
                        can_read=can_read,
                        can_write=can_write,
                        can_delete=can_delete,
                    )
                    db.add(perm)
                    print(f"  ✓ Created: {menu.name} (R:{can_read} W:{can_write} D:{can_delete})")
                    total_created += 1
        
        await db.commit()
        
        print(f"\n{'='*60}")
        print(f"✅ Seeding completed!")
        print(f"   - Menus: {len(created_menus)}")
        print(f"   - Permissions created: {total_created}")
        print(f"   - Permissions updated: {total_updated}")
        print(f"   - Permissions unchanged: {total_skipped}")
        print(f"{'='*60}\n")
        
        break  # Exit after first session


if __name__ == "__main__":
    asyncio.run(seed_menus_and_permissions())
