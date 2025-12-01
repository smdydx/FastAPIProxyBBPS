from fastapi import APIRouter, Query, UploadFile, File
from typing import Optional

from src.services.proxy_forwarder import forward_to_bbps
from src.routes.base_router import normalize_response
from src.models.responses import BBPSResponse
from src.models.bbps_requests import (
    SingleBillerMDMRequest,
    MultipleBillerMDMRequest,
    CategoryMDMRequest,
    MDMSearchRequest
)

router = APIRouter(prefix="/mdm", tags=["MDM - Master Data Management"])


@router.post("/fetch/single", response_model=BBPSResponse)
async def fetch_single_biller_mdm(
    request: SingleBillerMDMRequest,
    store_in_db: bool = True
) -> BBPSResponse:
    """Fetch MDM for a single biller from BBPS API."""
    payload = request.model_dump()
    payload["store_in_db"] = store_in_db
    
    response_data, status_code = await forward_to_bbps(
        category="mdm",
        endpoint_key="fetch_single",
        method="POST",
        payload=payload
    )
    return normalize_response(response_data, status_code)


@router.post("/fetch/multiple", response_model=BBPSResponse)
async def fetch_multiple_billers_mdm(
    request: MultipleBillerMDMRequest,
    store_in_db: bool = True
) -> BBPSResponse:
    """Fetch MDM for multiple billers from BBPS API."""
    payload = request.model_dump()
    payload["store_in_db"] = store_in_db
    
    response_data, status_code = await forward_to_bbps(
        category="mdm",
        endpoint_key="fetch_multiple",
        method="POST",
        payload=payload
    )
    return normalize_response(response_data, status_code)


@router.post("/fetch/by-category", response_model=BBPSResponse)
async def fetch_mdm_by_category(
    request: CategoryMDMRequest,
    store_in_db: bool = True,
    batch_size: int = Query(50, ge=10, le=100)
) -> BBPSResponse:
    """Fetch MDM for all billers in a category."""
    payload = request.model_dump()
    payload["store_in_db"] = store_in_db
    
    response_data, status_code = await forward_to_bbps(
        category="mdm",
        endpoint_key="fetch_by_category",
        method="POST",
        payload=payload,
        query_params={"batch_size": str(batch_size)}
    )
    return normalize_response(response_data, status_code)


@router.get("/stats", response_model=BBPSResponse)
async def get_mdm_stats() -> BBPSResponse:
    """Get MDM statistics."""
    response_data, status_code = await forward_to_bbps(
        category="mdm",
        endpoint_key="stats",
        method="GET"
    )
    return normalize_response(response_data, status_code)


@router.get("/sync/status", response_model=BBPSResponse)
async def get_sync_status() -> BBPSResponse:
    """Get MDM sync status."""
    response_data, status_code = await forward_to_bbps(
        category="mdm",
        endpoint_key="sync_status",
        method="GET"
    )
    return normalize_response(response_data, status_code)


@router.post("/sync/start", response_model=BBPSResponse)
async def start_full_sync(batch_size: int = Query(50, ge=10, le=100)) -> BBPSResponse:
    """Start full MDM sync for all billers."""
    response_data, status_code = await forward_to_bbps(
        category="mdm",
        endpoint_key="sync_start",
        method="POST",
        query_params={"batch_size": str(batch_size)}
    )
    return normalize_response(response_data, status_code)


@router.post("/sync/category", response_model=BBPSResponse)
async def sync_category(
    request: CategoryMDMRequest,
    batch_size: int = Query(50, ge=10, le=100)
) -> BBPSResponse:
    """Sync MDM for a specific category."""
    payload = request.model_dump()
    
    response_data, status_code = await forward_to_bbps(
        category="mdm",
        endpoint_key="sync_category",
        method="POST",
        payload=payload,
        query_params={"batch_size": str(batch_size)}
    )
    return normalize_response(response_data, status_code)


@router.post("/search", response_model=BBPSResponse)
async def search_mdm(request: MDMSearchRequest) -> BBPSResponse:
    """Search MDM records."""
    payload = request.model_dump(exclude_none=True)
    
    response_data, status_code = await forward_to_bbps(
        category="mdm",
        endpoint_key="search",
        method="POST",
        payload=payload
    )
    return normalize_response(response_data, status_code)


@router.get("/category/{category}", response_model=BBPSResponse)
async def get_mdm_by_category(
    category: str,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
) -> BBPSResponse:
    """Get cached MDM for all billers in a category."""
    response_data, status_code = await forward_to_bbps(
        category="mdm",
        endpoint_key="get_by_category",
        method="GET",
        path_params={"category": category},
        query_params={"limit": str(limit), "offset": str(offset)}
    )
    return normalize_response(response_data, status_code)


@router.get("/export/{category}", response_model=BBPSResponse)
async def export_category_mdm(
    category: str,
    format: str = Query("json", pattern="^(json|csv|xml)$")
) -> BBPSResponse:
    """Export MDM data for a category."""
    response_data, status_code = await forward_to_bbps(
        category="mdm",
        endpoint_key="export_category",
        method="GET",
        path_params={"category": category},
        query_params={"format": format}
    )
    return normalize_response(response_data, status_code)


@router.get("/{biller_id}", response_model=BBPSResponse)
async def get_biller_mdm(biller_id: str) -> BBPSResponse:
    """Get cached MDM for a specific biller."""
    response_data, status_code = await forward_to_bbps(
        category="mdm",
        endpoint_key="get_single",
        method="GET",
        path_params={"biller_id": biller_id}
    )
    return normalize_response(response_data, status_code)
