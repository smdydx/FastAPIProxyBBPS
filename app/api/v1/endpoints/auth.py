from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional, List

from app.core.database import get_db
from app.core.auth import (
    create_access_token, create_refresh_token, verify_token,
    get_current_active_client, ClientInfo, TokenData
)
from app.core.security import verify_password, get_password_hash
from app.core.logging import logger
from app.core.config import settings
from app.models.optimized_models import Client

router = APIRouter()


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ClientProfileResponse(BaseModel):
    client_id: str
    client_name: str
    contact_email: Optional[str]
    contact_phone: Optional[str]
    scopes: List[str]
    rate_limit: int
    created_at: Optional[datetime]
    last_login_at: Optional[datetime]


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    client = await db.scalar(
        select(Client).where(Client.client_id == form_data.username)
    )
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect client ID or secret",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(form_data.password, client.client_secret_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect client ID or secret",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not client.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Client account is deactivated"
        )
    
    client.last_login_at = datetime.utcnow()
    
    token_data = {
        "sub": client.client_id,
        "scopes": client.scopes or ["read", "write"]
    }
    
    access_token = create_access_token(
        data=token_data,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(data=token_data)
    
    logger.info(f"Client {client.client_id} logged in successfully")
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    token_data = verify_token(request.refresh_token)
    
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    client = await db.scalar(
        select(Client).where(Client.client_id == token_data.client_id)
    )
    
    if not client or not client.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Client not found or inactive"
        )
    
    new_token_data = {
        "sub": client.client_id,
        "scopes": client.scopes or ["read", "write"]
    }
    
    access_token = create_access_token(
        data=new_token_data,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    new_refresh_token = create_refresh_token(data=new_token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=ClientProfileResponse)
async def get_current_client_profile(
    current_client: ClientInfo = Depends(get_current_active_client),
    db: AsyncSession = Depends(get_db)
):
    client = await db.scalar(
        select(Client).where(Client.client_id == current_client.client_id)
    )
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client profile not found"
        )
    
    return ClientProfileResponse(
        client_id=client.client_id,
        client_name=client.client_name,
        contact_email=client.contact_email,
        contact_phone=client.contact_phone,
        scopes=client.scopes or [],
        rate_limit=client.rate_limit,
        created_at=client.created_at,
        last_login_at=client.last_login_at
    )


@router.put("/me")
async def update_current_client_profile(
    contact_email: Optional[str] = None,
    contact_phone: Optional[str] = None,
    webhook_url: Optional[str] = None,
    current_client: ClientInfo = Depends(get_current_active_client),
    db: AsyncSession = Depends(get_db)
):
    client = await db.scalar(
        select(Client).where(Client.client_id == current_client.client_id)
    )
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client profile not found"
        )
    
    if contact_email is not None:
        client.contact_email = contact_email
    if contact_phone is not None:
        client.contact_phone = contact_phone
    if webhook_url is not None:
        client.webhook_url = webhook_url
    
    return {
        "success": True,
        "message": "Profile updated successfully"
    }


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_client: ClientInfo = Depends(get_current_active_client),
    db: AsyncSession = Depends(get_db)
):
    client = await db.scalar(
        select(Client).where(Client.client_id == current_client.client_id)
    )
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    if not verify_password(request.current_password, client.client_secret_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    client.client_secret_hash = get_password_hash(request.new_password)
    
    logger.info(f"Client {client.client_id} changed password")
    
    return {
        "success": True,
        "message": "Password changed successfully"
    }


@router.post("/logout")
async def logout(
    current_client: ClientInfo = Depends(get_current_active_client)
):
    logger.info(f"Client {current_client.client_id} logged out")
    return {
        "success": True,
        "message": "Logged out successfully"
    }


@router.get("/verify")
async def verify_authentication(
    current_client: ClientInfo = Depends(get_current_active_client)
):
    return {
        "success": True,
        "client_id": current_client.client_id,
        "scopes": current_client.scopes,
        "is_active": current_client.is_active
    }
