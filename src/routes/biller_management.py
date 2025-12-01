
"""
Biller management router - bulk operations with CSV/Excel upload.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from typing import Optional

from src.services.proxy_forwarder import forward_to_bbps
from src.routes.base_router import normalize_response
from src.models.responses import BBPSResponse

router = APIRouter(prefix="/biller-management", tags=["Biller Management"])


@router.post("/upload/csv", response_model=BBPSResponse)
async def upload_csv(
    file: UploadFile = File(...),
    operation: str = Query("insert", regex="^(insert|update|upsert)$")
) -> BBPSResponse:
    """
    Upload CSV file for bulk biller insert/update.
    Operations: insert, update, upsert
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(400, "Only CSV files allowed")
    
    file_content = await file.read()
    
    response_data, status_code = await forward_to_bbps(
        category="biller_management",
        endpoint_key="upload_csv",
        method="POST",
        payload={
            "filename": file.filename,
            "operation": operation,
            "file_size": len(file_content)
        }
    )
    return normalize_response(response_data, status_code)


@router.post("/bulk/insert", response_model=BBPSResponse)
async def bulk_insert(billers: list[dict]) -> BBPSResponse:
    """Bulk insert billers via JSON payload."""
    response_data, status_code = await forward_to_bbps(
        category="biller_management",
        endpoint_key="bulk_insert",
        method="POST",
        payload={"billers": billers}
    )
    return normalize_response(response_data, status_code)


@router.post("/bulk/update", response_model=BBPSResponse)
async def bulk_update(billers: list[dict]) -> BBPSResponse:
    """Bulk update billers via JSON payload."""
    response_data, status_code = await forward_to_bbps(
        category="biller_management",
        endpoint_key="bulk_update",
        method="POST",
        payload={"billers": billers}
    )
    return normalize_response(response_data, status_code)


@router.delete("/bulk/delete", response_model=BBPSResponse)
async def bulk_delete(biller_ids: list[str]) -> BBPSResponse:
    """Bulk delete billers by IDs."""
    response_data, status_code = await forward_to_bbps(
        category="biller_management",
        endpoint_key="bulk_delete",
        method="DELETE",
        payload={"biller_ids": biller_ids}
    )
    return normalize_response(response_data, status_code)
