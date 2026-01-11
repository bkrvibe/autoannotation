#!/usr/bin/env python3
"""Script to add a new user to the database."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.base import Base  # Import all models
from app.db.session import SessionLocal
from app.models.user import User, UserStatus, UserRole
from app.core.security import get_password_hash


def add_user(email: str, password: str, full_name: str = None, role: str = "annotation_runner"):
    """Add a new user to the database."""
    db = SessionLocal()
    
    # Check if user already exists
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        print(f"Error: User with email '{email}' already exists!")
        db.close()
        return False
    
    # Validate role
    valid_roles = ["annotation_runner", "tenant_admin", "ops", "admin"]
    if role not in valid_roles:
        print(f"Error: Invalid role '{role}'. Valid roles: {valid_roles}")
        db.close()
        return False
    
    # Create new user
    user = User(
        email=email,
        password_hash=get_password_hash(password),
        full_name=full_name,
        role=role,
        status=UserStatus.ACTIVE,
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    print(f"✓ User created successfully!")
    print(f"  ID: {user.id}")
    print(f"  Email: {user.email}")
    print(f"  Name: {user.full_name}")
    print(f"  Role: {user.role}")
    print(f"  Status: {user.status}")
    
    db.close()
    return True


def list_users():
    """List all users in the database."""
    db = SessionLocal()
    users = db.query(User).all()
    
    print("\nCurrent users:")
    print("-" * 60)
    for u in users:
        print(f"  Email: {u.email}")
        print(f"  Name: {u.full_name or '(not set)'}")
        print(f"  Role: {u.role}")
        print(f"  Status: {u.status}")
        print("-" * 60)
    
    db.close()


def reset_password(email: str, new_password: str):
    """Reset a user's password."""
    db = SessionLocal()
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        print(f"Error: User with email '{email}' not found!")
        db.close()
        return False
    
    user.password_hash = get_password_hash(new_password)
    db.commit()
    
    print(f"✓ Password reset successfully for {email}")
    db.close()
    return True


def delete_user(email: str):
    """Delete a user from the database."""
    db = SessionLocal()
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        print(f"Error: User with email '{email}' not found!")
        db.close()
        return False
    
    db.delete(user)
    db.commit()
    
    print(f"✓ User '{email}' deleted successfully!")
    db.close()
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Add user:       python add_user.py add <email> <password> [full_name] [role]")
        print("  List users:     python add_user.py list")
        print("  Reset password: python add_user.py reset-password <email> <new_password>")
        print("  Delete user:    python add_user.py delete <email>")
        print("")
        print("Roles: annotation_runner, tenant_admin, ops, admin")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "list":
        list_users()
    elif command == "add":
        if len(sys.argv) < 4:
            print("Error: Email and password are required")
            print("Usage: python add_user.py add <email> <password> [full_name] [role]")
            sys.exit(1)
        
        email = sys.argv[2]
        password = sys.argv[3]
        full_name = sys.argv[4] if len(sys.argv) > 4 else None
        role = sys.argv[5] if len(sys.argv) > 5 else "annotation_runner"
        
        add_user(email, password, full_name, role)
    elif command == "reset-password":
        if len(sys.argv) < 4:
            print("Error: Email and new password are required")
            print("Usage: python add_user.py reset-password <email> <new_password>")
            sys.exit(1)
        
        email = sys.argv[2]
        new_password = sys.argv[3]
        reset_password(email, new_password)
    elif command == "delete":
        if len(sys.argv) < 3:
            print("Error: Email is required")
            print("Usage: python add_user.py delete <email>")
            sys.exit(1)
        
        email = sys.argv[2]
        confirm = input(f"Are you sure you want to delete user '{email}'? (yes/no): ")
        if confirm.lower() == "yes":
            delete_user(email)
        else:
            print("Cancelled.")
    else:
        print(f"Unknown command: {command}")
        print("Use 'add', 'list', 'reset-password', or 'delete'")
        sys.exit(1)
