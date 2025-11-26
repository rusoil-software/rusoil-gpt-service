from __future__ import annotations

import os
import time
from typing import Dict, Optional

import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

AUTH_SECRET = os.getenv("AUTH_SECRET", "changeme")
ALGORITHM = "HS256"


security = HTTPBearer(auto_error=False)


class User:
    def __init__(self, user_id: str, username: str, claims: Dict = None):
        self.user_id = str(user_id)
        self.username = username
        self.claims = claims or {}

    def dict(self) -> Dict:
        return {"user_id": self.user_id, "username": self.username, **self.claims}


def verify_jwt(token: str) -> Dict:
    """Decode and verify a JWT using AUTH_SECRET.

    Raises HTTPException(401) if token is missing, invalid or expired.
    Returns the payload dict on success.
    """
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization token")
    try:
        payload = jwt.decode(token, AUTH_SECRET, algorithms=[ALGORITHM])
        # Ensure token is not expired (PyJWT will raise if 'exp' is present and expired)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return payload


def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> User:
    """FastAPI dependency which extracts a bearer token from the Authorization header,
    validates it and returns a User object.
    """
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header missing or malformed")
    token = credentials.credentials
    payload = verify_jwt(token)
    # Expect claims 'user_id' and 'username'
    user_id = payload.get("user_id") or payload.get("sub")
    username = payload.get("username") or payload.get("name")
    if not user_id or not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing required user claims")
    return User(user_id=user_id, username=username, claims=payload)
