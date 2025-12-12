"""
Set default passwords for all employees.

This script sets a default password (Password123!) for all employees
who don't have a password set yet.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update
from app.core.database import get_db
from app.models.employee import Employee
from app.middleware.auth import get_password_hash


async def set_default_passwords(dry_run: bool = True):
    """
    Set default passwords for all employees without passwords.
    
    Args:
        dry_run: If True, only show what would be updated without making changes
    """
    default_password = "Password123!"
    
    print("\n" + "="*80)
    print("🔐 SET DEFAULT PASSWORDS FOR EMPLOYEES")
    print("="*80)
    
    if dry_run:
        print("⚠️  DRY RUN MODE - No changes will be made")
    else:
        print("✅ LIVE MODE - Passwords will be updated")
    
    print(f"📝 Default Password: {default_password}")
    print("="*80 + "\n")
    
    async for db in get_db():
        # Get all employees without passwords
        result = await db.execute(
            select(Employee)
            .where(Employee.is_deleted == False)
            .where(Employee.password_hash == None)
            .order_by(Employee.employee_number)
        )
        employees = result.scalars().all()
        
        if not employees:
            print("✓ All employees already have passwords set!")
            return
        
        print(f"Found {len(employees)} employees without passwords:\n")
        
        # Show employees that will be updated
        for i, emp in enumerate(employees, 1):
            print(f"{i:2d}. {emp.employee_number:<10} {emp.first_name} {emp.last_name:<20} ({emp.email})")
        
        print("\n" + "="*80)
        
        if dry_run:
            print(f"\n⚠️  DRY RUN: Would set password for {len(employees)} employees")
            print(f"   Password would be: {default_password}")
            print("\n   Run with --execute flag to actually set passwords:")
            print(f"   python scripts/set_default_passwords.py --execute")
        else:
            # Hash the default password
            hashed_password = get_password_hash(default_password)
            
            print(f"\n🔄 Setting passwords for {len(employees)} employees...")
            
            # Update all employees
            updated_count = 0
            for emp in employees:
                await db.execute(
                    update(Employee)
                    .where(Employee.id == emp.id)
                    .values(password_hash=hashed_password)
                )
                updated_count += 1
                print(f"   ✓ {emp.employee_number} - {emp.first_name} {emp.last_name}")
            
            await db.commit()
            
            print("\n" + "="*80)
            print(f"✅ SUCCESS! Set passwords for {updated_count} employees")
            print(f"   Default password: {default_password}")
            print("="*80 + "\n")
            print("⚠️  IMPORTANT: Users should change their passwords after first login!")
            
        break


if __name__ == "__main__":
    # Check if --execute flag is provided
    execute = "--execute" in sys.argv or "-e" in sys.argv
    
    asyncio.run(set_default_passwords(dry_run=not execute))
