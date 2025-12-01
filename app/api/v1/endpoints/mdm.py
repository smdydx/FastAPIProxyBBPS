from fastapi import APIRouter, Query

from app.services.proxy import forward_to_bbps
from app.api.deps import normalize_response
from app.schemas.responses import BBPSResponse
from app.schemas.bbps import (
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
    response_data, status_code = await forward_to_bbps(
        category="mdm",
        endpoint_key="stats",
        method="GET"
    )
    return normalize_response(response_data, status_code)


@router.get("/sync/status", response_model=BBPSResponse)
async def get_sync_status() -> BBPSResponse:
    response_data, status_code = await forward_to_bbps(
        category="mdm",
        endpoint_key="sync_status",
        method="GET"
    )
    return normalize_response(response_data, status_code)


@router.post("/sync/start", response_model=BBPSResponse)
async def start_full_sync(batch_size: int = Query(50, ge=10, le=100)) -> BBPSResponse:
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
    response_data, status_code = await forward_to_bbps(
        category="mdm",
        endpoint_key="get_single",
        method="GET",
        path_params={"biller_id": biller_id}
    )
    return normalize_response(response_data, status_code)
