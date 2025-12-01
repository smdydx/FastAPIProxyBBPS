
"""
Admin router for BBPS Proxy - forwards admin operations to backend.
Supports Excel/CSV uploads, stats, and category management.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from typing import Optional, Dict, Any

from src.services.proxy_forwarder import forward_to_bbps
from src.routes.base_router import normalize_response
from src.models.responses import BBPSResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/upload/excel", response_model=BBPSResponse)
async def upload_excel(
    file: UploadFile = File(...),
    category: Optional[str] = None
) -> BBPSResponse:
    """
    Upload Excel/CSV file for bulk biller data.
    Forwards file to backend for processing.
    """
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(400, "Only Excel/CSV files allowed")
    
    file_content = await file.read()
    
    # Forward as multipart file
    response_data, status_code = await forward_to_bbps(
        category="admin",
        endpoint_key="upload_excel",
        method="POST",
        payload={
            "filename": file.filename,
            "category": category,
            "file_size": len(file_content)
        }
    )
    return normalize_response(response_data, status_code)


@router.get("/stats", response_model=BBPSResponse)
async def get_admin_stats() -> BBPSResponse:
    """Get admin dashboard statistics."""
    response_data, status_code = await forward_to_bbps(
        category="admin",
        endpoint_key="stats",
        method="GET"
    )
    return normalize_response(response_data, status_code)


@router.get("/categories", response_model=BBPSResponse)
async def list_categories() -> BBPSResponse:
    """List all available biller categories."""
    response_data, status_code = await forward_to_bbps(
        category="admin",
        endpoint_key="categories",
        method="GET"
    )
    return normalize_response(response_data, status_code)


@router.post("/sync/billers", response_model=BBPSResponse)
async def sync_billers(category: Optional[str] = None) -> BBPSResponse:
    """Trigger biller data sync from BBPS."""
    response_data, status_code = await forward_to_bbps(
        category="admin",
        endpoint_key="sync_billers",
        method="POST",
        payload={"category": category}
    )
    return normalize_response(response_data, status_code)
