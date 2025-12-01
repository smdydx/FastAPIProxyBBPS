from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends, Security
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)
api_key_header = APIKeyHeader(name=settings.API_KEY_HEADER, auto_error=False)


class TokenData(BaseModel):
    client_id: Optional[str] = None
    scopes: list[str] = []
    exp: Optional[datetime] = None


class ClientInfo(BaseModel):
    client_id: str
    client_name: Optional[str] = None
    is_active: bool = True
    scopes: list[str] = []
    rate_limit: int = 100


def create_access_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[TokenData]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        client_id: str = payload.get("sub")
        scopes: list = payload.get("scopes", [])
        exp = payload.get("exp")
        
        if client_id is None:
            return None
        
        return TokenData(
            client_id=client_id, 
            scopes=scopes,
            exp=datetime.fromtimestamp(exp) if exp else None
        )
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        return None


def verify_token(token: str) -> Optional[TokenData]:
    token_data = decode_token(token)
    if token_data is None:
        return None
    
    if token_data.exp and token_data.exp < datetime.utcnow():
        return None
    
    return token_data


async def get_current_client(
    token: Optional[str] = Depends(oauth2_scheme),
    api_key: Optional[str] = Security(api_key_header)
) -> ClientInfo:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if token:
        token_data = verify_token(token)
        if token_data is None:
            raise credentials_exception
        
        return ClientInfo(
            client_id=token_data.client_id,
            scopes=token_data.scopes,
            is_active=True
        )
    
    if api_key:
        if not api_key.startswith(settings.API_KEY_PREFIX):
            raise credentials_exception
        
        return ClientInfo(
            client_id=api_key,
            is_active=True,
            scopes=["read", "write"]
        )
    
    raise credentials_exception


async def get_current_active_client(
    current_client: ClientInfo = Depends(get_current_client)
) -> ClientInfo:
    if not current_client.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Inactive client"
        )
    return current_client


def get_optional_client(
    token: Optional[str] = Depends(oauth2_scheme),
    api_key: Optional[str] = Security(api_key_header)
) -> Optional[ClientInfo]:
    if token:
        token_data = verify_token(token)
        if token_data:
            return ClientInfo(
                client_id=token_data.client_id,
                scopes=token_data.scopes,
                is_active=True
            )
    
    if api_key and api_key.startswith(settings.API_KEY_PREFIX):
        return ClientInfo(
            client_id=api_key,
            is_active=True,
            scopes=["read", "write"]
        )
    
    return None


class ScopeChecker:
    def __init__(self, required_scopes: list[str]):
        self.required_scopes = required_scopes
    
    def __call__(self, client: ClientInfo = Depends(get_current_active_client)) -> ClientInfo:
        for scope in self.required_scopes:
            if scope not in client.scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required scope: {scope}"
                )
        return client


def require_scopes(*scopes: str):
    return ScopeChecker(list(scopes))
