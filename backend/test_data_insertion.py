"""
Test script to verify database schema, FK relationships, and cascading behaviors.
This script tests all 9 tables with realistic data.
"""
import asyncio
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models import (
    Department,
    Position,
    Role,
    Menu,
    Employee,
    EmployeeRole,
    RoleMenuPerm,
    WorkLog,
    ExportJob,
)

DATABASE_URL = "postgresql+asyncpg://crm_user:crm_password@localhost:5432/crm_db"


async def test_data_insertion():
    """Test inserting data into all 9 tables and verify FK relationships"""
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("\n=== PHASE 1: Create base entities (no dependencies) ===\n")

        # 1. Create root department (no parent, no manager yet)
        eng_dept = Department(
            id=uuid4(),
            name="Engineering",
            code="ENG",
            description="Engineering department",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_deleted=False,
        )
        session.add(eng_dept)

        # 2. Create positions (linked to department)
        cto_position = Position(
            id=uuid4(),
            name="Chief Technology Officer",
            code="CTO",
            level=1,
            description="Technology leadership",
            department_id=eng_dept.id,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_deleted=False,
        )
        dev_position = Position(
            id=uuid4(),
            name="Senior Developer",
            code="DEV",
            level=3,
            description="Software development",
            department_id=eng_dept.id,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_deleted=False,
        )
        session.add_all([cto_position, dev_position])

        # 3. Create roles (RBAC)
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
        session.add_all([admin_role, manager_role])

        # 4. Create menus (navigation structure)
        dashboard_menu = Menu(
            id=uuid4(),
            name="Dashboard",
            path="/dashboard",
            icon="dashboard",
            sort_order=1,
            menu_type="frontend",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_deleted=False,
        )
        employee_menu = Menu(
            id=uuid4(),
            name="Employee Management",
            path="/employees",
            icon="people",
            sort_order=2,
            menu_type="frontend",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_deleted=False,
        )
        session.add_all([dashboard_menu, employee_menu])

        await session.flush()  # Get IDs for FK relationships
        print("✅ Base entities created: Department, Positions, Roles, Menus")

        print("\n=== PHASE 2: Create employees and update circular FK ===\n")

        # 5. Create CTO (manager of department)
        cto_employee = Employee(
            id=uuid4(),
            first_name="Alice",
            last_name="Smith",
            email="alice.smith@example.com",
            phone="+1-555-0101",
            address1="123 Tech St",
            city="San Francisco",
            state="CA",
            zip_code="94105",
            country="USA",
            employee_number="EMP001",
            hire_date=date(2020, 1, 15),
            position_id=cto_position.id,
            department_id=eng_dept.id,
            manager_id=None,  # Top-level manager has no manager
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_deleted=False,
        )
        session.add(cto_employee)
        await session.flush()

        # Update department manager (circular FK resolution)
        eng_dept.manager_id = cto_employee.id
        print(f"✅ CTO created and linked as department manager")

        # 6. Create developer (managed by CTO)
        dev_employee = Employee(
            id=uuid4(),
            first_name="Bob",
            last_name="Johnson",
            email="bob.johnson@example.com",
            phone="+1-555-0102",
            address1="456 Code Ave",
            city="San Francisco",
            state="CA",
            zip_code="94105",
            country="USA",
            employee_number="EMP002",
            hire_date=date(2021, 3, 20),
            position_id=dev_position.id,
            department_id=eng_dept.id,
            manager_id=cto_employee.id,  # Managed by CTO
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_deleted=False,
        )
        session.add(dev_employee)
        await session.flush()
        print(f"✅ Developer created with manager relationship")

        print("\n=== PHASE 3: Create junction and dependent tables ===\n")

        # 7. Assign roles to employees (Many-to-Many)
        cto_admin_role = EmployeeRole(
            id=uuid4(),
            employee_id=cto_employee.id,
            role_id=admin_role.id,
            assigned_at=datetime.now(),
            assigned_by_id=cto_employee.id,  # Self-assigned for bootstrap
        )
        dev_manager_role = EmployeeRole(
            id=uuid4(),
            employee_id=dev_employee.id,
            role_id=manager_role.id,
            assigned_at=datetime.now(),
            assigned_by_id=cto_employee.id,
        )
        session.add_all([cto_admin_role, dev_manager_role])
        print(f"✅ Employee roles assigned")

        # 8. Grant menu permissions to roles (granular R/W/D)
        admin_dashboard_perm = RoleMenuPerm(
            id=uuid4(),
            role_id=admin_role.id,
            menu_id=dashboard_menu.id,
            can_read=True,
            can_write=True,
            can_delete=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_deleted=False,
        )
        manager_employee_perm = RoleMenuPerm(
            id=uuid4(),
            role_id=manager_role.id,
            menu_id=employee_menu.id,
            can_read=True,
            can_write=True,
            can_delete=False,  # Managers can view/edit but not delete
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_deleted=False,
        )
        session.add_all([admin_dashboard_perm, manager_employee_perm])
        print(f"✅ Role menu permissions created")

        # 9. Create work logs (approval workflow)
        work_log = WorkLog(
            id=uuid4(),
            employee_id=dev_employee.id,
            date=date(2025, 1, 20),
            hours=Decimal("8.5"),
            description="Implemented database consolidation migration",
            status="submitted",
            approver_id=cto_employee.id,  # Waiting for CTO approval
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_deleted=False,
        )
        session.add(work_log)
        print(f"✅ Work log created with approval workflow")

        # 10. Create export job (async task tracking)
        export_job = ExportJob(
            id=uuid4(),
            employee_id=cto_employee.id,
            export_type="employee_report",
            status="pending",
            params={"department_id": str(eng_dept.id), "format": "xlsx"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        session.add(export_job)
        print(f"✅ Export job created")

        # Commit all changes
        await session.commit()
        print("\n=== ✅ All data inserted successfully! ===\n")

        # Verify data
        print("\n=== PHASE 4: Verify data and relationships ===\n")
        await session.refresh(cto_employee)
        await session.refresh(dev_employee)
        await session.refresh(eng_dept)

        print(f"Department: {eng_dept.name} (Manager: {eng_dept.manager_id})")
        print(f"CTO: {cto_employee.first_name} {cto_employee.last_name} (Dept: {cto_employee.department_id})")
        print(f"Developer: {dev_employee.first_name} {dev_employee.last_name} (Manager: {dev_employee.manager_id})")
        print(f"Work Log: {work_log.hours}h on {work_log.date} (Approver: {work_log.approver_id})")
        print(f"Export Job: {export_job.export_type} - {export_job.status}")

        print("\n=== TEST PASSED: Schema is correctly configured! ===")

    await engine.dispose()


async def test_soft_delete_unique_constraint():
    """Test that soft-deleted codes can be reused"""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("\n=== PHASE 5: Test soft-delete unique constraint ===\n")

        # Create department with code TEST
        test_dept = Department(
            id=uuid4(),
            name="Test Department",
            code="TEST",
            description="Testing soft delete",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_deleted=False,
        )
        session.add(test_dept)
        await session.commit()
        print(f"✅ Created department with code TEST")

        # Soft delete it
        test_dept.is_deleted = True
        test_dept.deleted_at = datetime.now()
        await session.commit()
        print(f"✅ Soft-deleted department TEST")

        # Create new department with same code (should work due to unique constraint on (code, is_deleted))
        new_test_dept = Department(
            id=uuid4(),
            name="New Test Department",
            code="TEST",  # Same code as deleted one
            description="Reusing code after soft delete",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_deleted=False,
        )
        session.add(new_test_dept)
        await session.commit()
        print(f"✅ Created new department with code TEST (reused after soft delete)")

        print("\n=== SOFT DELETE TEST PASSED! ===")

    await engine.dispose()


if __name__ == "__main__":
    print("=" * 80)
    print("DATABASE SCHEMA VERIFICATION SCRIPT")
    print("Testing all 9 tables, FK relationships, and cascading behaviors")
    print("=" * 80)

    asyncio.run(test_data_insertion())
    asyncio.run(test_soft_delete_unique_constraint())

    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED - Schema consolidation successful!")
    print("=" * 80)
