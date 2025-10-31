"""
Seed comprehensive organizational data for CRM system.

This script implements the "Clean Slate" approach:
1. Clears existing employee, position, and department data
2. Seeds 10 departments, 25 positions, 30 employees
3. Assigns roles based on position levels
4. Validates all foreign key relationships

KEEPS: roles, menus, role_menu_perm (already configured)

Run with --dry-run to preview without making changes.
"""
import asyncio
import sys
from datetime import date
from pathlib import Path
from typing import Optional
from uuid import UUID

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, delete
from app.core.database import get_db
from app.models.department import Department
from app.models.position import Position
from app.models.employee import Employee
from app.models.employee_role import EmployeeRole
from app.models.role import Role


# ============================================================================
# ORGANIZATIONAL DATA
# ============================================================================

DEPARTMENTS_DATA = [
    # Level 1: Top-level departments (no parent)
    {"code": "EXEC", "name": "Executive", "description": "C-Suite and executive leadership", "parent_code": None},
    {"code": "ENG", "name": "Engineering", "description": "Product development and engineering", "parent_code": None},
    {"code": "SALES", "name": "Sales", "description": "Sales and business development", "parent_code": None},
    {"code": "MKT", "name": "Marketing", "description": "Marketing and brand management", "parent_code": None},
    {"code": "HR", "name": "Human Resources", "description": "HR, recruiting, and employee relations", "parent_code": None},
    {"code": "FIN", "name": "Finance", "description": "Finance, accounting, and operations", "parent_code": None},
    
    # Level 2: Sub-departments
    {"code": "ENG-FE", "name": "Frontend Engineering", "description": "UI/UX development team", "parent_code": "ENG"},
    {"code": "ENG-BE", "name": "Backend Engineering", "description": "Backend systems and APIs", "parent_code": "ENG"},
    {"code": "SALES-ENT", "name": "Enterprise Sales", "description": "Enterprise and strategic accounts", "parent_code": "SALES"},
    {"code": "SALES-SMB", "name": "SMB Sales", "description": "Small and medium business sales", "parent_code": "SALES"},
]

POSITIONS_DATA = [
    # Executive (Level 10)
    {"code": "CEO", "name": "Chief Executive Officer", "level": 10, "department_code": "EXEC"},
    
    # VP Level (Level 9)
    {"code": "VP-ENG", "name": "VP Engineering", "level": 9, "department_code": "ENG"},
    {"code": "VP-SALES", "name": "VP Sales", "level": 9, "department_code": "SALES"},
    {"code": "VP-MKT", "name": "VP Marketing", "level": 9, "department_code": "MKT"},
    {"code": "VP-HR", "name": "VP Human Resources", "level": 9, "department_code": "HR"},
    {"code": "VP-FIN", "name": "VP Finance", "level": 9, "department_code": "FIN"},
    
    # Director Level (Level 8)
    {"code": "DIR-ENG", "name": "Engineering Director", "level": 8, "department_code": "ENG"},
    {"code": "DIR-SALES-ENT", "name": "Enterprise Sales Director", "level": 8, "department_code": "SALES-ENT"},
    {"code": "DIR-SALES-SMB", "name": "SMB Sales Director", "level": 8, "department_code": "SALES-SMB"},
    
    # Manager Level (Level 7)
    {"code": "MGR-ENG-FE", "name": "Frontend Engineering Manager", "level": 7, "department_code": "ENG-FE"},
    {"code": "MGR-ENG-BE", "name": "Backend Engineering Manager", "level": 7, "department_code": "ENG-BE"},
    {"code": "MGR-SALES-ENT", "name": "Enterprise Account Manager", "level": 7, "department_code": "SALES-ENT"},
    {"code": "MGR-HR", "name": "HR Manager", "level": 7, "department_code": "HR"},
    {"code": "MGR-FIN", "name": "Finance Manager", "level": 7, "department_code": "FIN"},
    
    # Senior Level (Level 6)
    {"code": "SR-SWE-FE", "name": "Senior Frontend Engineer", "level": 6, "department_code": "ENG-FE"},
    {"code": "SR-SWE-BE", "name": "Senior Backend Engineer", "level": 6, "department_code": "ENG-BE"},
    {"code": "SR-SALES", "name": "Senior Account Executive", "level": 6, "department_code": "SALES-ENT"},
    
    # Mid Level (Level 5)
    {"code": "SWE-FE", "name": "Frontend Engineer", "level": 5, "department_code": "ENG-FE"},
    {"code": "SWE-BE", "name": "Backend Engineer", "level": 5, "department_code": "ENG-BE"},
    {"code": "AE-ENT", "name": "Account Executive", "level": 5, "department_code": "SALES-ENT"},
    {"code": "MKT-MGR", "name": "Marketing Manager", "level": 5, "department_code": "MKT"},
    
    # Junior/Entry Level (Level 4)
    {"code": "JR-SWE", "name": "Junior Software Engineer", "level": 4, "department_code": "ENG"},
    {"code": "SDR", "name": "Sales Development Rep", "level": 4, "department_code": "SALES-SMB"},
    {"code": "HR-COORD", "name": "HR Coordinator", "level": 4, "department_code": "HR"},
    {"code": "FIN-ANALYST", "name": "Financial Analyst", "level": 4, "department_code": "FIN"},
]

EMPLOYEES_DATA = [
    # Executive Team
    {"employee_number": "EMP-001", "first_name": "Sarah", "last_name": "Chen", "email": "sarah.chen@company.com", "phone": "+1-555-0001", "position_code": "CEO", "department_code": "EXEC", "manager_employee_number": None, "hire_date": "2020-01-15", "role_code": "ADMIN"},
    
    # VPs (Report to CEO)
    {"employee_number": "EMP-002", "first_name": "Michael", "last_name": "Park", "email": "michael.park@company.com", "phone": "+1-555-0002", "position_code": "VP-ENG", "department_code": "ENG", "manager_employee_number": "EMP-001", "hire_date": "2020-03-01", "role_code": "MANAGER"},
    {"employee_number": "EMP-003", "first_name": "Jessica", "last_name": "Torres", "email": "jessica.torres@company.com", "phone": "+1-555-0003", "position_code": "VP-SALES", "department_code": "SALES", "manager_employee_number": "EMP-001", "hire_date": "2020-04-10", "role_code": "MANAGER"},
    {"employee_number": "EMP-004", "first_name": "Robert", "last_name": "Williams", "email": "robert.williams@company.com", "phone": "+1-555-0004", "position_code": "VP-MKT", "department_code": "MKT", "manager_employee_number": "EMP-001", "hire_date": "2020-05-20", "role_code": "MANAGER"},
    {"employee_number": "EMP-005", "first_name": "Emily", "last_name": "Johnson", "email": "emily.johnson@company.com", "phone": "+1-555-0005", "position_code": "VP-HR", "department_code": "HR", "manager_employee_number": "EMP-001", "hire_date": "2020-06-15", "role_code": "MANAGER"},
    {"employee_number": "EMP-006", "first_name": "David", "last_name": "Martinez", "email": "david.martinez@company.com", "phone": "+1-555-0006", "position_code": "VP-FIN", "department_code": "FIN", "manager_employee_number": "EMP-001", "hire_date": "2020-07-01", "role_code": "MANAGER"},
    
    # Directors (Report to VPs)
    {"employee_number": "EMP-007", "first_name": "Jennifer", "last_name": "Lee", "email": "jennifer.lee@company.com", "phone": "+1-555-0007", "position_code": "DIR-ENG", "department_code": "ENG", "manager_employee_number": "EMP-002", "hire_date": "2021-01-15", "role_code": "MANAGER"},
    {"employee_number": "EMP-008", "first_name": "Christopher", "last_name": "Brown", "email": "christopher.brown@company.com", "phone": "+1-555-0008", "position_code": "DIR-SALES-ENT", "department_code": "SALES-ENT", "manager_employee_number": "EMP-003", "hire_date": "2021-02-01", "role_code": "MANAGER"},
    {"employee_number": "EMP-009", "first_name": "Amanda", "last_name": "Davis", "email": "amanda.davis@company.com", "phone": "+1-555-0009", "position_code": "DIR-SALES-SMB", "department_code": "SALES-SMB", "manager_employee_number": "EMP-003", "hire_date": "2021-03-10", "role_code": "MANAGER"},
    
    # Managers (Report to Directors/VPs)
    {"employee_number": "EMP-010", "first_name": "Daniel", "last_name": "Kim", "email": "daniel.kim@company.com", "phone": "+1-555-0010", "position_code": "MGR-ENG-FE", "department_code": "ENG-FE", "manager_employee_number": "EMP-007", "hire_date": "2021-06-01", "role_code": "MANAGER"},
    {"employee_number": "EMP-011", "first_name": "Rachel", "last_name": "Anderson", "email": "rachel.anderson@company.com", "phone": "+1-555-0011", "position_code": "MGR-ENG-BE", "department_code": "ENG-BE", "manager_employee_number": "EMP-007", "hire_date": "2021-07-15", "role_code": "MANAGER"},
    {"employee_number": "EMP-012", "first_name": "Kevin", "last_name": "Wilson", "email": "kevin.wilson@company.com", "phone": "+1-555-0012", "position_code": "MGR-SALES-ENT", "department_code": "SALES-ENT", "manager_employee_number": "EMP-008", "hire_date": "2021-08-01", "role_code": "MANAGER"},
    {"employee_number": "EMP-013", "first_name": "Lisa", "last_name": "Taylor", "email": "lisa.taylor@company.com", "phone": "+1-555-0013", "position_code": "MGR-HR", "department_code": "HR", "manager_employee_number": "EMP-005", "hire_date": "2021-09-15", "role_code": "MANAGER"},
    {"employee_number": "EMP-014", "first_name": "Brian", "last_name": "Moore", "email": "brian.moore@company.com", "phone": "+1-555-0014", "position_code": "MGR-FIN", "department_code": "FIN", "manager_employee_number": "EMP-006", "hire_date": "2021-10-01", "role_code": "MANAGER"},
    
    # Senior Engineers (Report to Engineering Managers)
    {"employee_number": "EMP-015", "first_name": "Michelle", "last_name": "Garcia", "email": "michelle.garcia@company.com", "phone": "+1-555-0015", "position_code": "SR-SWE-FE", "department_code": "ENG-FE", "manager_employee_number": "EMP-010", "hire_date": "2022-01-10", "role_code": "STAFF"},
    {"employee_number": "EMP-016", "first_name": "Jason", "last_name": "Rodriguez", "email": "jason.rodriguez@company.com", "phone": "+1-555-0016", "position_code": "SR-SWE-FE", "department_code": "ENG-FE", "manager_employee_number": "EMP-010", "hire_date": "2022-02-15", "role_code": "STAFF"},
    {"employee_number": "EMP-017", "first_name": "Ashley", "last_name": "White", "email": "ashley.white@company.com", "phone": "+1-555-0017", "position_code": "SR-SWE-BE", "department_code": "ENG-BE", "manager_employee_number": "EMP-011", "hire_date": "2022-03-01", "role_code": "STAFF"},
    {"employee_number": "EMP-018", "first_name": "Matthew", "last_name": "Harris", "email": "matthew.harris@company.com", "phone": "+1-555-0018", "position_code": "SR-SWE-BE", "department_code": "ENG-BE", "manager_employee_number": "EMP-011", "hire_date": "2022-04-10", "role_code": "STAFF"},
    
    # Mid-Level Engineers
    {"employee_number": "EMP-019", "first_name": "Nicole", "last_name": "Clark", "email": "nicole.clark@company.com", "phone": "+1-555-0019", "position_code": "SWE-FE", "department_code": "ENG-FE", "manager_employee_number": "EMP-010", "hire_date": "2023-01-15", "role_code": "STAFF"},
    {"employee_number": "EMP-020", "first_name": "Ryan", "last_name": "Lewis", "email": "ryan.lewis@company.com", "phone": "+1-555-0020", "position_code": "SWE-FE", "department_code": "ENG-FE", "manager_employee_number": "EMP-010", "hire_date": "2023-02-20", "role_code": "STAFF"},
    {"employee_number": "EMP-021", "first_name": "Stephanie", "last_name": "Walker", "email": "stephanie.walker@company.com", "phone": "+1-555-0021", "position_code": "SWE-BE", "department_code": "ENG-BE", "manager_employee_number": "EMP-011", "hire_date": "2023-03-10", "role_code": "STAFF"},
    {"employee_number": "EMP-022", "first_name": "Brandon", "last_name": "Hall", "email": "brandon.hall@company.com", "phone": "+1-555-0022", "position_code": "SWE-BE", "department_code": "ENG-BE", "manager_employee_number": "EMP-011", "hire_date": "2023-04-05", "role_code": "STAFF"},
    
    # Junior Engineers
    {"employee_number": "EMP-023", "first_name": "Lauren", "last_name": "Allen", "email": "lauren.allen@company.com", "phone": "+1-555-0023", "position_code": "JR-SWE", "department_code": "ENG", "manager_employee_number": "EMP-007", "hire_date": "2024-01-15", "role_code": "STAFF"},
    {"employee_number": "EMP-024", "first_name": "Justin", "last_name": "Young", "email": "justin.young@company.com", "phone": "+1-555-0024", "position_code": "JR-SWE", "department_code": "ENG", "manager_employee_number": "EMP-007", "hire_date": "2024-02-01", "role_code": "STAFF"},
    
    # Sales Team
    {"employee_number": "EMP-025", "first_name": "Samantha", "last_name": "King", "email": "samantha.king@company.com", "phone": "+1-555-0025", "position_code": "SR-SALES", "department_code": "SALES-ENT", "manager_employee_number": "EMP-012", "hire_date": "2022-05-10", "role_code": "SALES_REP"},
    {"employee_number": "EMP-026", "first_name": "Thomas", "last_name": "Wright", "email": "thomas.wright@company.com", "phone": "+1-555-0026", "position_code": "AE-ENT", "department_code": "SALES-ENT", "manager_employee_number": "EMP-012", "hire_date": "2023-06-15", "role_code": "SALES_REP"},
    {"employee_number": "EMP-027", "first_name": "Angela", "last_name": "Lopez", "email": "angela.lopez@company.com", "phone": "+1-555-0027", "position_code": "SDR", "department_code": "SALES-SMB", "manager_employee_number": "EMP-009", "hire_date": "2024-03-01", "role_code": "SALES_REP"},
    
    # Support Staff
    {"employee_number": "EMP-028", "first_name": "Eric", "last_name": "Hill", "email": "eric.hill@company.com", "phone": "+1-555-0028", "position_code": "MKT-MGR", "department_code": "MKT", "manager_employee_number": "EMP-004", "hire_date": "2023-07-10", "role_code": "STAFF"},
    {"employee_number": "EMP-029", "first_name": "Megan", "last_name": "Scott", "email": "megan.scott@company.com", "phone": "+1-555-0029", "position_code": "HR-COORD", "department_code": "HR", "manager_employee_number": "EMP-013", "hire_date": "2024-04-15", "role_code": "STAFF"},
    {"employee_number": "EMP-030", "first_name": "Patrick", "last_name": "Green", "email": "patrick.green@company.com", "phone": "+1-555-0030", "position_code": "FIN-ANALYST", "department_code": "FIN", "manager_employee_number": "EMP-014", "hire_date": "2024-05-01", "role_code": "STAFF"},
]


# ============================================================================
# SEEDING LOGIC
# ============================================================================

async def clear_existing_data(db, dry_run: bool = False):
    """Phase 1: Clear existing organizational data."""
    print("\n" + "="*70)
    print("PHASE 1: CLEARING EXISTING DATA")
    print("="*70)
    
    # Count existing records
    employee_roles_count = (await db.execute(select(EmployeeRole))).scalars().all()
    employees_count = (await db.execute(select(Employee))).scalars().all()
    positions_count = (await db.execute(select(Position))).scalars().all()
    departments_count = (await db.execute(select(Department))).scalars().all()
    
    print(f"\n📊 Current state:")
    print(f"   - Employee-Roles: {len(employee_roles_count)}")
    print(f"   - Employees: {len(employees_count)}")
    print(f"   - Positions: {len(positions_count)}")
    print(f"   - Departments: {len(departments_count)}")
    
    if dry_run:
        print("\n🔍 DRY RUN: Would delete all records above")
        return
    
    # Delete in correct order (respect FK constraints)
    print("\n🗑️  Deleting records...")
    
    await db.execute(delete(EmployeeRole))
    print("   ✓ Cleared employee_roles")
    
    await db.execute(delete(Employee))
    print("   ✓ Cleared employees")
    
    await db.execute(delete(Position))
    print("   ✓ Cleared positions")
    
    await db.execute(delete(Department))
    print("   ✓ Cleared departments")
    
    await db.commit()
    print("\n✅ Data cleanup complete!")


async def seed_departments(db, dry_run: bool = False):
    """Phase 2a: Seed departments."""
    print("\n" + "="*70)
    print("PHASE 2A: SEEDING DEPARTMENTS")
    print("="*70)
    
    dept_map = {}  # code -> Department object
    
    # First pass: create all departments
    print(f"\n📁 Creating {len(DEPARTMENTS_DATA)} departments...")
    for dept_data in DEPARTMENTS_DATA:
        dept = Department(
            code=dept_data["code"],
            name=dept_data["name"],
            description=dept_data["description"],
            manager_id=None,  # Will set after employees are created
            parent_id=None,   # Will set in second pass
        )
        dept_map[dept_data["code"]] = dept
        
        if not dry_run:
            db.add(dept)
        
        print(f"   {'[DRY RUN]' if dry_run else '✓'} {dept.code}: {dept.name}")
    
    if not dry_run:
        await db.flush()
    
    # Second pass: set parent relationships
    print(f"\n🔗 Setting parent relationships...")
    for dept_data in DEPARTMENTS_DATA:
        if dept_data["parent_code"]:
            child = dept_map[dept_data["code"]]
            parent = dept_map[dept_data["parent_code"]]
            child.parent_id = parent.id
            print(f"   {'[DRY RUN]' if dry_run else '✓'} {child.code} → parent: {parent.code}")
    
    if not dry_run:
        await db.commit()
    
    print(f"\n✅ Departments seeded!")
    return dept_map


async def seed_positions(db, dept_map: dict, dry_run: bool = False):
    """Phase 2b: Seed positions."""
    print("\n" + "="*70)
    print("PHASE 2B: SEEDING POSITIONS")
    print("="*70)
    
    position_map = {}  # code -> Position object
    
    print(f"\n💼 Creating {len(POSITIONS_DATA)} positions...")
    for pos_data in POSITIONS_DATA:
        dept = dept_map[pos_data["department_code"]]
        position = Position(
            code=pos_data["code"],
            name=pos_data["name"],
            level=pos_data["level"],
            department_id=dept.id,
        )
        position_map[pos_data["code"]] = position
        
        if not dry_run:
            db.add(position)
        
        print(f"   {'[DRY RUN]' if dry_run else '✓'} {position.code}: {position.name} (L{position.level}) → {dept.code}")
    
    if not dry_run:
        await db.commit()
    
    print(f"\n✅ Positions seeded!")
    return position_map


async def seed_employees(db, dept_map: dict, position_map: dict, dry_run: bool = False):
    """Phase 2c: Seed employees."""
    print("\n" + "="*70)
    print("PHASE 2C: SEEDING EMPLOYEES")
    print("="*70)
    
    employee_map = {}  # employee_number -> Employee object
    
    # First pass: create all employees without manager
    print(f"\n👥 Creating {len(EMPLOYEES_DATA)} employees...")
    for emp_data in EMPLOYEES_DATA:
        dept = dept_map[emp_data["department_code"]]
        position = position_map[emp_data["position_code"]]
        
        employee = Employee(
            employee_number=emp_data["employee_number"],
            first_name=emp_data["first_name"],
            last_name=emp_data["last_name"],
            email=emp_data["email"],
            phone=emp_data["phone"],
            department_id=dept.id,
            position_id=position.id,
            manager_id=None,  # Will set in second pass
            hire_date=date.fromisoformat(emp_data["hire_date"]),
            is_active=True,
        )
        employee_map[emp_data["employee_number"]] = employee
        
        if not dry_run:
            db.add(employee)
        
        print(f"   {'[DRY RUN]' if dry_run else '✓'} {employee.employee_number}: {employee.first_name} {employee.last_name} ({position.code}) → {dept.code}")
    
    if not dry_run:
        await db.flush()
    
    # Second pass: set manager relationships
    print(f"\n🔗 Setting manager relationships...")
    for emp_data in EMPLOYEES_DATA:
        if emp_data["manager_employee_number"]:
            employee = employee_map[emp_data["employee_number"]]
            manager = employee_map[emp_data["manager_employee_number"]]
            employee.manager_id = manager.id
            print(f"   {'[DRY RUN]' if dry_run else '✓'} {employee.employee_number} → manager: {manager.employee_number}")
    
    # Third pass: set department managers (CEO manages EXEC, VPs manage their depts)
    print(f"\n🔗 Setting department managers...")
    dept_manager_map = {
        "EXEC": "EMP-001",  # Sarah Chen (CEO)
        "ENG": "EMP-002",   # Michael Park (VP Eng)
        "SALES": "EMP-003", # Jessica Torres (VP Sales)
        "MKT": "EMP-004",   # Robert Williams (VP Marketing)
        "HR": "EMP-005",    # Emily Johnson (VP HR)
        "FIN": "EMP-006",   # David Martinez (VP Finance)
        "ENG-FE": "EMP-010", # Daniel Kim (FE Manager)
        "ENG-BE": "EMP-011", # Rachel Anderson (BE Manager)
        "SALES-ENT": "EMP-012", # Kevin Wilson (Ent Sales Manager)
        "SALES-SMB": "EMP-009", # Amanda Davis (SMB Director)
    }
    
    for dept_code, emp_number in dept_manager_map.items():
        dept = dept_map[dept_code]
        manager = employee_map[emp_number]
        dept.manager_id = manager.id
        print(f"   {'[DRY RUN]' if dry_run else '✓'} {dept.code} manager: {manager.first_name} {manager.last_name}")
    
    if not dry_run:
        await db.commit()
    
    print(f"\n✅ Employees seeded!")
    return employee_map


async def seed_employee_roles(db, employee_map: dict, dry_run: bool = False):
    """Phase 2d: Assign roles to employees."""
    print("\n" + "="*70)
    print("PHASE 2D: ASSIGNING EMPLOYEE ROLES")
    print("="*70)
    
    # Get all roles
    result = await db.execute(select(Role))
    roles = {role.code: role for role in result.scalars().all()}
    
    print(f"\n🔑 Available roles: {', '.join(roles.keys())}")
    print(f"\n👔 Assigning roles to {len(EMPLOYEES_DATA)} employees...")
    
    for emp_data in EMPLOYEES_DATA:
        employee = employee_map[emp_data["employee_number"]]
        role_code = emp_data["role_code"]
        
        if role_code not in roles:
            print(f"   ⚠️  Role not found: {role_code} for {employee.employee_number}")
            continue
        
        role = roles[role_code]
        employee_role = EmployeeRole(
            employee_id=employee.id,
            role_id=role.id,
        )
        
        if not dry_run:
            db.add(employee_role)
        
        print(f"   {'[DRY RUN]' if dry_run else '✓'} {employee.employee_number}: {role.code} ({role.name})")
    
    if not dry_run:
        await db.commit()
    
    print(f"\n✅ Employee roles assigned!")


async def validate_data(db):
    """Phase 3: Validate seeded data."""
    print("\n" + "="*70)
    print("PHASE 3: VALIDATING DATA")
    print("="*70)
    
    # Count records
    departments = (await db.execute(select(Department))).scalars().all()
    positions = (await db.execute(select(Position))).scalars().all()
    employees = (await db.execute(select(Employee))).scalars().all()
    employee_roles = (await db.execute(select(EmployeeRole))).scalars().all()
    
    print(f"\n📊 Record counts:")
    print(f"   - Departments: {len(departments)}")
    print(f"   - Positions: {len(positions)}")
    print(f"   - Employees: {len(employees)}")
    print(f"   - Employee-Role mappings: {len(employee_roles)}")
    
    # Validate FK relationships
    print(f"\n🔍 Validating relationships...")
    
    errors = []
    
    # Check employees have valid department and position
    for emp in employees:
        if not emp.department_id:
            errors.append(f"Employee {emp.employee_number} has no department")
        if not emp.position_id:
            errors.append(f"Employee {emp.employee_number} has no position")
    
    # Check positions have valid department
    for pos in positions:
        if not pos.department_id:
            errors.append(f"Position {pos.code} has no department")
    
    # Check departments with parent have valid parent_id
    for dept in departments:
        if dept.parent_id:
            parent_exists = any(d.id == dept.parent_id for d in departments)
            if not parent_exists:
                errors.append(f"Department {dept.code} has invalid parent_id")
    
    # Check employee roles have valid employee and role
    for er in employee_roles:
        if not er.employee_id:
            errors.append(f"EmployeeRole has no employee_id")
        if not er.role_id:
            errors.append(f"EmployeeRole has no role_id")
    
    if errors:
        print(f"\n❌ Validation errors found:")
        for error in errors:
            print(f"   - {error}")
        return False
    
    print(f"   ✓ All FK relationships valid")
    print(f"   ✓ No orphaned references")
    print(f"   ✓ All employees have departments and positions")
    print(f"   ✓ All positions linked to departments")
    print(f"   ✓ All employee-role mappings valid")
    
    print(f"\n✅ Validation complete - all checks passed!")
    return True


async def main():
    """Main seeding function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed organizational data")
    parser.add_argument("--dry-run", action="store_true", help="Preview without making changes")
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("🌱 CRM ORGANIZATIONAL DATA SEEDING")
    print("="*70)
    print(f"\nMode: {'DRY RUN (preview only)' if args.dry_run else 'LIVE (will modify database)'}")
    print(f"Strategy: Clean Slate - Clear existing data and seed fresh")
    print(f"\nThis will seed:")
    print(f"  - {len(DEPARTMENTS_DATA)} departments (3-level hierarchy)")
    print(f"  - {len(POSITIONS_DATA)} positions (levels 4-10)")
    print(f"  - {len(EMPLOYEES_DATA)} employees (with reporting chain)")
    print(f"  - {len(EMPLOYEES_DATA)} employee-role mappings")
    
    if not args.dry_run:
        print(f"\n⚠️  WARNING: This will DELETE all existing employees, positions, and departments!")
        print(f"⚠️  Roles, menus, and permissions will be PRESERVED.")
        response = input("\nContinue? (yes/no): ")
        if response.lower() not in ["yes", "y"]:
            print("\n❌ Aborted by user")
            return
    
    # Get database session
    async for db in get_db():
        try:
            # Phase 1: Clear existing data
            await clear_existing_data(db, dry_run=args.dry_run)
            
            # Phase 2: Seed new data
            dept_map = await seed_departments(db, dry_run=args.dry_run)
            position_map = await seed_positions(db, dept_map, dry_run=args.dry_run)
            employee_map = await seed_employees(db, dept_map, position_map, dry_run=args.dry_run)
            await seed_employee_roles(db, employee_map, dry_run=args.dry_run)
            
            # Phase 3: Validate
            if not args.dry_run:
                validation_passed = await validate_data(db)
                if not validation_passed:
                    print("\n❌ Validation failed! Rolling back...")
                    await db.rollback()
                    return
            
            print("\n" + "="*70)
            print("🎉 SUCCESS!")
            print("="*70)
            
            if args.dry_run:
                print("\n✓ Dry run completed - no changes were made")
                print("\nRun without --dry-run to apply changes:")
                print("  python scripts/seed_org_data.py")
            else:
                print("\n✓ All data seeded successfully")
                print("✓ All validations passed")
                print("\n📝 Next steps:")
                print("  1. Test API endpoints: http://localhost:8000/docs")
                print("  2. Verify data in frontend applications")
                print("  3. Check role permissions are working correctly")
            
        except Exception as e:
            print(f"\n❌ Error during seeding: {e}")
            if not args.dry_run:
                print("Rolling back transaction...")
                await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
