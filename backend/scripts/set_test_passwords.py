"""
Set password for test users.

Run this script to set a password for the admin test user.
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


async def set_test_passwords():
    """Set passwords for test users."""
    print("🔐 Setting passwords for test users...")
    
    # Get database session
    async for db in get_db():
        # Define users and their passwords
        users_passwords = [
            ("test1@email.com", "admin123", "Admin user"),
            ("test@email.com", "manager123", "Manager user"),
        ]
        
        for email, password, description in users_passwords:
            # Find user
            result = await db.execute(
                select(Employee).where(Employee.email == email)
            )
            employee = result.scalar_one_or_none()
            
            if not employee:
                print(f"⚠️  User not found: {email}")
                continue
            
            # Hash password and update
            password_hash = get_password_hash(password)
            await db.execute(
                update(Employee)
                .where(Employee.id == employee.id)
                .values(password_hash=password_hash)
            )
            
            print(f"✅ Set password for {description}: {email}")
            print(f"   Password: {password}")
        
        await db.commit()
        
        print(f"\n{'='*60}")
        print(f"✅ Passwords set successfully!")
        print(f"\n📝 Login Credentials:")
        print(f"{'='*60}")
        for email, password, description in users_passwords:
            print(f"{description}:")
            print(f"  Email: {email}")
            print(f"  Password: {password}")
            print()
        print(f"{'='*60}\n")
        
        break  # Exit after first session


if __name__ == "__main__":
    asyncio.run(set_test_passwords())
