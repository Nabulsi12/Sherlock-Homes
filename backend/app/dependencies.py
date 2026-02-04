"""
Dependency Injection
"""

from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Validate API authentication
    For hackathon: simple bearer token
    In production: implement proper JWT validation
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials"
        )

    # For hackathon: accept any bearer token
    # In production: validate JWT token here
    return {"user_id": "hackathon_user"}


async def validate_api_key(api_key: str = Depends(security)):
    """Validate API key if needed"""
    # Implement if you need API key validation
    pass
