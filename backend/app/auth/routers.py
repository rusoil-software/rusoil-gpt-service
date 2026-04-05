from datetime import datetime, timedelta
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status, Body
from fastapi.security import OAuth2PasswordRequestForm

from backend.app.auth.models import User
from backend.app.auth.security import create_access_token, decode_access_token, Hasher
from backend.app.auth.users import get_user_by_id, get_user_by_username, initialize_admin

router = APIRouter(prefix="/auth", tags=["auth"])

@router.on_event("startup")
def startup_event():
    """
    Initialize admin user on application startup.
    """
    initialize_admin()

@router.post("/login", response_model=Dict[str, str],
         summary="Authenticate user and return JWT",
         description="Verify username and password, and return a signed JWT token for session management.",
         responses={
             200: {
                 "description": "Successful authentication",
                 "content": {
                     "application/json": {
                         "example": {
                             "access_token": "eyJhbGciOiJIUzI1NiIs...",
                             "token_type": "bearer"
                         }
                     }
                 }
             },
             401: {
                 "description": "Invalid credentials",
                 "content": {
                     "application/json": {
                         "example": {
                             "detail": "Incorrect username or password"
                         }
                     }
                 }
             }
         })
def login(username: str = Body(..., embed=True), password: str = Body(..., embed=True)) -> Dict[str, str]:
    """
    Authenticate user with username and password and return JWT access token.
    
    This endpoint supports both JSON and form data input.
    
    Args:
        username (str): User's username
        password (str): User's password
    
    Returns:
        Dict[str, str]: JSON response with access_token and token_type
    
    Raises:
        HTTPException: 401 Unauthorized for invalid credentials
    """
    
    # Validate input
    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username and password are required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # First try to find user by username
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password using bcrypt
    if not Hasher.verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # First try to find user by username
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password using bcrypt
    if not Hasher.verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate access token with claims
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "username": user.username,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + access_token_expires
        },
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

def get_current_user(request: Request) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    Implements JWT authentication middleware functionality by:
    - Parsing and verifying JWT using AUTH_SECRET
    - Rejecting requests with missing, invalid, or expired tokens
    - Extracting user_id and username from token claims
    - Making user data available in the request context
    
    Args:
        request: FastAPI request object
    
    Returns:
        User: Authenticated user object
    
    Raises:
        HTTPException: 401 Unauthorized for invalid/missing tokens
    """
    authorization: str = request.headers.get("Authorization")
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated - missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme - expected Bearer",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload - missing user ID (sub claim)",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username = payload.get("username")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload - missing username",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = get_user_by_id(int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Add user to request state for access in other dependencies/endpoints
    request.state.user = user
    
    return user

@router.get("/me", response_model=Dict)
def get_me(current_user: User = Depends(get_current_user)) -> Dict:
    """
    Get the currently authenticated user's information.
    """
    return current_user.to_dict()