from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    """
    Represents an authenticated user in the system.
    """
    id: int
    username: str
    hashed_password: str
    is_active: bool = True
    is_admin: bool = False

    def to_dict(self) -> dict:
        """
        Convert user to dictionary for JSON serialization.
        """
        return {
            "id": self.id,
            "username": self.username,
            "is_active": self.is_active,
            "is_admin": self.is_admin
        }