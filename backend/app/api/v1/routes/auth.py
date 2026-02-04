"""
Authentication Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, timedelta
import hashlib
import secrets
import uuid

router = APIRouter()

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# In-memory user storage (use database in production)
_users = {}
_tokens = {}
_sessions = {}

# Token expiration time
TOKEN_EXPIRE_HOURS = 24


# ============ Schemas ============

class UserCreate(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    full_name: str
    company: Optional[str] = None
    role: Optional[str] = "underwriter"  # underwriter, admin, viewer


class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response (without password)"""
    user_id: str
    email: str
    full_name: str
    company: Optional[str] = None
    role: str
    created_at: str
    last_login: Optional[str] = None


class TokenResponse(BaseModel):
    """Token response after login"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: UserResponse


class PasswordChange(BaseModel):
    """Password change request"""
    current_password: str
    new_password: str = Field(..., min_length=8)


# ============ Helper Functions ============

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt"""
    salt = "loan_ai_salt_2024"  # In production, use unique salt per user
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hashed


def create_token(user_id: str) -> tuple[str, datetime]:
    """Create access token"""
    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    _tokens[token] = {
        "user_id": user_id,
        "expires": expires
    }
    return token, expires


def get_user_from_token(token: str) -> Optional[dict]:
    """Get user from token"""
    token_data = _tokens.get(token)
    if not token_data:
        return None

    if datetime.utcnow() > token_data["expires"]:
        del _tokens[token]
        return None

    return _users.get(token_data["user_id"])


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Dependency to get current authenticated user"""
    user = get_user_from_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# ============ Demo Users ============

def init_demo_users():
    """Initialize demo users"""
    demo_users = [
        {
            "email": "admin@loanai.com",
            "password": "admin123",
            "full_name": "Admin User",
            "company": "LoanAI",
            "role": "admin"
        },
        {
            "email": "underwriter@loanai.com",
            "password": "underwriter123",
            "full_name": "John Underwriter",
            "company": "LoanAI",
            "role": "underwriter"
        },
        {
            "email": "demo@example.com",
            "password": "demo1234",
            "full_name": "Demo User",
            "company": "Demo Corp",
            "role": "viewer"
        }
    ]

    for user_data in demo_users:
        user_id = str(uuid.uuid4())
        _users[user_id] = {
            "user_id": user_id,
            "email": user_data["email"],
            "password_hash": hash_password(user_data["password"]),
            "full_name": user_data["full_name"],
            "company": user_data["company"],
            "role": user_data["role"],
            "created_at": datetime.utcnow().isoformat(),
            "last_login": None
        }
        # Also index by email for login lookup
        _users[user_data["email"]] = _users[user_id]


# Initialize demo users
init_demo_users()


# ============ Endpoints ============

@router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    """
    Register a new user account
    """
    # Check if email already exists
    if user.email in _users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    user_id = str(uuid.uuid4())
    new_user = {
        "user_id": user_id,
        "email": user.email,
        "password_hash": hash_password(user.password),
        "full_name": user.full_name,
        "company": user.company,
        "role": user.role or "underwriter",
        "created_at": datetime.utcnow().isoformat(),
        "last_login": None
    }

    _users[user_id] = new_user
    _users[user.email] = new_user  # Index by email

    return UserResponse(
        user_id=user_id,
        email=user.email,
        full_name=user.full_name,
        company=user.company,
        role=new_user["role"],
        created_at=new_user["created_at"]
    )


@router.post("/auth/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login and get access token

    Use email as username
    """
    # Find user by email
    user = _users.get(form_data.username)

    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login
    user["last_login"] = datetime.utcnow().isoformat()

    # Create token
    token, expires = create_token(user["user_id"])

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=TOKEN_EXPIRE_HOURS * 3600,
        user=UserResponse(
            user_id=user["user_id"],
            email=user["email"],
            full_name=user["full_name"],
            company=user.get("company"),
            role=user["role"],
            created_at=user["created_at"],
            last_login=user["last_login"]
        )
    )


@router.post("/auth/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout and invalidate token
    """
    # Find and remove token (simplified - in production track tokens per user)
    tokens_to_remove = [
        token for token, data in _tokens.items()
        if data["user_id"] == current_user["user_id"]
    ]
    for token in tokens_to_remove:
        del _tokens[token]

    return {"message": "Successfully logged out"}


@router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current user information
    """
    return UserResponse(
        user_id=current_user["user_id"],
        email=current_user["email"],
        full_name=current_user["full_name"],
        company=current_user.get("company"),
        role=current_user["role"],
        created_at=current_user["created_at"],
        last_login=current_user.get("last_login")
    )


@router.put("/auth/password")
async def change_password(
    password_data: PasswordChange,
    current_user: dict = Depends(get_current_user)
):
    """
    Change password for current user
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Update password
    current_user["password_hash"] = hash_password(password_data.new_password)

    return {"message": "Password updated successfully"}


@router.get("/auth/users", response_model=list[UserResponse])
async def list_users(current_user: dict = Depends(get_current_user)):
    """
    List all users (admin only)
    """
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    # Get unique users (avoid duplicates from email indexing)
    seen_ids = set()
    users = []
    for user in _users.values():
        if user["user_id"] not in seen_ids:
            seen_ids.add(user["user_id"])
            users.append(UserResponse(
                user_id=user["user_id"],
                email=user["email"],
                full_name=user["full_name"],
                company=user.get("company"),
                role=user["role"],
                created_at=user["created_at"],
                last_login=user.get("last_login")
            ))

    return users
