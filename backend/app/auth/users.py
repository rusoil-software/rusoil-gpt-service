import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from backend.app.auth.models import User

# Global users in memory (in production, use database)
_users: Dict[int, User] = {}
_next_id: int = 1


def _load_users() -> None:
    """
    Load users from users.json file if it exists.
    """
    global _next_id
    users_file = Path(__file__).parent / "users.json"
    
    if users_file.exists():
        with open(users_file, 'r') as f:
            data = json.load(f)
            
        for user_data in data:
            user = User(
                id=user_data["id"],
                username=user_data["username"],
                hashed_password=user_data["hashed_password"],
                is_active=user_data.get("is_active", True),
                is_admin=user_data.get("is_admin", False)
            )
            _users[user.id] = user
            
        if _users:
            _next_id = max(_users.keys()) + 1

# Load users on import
_load_users()

def get_user_by_id(user_id: int) -> Optional[User]:
    """
    Retrieve a user by their ID.
    """
    return _users.get(user_id)

def get_user_by_username(username: str) -> Optional[User]:
    """
    Retrieve a user by their username (case-insensitive).
    """
    username = username.lower()
    for user in _users.values():
        if user.username.lower() == username:
            return user
    return None

def create_user(username: str, hashed_password: str, is_admin: bool = False) -> User:
    """
    Create a new user with the given credentials.
    """
    global _next_id
    
    # Check if username already exists
    if get_user_by_username(username):
        raise ValueError(f"Username '{username}' already exists")
    
    user = User(
        id=_next_id,
        username=username,
        hashed_password=hashed_password,
        is_admin=is_admin
    )
    _users[user.id] = user
    _next_id += 1
    
    # Save to file
    _save_users()
    return user

def _save_users() -> None:
    """
    Save users to users.json file.
    """
    users_file = Path(__file__).parent / "users.json"
    data = [
        {
            "id": user.id,
            "username": user.username,
            "hashed_password": user.hashed_password,
            "is_active": user.is_active,
            "is_admin": user.is_admin
        }
        for user in _users.values()
    ]
    
    with open(users_file, 'w') as f:
        json.dump(data, f, indent=2)

def initialize_admin() -> None:
    """
    Initialize admin user if no users exist.
    Username and password can be set via environment variables:
    - ADMIN_USERNAME (default: admin)
    - ADMIN_PASSWORD (required)
    """
    if _users:
        return  # Don't create admin if users exist
    
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD")
    
    if not admin_password:
        print("Warning: ADMIN_PASSWORD not set, admin user will not be created")
        return
    
    from backend.app.auth.security import get_password_hash
    
    try:
        create_user(admin_username, get_password_hash(admin_password), is_admin=True)
        print(f"Admin user '{admin_username}' created successfully")
    except ValueError as e:
        print(f"Warning: Could not create admin user: {e}")