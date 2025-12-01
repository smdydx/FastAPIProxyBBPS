from fastapi import APIRouter, Query
from typing import Optional

from src.services.proxy_forwarder import forward_to_bbps
from src.routes.base_router import normalize_response
from src.models.responses import BBPSResponse

router = APIRouter(prefix="/billers", tags=["Billers"])


@router.get("", response_model=BBPSResponse)
async def list_all_billers(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
) -> BBPSResponse:
    """Get list of all billers."""
    response_data, status_code = await forward_to_bbps(
        category="billers",
        endpoint_key="list_all",
        method="GET",
        query_params={"limit": str(limit), "offset": str(offset)}
    )
    return normalize_response(response_data, status_code)


@router.get("/categories", response_model=BBPSResponse)
async def get_biller_categories() -> BBPSResponse:
    """Get list of all biller categories."""
    response_data, status_code = await forward_to_bbps(
        category="billers",
        endpoint_key="categories",
        method="GET"
    )
    return normalize_response(response_data, status_code)


@router.get("/category/{category}", response_model=BBPSResponse)
async def get_billers_by_category(
    category: str,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
) -> BBPSResponse:
    """Get billers for a specific category."""
    response_data, status_code = await forward_to_bbps(
        category="billers",
        endpoint_key="by_category",
        method="GET",
        path_params={"category": category},
        query_params={"limit": str(limit), "offset": str(offset)}
    )
    return normalize_response(response_data, status_code)


@router.get("/search", response_model=BBPSResponse)
async def search_billers(
    q: str = Query(..., min_length=2, description="Search query"),
    category: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
) -> BBPSResponse:
    """Search billers by name or ID."""
    query_params = {
        "q": q,
        "limit": str(limit),
        "offset": str(offset)
    }
    if category:
        query_params["category"] = category
    
    response_data, status_code = await forward_to_bbps(
        category="billers",
        endpoint_key="search",
        method="GET",
        query_params=query_params
    )
    return normalize_response(response_data, status_code)


@router.get("/{biller_id}", response_model=BBPSResponse)
async def get_biller_by_id(biller_id: str) -> BBPSResponse:
    """Get biller details by ID."""
    response_data, status_code = await forward_to_bbps(
        category="billers",
        endpoint_key="get_by_id",
        method="GET",
        path_params={"biller_id": biller_id}
    )
    return normalize_response(response_data, status_code)
