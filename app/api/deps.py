"""API Dependencies - Common dependencies for route handlers"""
from typing import Any, Dict, List, Optional, AsyncGenerator
from datetime import datetime
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.responses import BBPSResponse
from app.core.database import get_db, check_db_connection
from app.core.cache import cache, get_redis_client
from app.core.auth import (
    get_current_client, 
    get_current_active_client, 
    get_optional_client,
    require_scopes,
    ClientInfo
)
from app.core.security import rate_limiter


def normalize_response(response_data: Dict[str, Any], status_code: int) -> BBPSResponse:
    success = response_data.get("success", status_code >= 200 and status_code < 300)
    message = response_data.get("message", "")
    
    if not message:
        if success:
            message = "Request processed successfully"
        elif response_data.get("error_code") == "CONNECTION_ERROR":
            message = "Failed to connect to BBPS backend"
        elif response_data.get("error_code") == "CONFIG_ERROR":
            message = "Configuration error"
        else:
            message = "Request failed"
    
    data = None
    if "data" in response_data:
        data = response_data.get("data")
    else:
        excluded_keys = {"success", "message", "request_id", "timestamp", "errors", "error_code", "details"}
        remaining_data = {k: v for k, v in response_data.items() if k not in excluded_keys}
        if remaining_data:
            data = remaining_data
    
    errors: Optional[List[Dict[str, str]]] = None
    
    if not success:
        backend_errors = response_data.get("errors")
        if backend_errors and isinstance(backend_errors, list):
            errors = backend_errors
        else:
            error_details = []
            
            if response_data.get("error_code"):
                error_details.append({
                    "code": response_data.get("error_code", "UNKNOWN"),
                    "message": response_data.get("details") or response_data.get("message", "An error occurred")
                })
            elif response_data.get("message"):
                error_details.append({
                    "code": "ERROR",
                    "message": response_data.get("message", "An error occurred")
                })
            else:
                error_details.append({
                    "code": "UNKNOWN_ERROR",
                    "message": f"Request failed with status code {status_code}"
                })
            
            errors = error_details
    
    return BBPSResponse(
        success=success,
        message=message,
        data=data,
        request_id=response_data.get("request_id"),
        timestamp=response_data.get("timestamp", datetime.utcnow().isoformat()),
        errors=errors
    )


async def get_database() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db():
        yield session


async def verify_database_connection():
    is_connected = await check_db_connection()
    if not is_connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection unavailable"
        )
    return True


async def verify_cache_connection():
    client = await get_redis_client()
    if client is None:
        return False
    try:
        await client.ping()
        return True
    except Exception:
        return False


def check_rate_limit(client: ClientInfo = Depends(get_current_active_client)):
    is_allowed, retry_after = rate_limiter.is_allowed(
        client.client_id, 
        limit=client.rate_limit
    )
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Retry after {retry_after} seconds",
            headers={"Retry-After": str(retry_after)}
        )
    return client


class PaginationParams:
    def __init__(
        self,
        skip: int = 0,
        limit: int = 50,
        max_limit: int = 100
    ):
        self.skip = max(0, skip)
        self.limit = min(max(1, limit), max_limit)


def get_pagination(skip: int = 0, limit: int = 50) -> PaginationParams:
    return PaginationParams(skip=skip, limit=limit)


__all__ = [
    "normalize_response",
    "get_database",
    "get_db",
    "verify_database_connection",
    "verify_cache_connection",
    "cache",
    "get_current_client",
    "get_current_active_client",
    "get_optional_client",
    "require_scopes",
    "ClientInfo",
    "check_rate_limit",
    "get_pagination",
    "PaginationParams"
]
