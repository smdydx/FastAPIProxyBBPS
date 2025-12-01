
"""
Authentication router for BBPS Proxy - handles user login/registration.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from src.services.proxy_forwarder import forward_to_bbps
from src.routes.base_router import normalize_response
from src.models.responses import BBPSResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


class UserRegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=BBPSResponse)
async def register_user(request: UserRegisterRequest) -> BBPSResponse:
    """Register new user in BBPS system."""
    payload = request.model_dump(exclude_none=True)
    
    response_data, status_code = await forward_to_bbps(
        category="auth",
        endpoint_key="register",
        method="POST",
        payload=payload
    )
    return normalize_response(response_data, status_code)


@router.post("/login", response_model=BBPSResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> BBPSResponse:
    """
    Login user and get JWT access token.
    Returns: access_token, token_type
    """
    payload = {
        "username": form_data.username,
        "password": form_data.password
    }
    
    response_data, status_code = await forward_to_bbps(
        category="auth",
        endpoint_key="login",
        method="POST",
        payload=payload
    )
    return normalize_response(response_data, status_code)


@router.post("/refresh", response_model=BBPSResponse)
async def refresh_token(refresh_token: str) -> BBPSResponse:
    """Refresh JWT access token."""
    response_data, status_code = await forward_to_bbps(
        category="auth",
        endpoint_key="refresh",
        method="POST",
        payload={"refresh_token": refresh_token}
    )
    return normalize_response(response_data, status_code)


@router.get("/me", response_model=BBPSResponse)
async def get_current_user() -> BBPSResponse:
    """Get current authenticated user details."""
    response_data, status_code = await forward_to_bbps(
        category="auth",
        endpoint_key="me",
        method="GET"
    )
    return normalize_response(response_data, status_code)
