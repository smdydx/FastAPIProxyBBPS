from fastapi import APIRouter, Query
from typing import Optional

from app.services.proxy import forward_to_bbps
from app.api.deps import normalize_response
from app.schemas.responses import BBPSResponse

router = APIRouter(prefix="/banks", tags=["Banks"])


@router.get("", response_model=BBPSResponse)
async def list_all_banks(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
) -> BBPSResponse:
    response_data, status_code = await forward_to_bbps(
        category="banks",
        endpoint_key="list_all",
        method="GET",
        query_params={"limit": str(limit), "offset": str(offset)}
    )
    return normalize_response(response_data, status_code)


@router.get("/ifsc/search", response_model=BBPSResponse)
async def search_ifsc(
    q: str = Query(..., min_length=4, description="IFSC code or branch name"),
    limit: int = Query(50, ge=1, le=100)
) -> BBPSResponse:
    response_data, status_code = await forward_to_bbps(
        category="banks",
        endpoint_key="search_ifsc",
        method="GET",
        query_params={"q": q, "limit": str(limit)}
    )
    return normalize_response(response_data, status_code)


@router.get("/{bank_id}", response_model=BBPSResponse)
async def get_bank_by_id(bank_id: str) -> BBPSResponse:
    response_data, status_code = await forward_to_bbps(
        category="banks",
        endpoint_key="get_by_id",
        method="GET",
        path_params={"bank_id": bank_id}
    )
    return normalize_response(response_data, status_code)


@router.get("/{bank_id}/ifsc", response_model=BBPSResponse)
async def get_bank_ifsc_list(
    bank_id: str,
    state: Optional[str] = None,
    city: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
) -> BBPSResponse:
    query_params = {"limit": str(limit), "offset": str(offset)}
    if state:
        query_params["state"] = state
    if city:
        query_params["city"] = city
    
    response_data, status_code = await forward_to_bbps(
        category="banks",
        endpoint_key="ifsc_list",
        method="GET",
        path_params={"bank_id": bank_id},
        query_params=query_params
    )
    return normalize_response(response_data, status_code)
