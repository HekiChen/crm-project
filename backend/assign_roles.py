"""
Simple script to assign roles to existing employees.
"""
import asyncio
from datetime import datetime
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.employee import Employee
from app.models.role import Role
from app.models.employee_role import EmployeeRole


async def assign_roles():
    """Assign roles to existing employees."""
    async for session in get_db():
        try:
            # Get all employees
            result = await session.execute(select(Employee))
            employees = result.scalars().all()
            
            if not employees:
                print("❌ No employees found in database")
                return
            
            print(f"\n✅ Found {len(employees)} employees:")
            for emp in employees:
                print(f"  - {emp.email} ({emp.first_name} {emp.last_name})")
            
            # Check if roles exist
            result = await session.execute(select(Role))
            roles = result.scalars().all()
            
            admin_role = next((r for r in roles if r.code == "ADMIN"), None)
            manager_role = next((r for r in roles if r.code == "MANAGER"), None)
            
            if not admin_role:
                print("\n📝 Creating ADMIN role...")
                admin_role = Role(
                    id=uuid4(),
                    name="Administrator",
                    code="ADMIN",
                    description="System administrator with full access",
                    is_system_role=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    is_deleted=False,
                )
                session.add(admin_role)
                await session.flush()
                print(f"✅ Created ADMIN role")
            
            if not manager_role:
                print("📝 Creating MANAGER role...")
                manager_role = Role(
                    id=uuid4(),
                    name="Manager",
                    code="MANAGER",
                    description="Department manager",
                    is_system_role=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    is_deleted=False,
                )
                session.add(manager_role)
                await session.flush()
                print(f"✅ Created MANAGER role")
            
            if roles:
                print(f"\n✅ Available roles:")
                if admin_role:
                    print(f"  - Administrator (ADMIN)")
                if manager_role:
                    print(f"  - Manager (MANAGER)")
            
            # Assign roles to employees
            print("\n=== Assigning Roles ===")
            
            for i, employee in enumerate(employees):
                # Assign MANAGER role to first employee, ADMIN to others
                if i == 0:
                    role_to_assign = manager_role
                    role_name = "MANAGER"
                else:
                    role_to_assign = admin_role
                    role_name = "ADMIN"
                
                # Check if already assigned
                result = await session.execute(
                    select(EmployeeRole)
                    .where(EmployeeRole.employee_id == employee.id)
                    .where(EmployeeRole.role_id == role_to_assign.id)
                )
                existing = result.scalar_one_or_none()
                
                if existing:
                    print(f"  - {employee.email}: Already has {role_name} role")
                else:
                    employee_role = EmployeeRole(
                        id=uuid4(),
                        employee_id=employee.id,
                        role_id=role_to_assign.id,
                        assigned_at=datetime.now(),
                        assigned_by_id=employee.id,  # Self-assigned
                    )
                    session.add(employee_role)
                    print(f"  - {employee.email}: Assigned {role_name} role ✅")
            
            await session.commit()
            
            # Verify assignments
            print("\n=== Verification ===")
            result = await session.execute(
                select(Employee)
                .options(selectinload(Employee.employee_roles).selectinload(EmployeeRole.role))
            )
            employees = result.scalars().all()
            
            for emp in employees:
                print(f"\n{emp.email}:")
                for er in emp.employee_roles:
                    print(f"  ✅ {er.role.name} ({er.role.code})")
            
            print("\n✅ Role assignment complete!")
            print("\n💡 Login with any of these users to test the manager role.")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            await session.rollback()
            raise
        finally:
            break


if __name__ == "__main__":
    asyncio.run(assign_roles())
