from fastapi import APIRouter, Query
from typing import Optional

from src.services.proxy_forwarder import forward_to_bbps
from src.routes.base_router import normalize_response
from src.models.responses import BBPSResponse
from src.models.bbps_requests import (
    BillFetchRequest,
    BillFetchHistoryRequest,
    ValidateParamsRequest
)

router = APIRouter(prefix="/billfetch", tags=["Bill Fetch"])


@router.get("/input-params/{biller_id}", response_model=BBPSResponse)
async def get_biller_input_params(biller_id: str) -> BBPSResponse:
    """
    Get input parameters required for a biller.
    Returns the list of parameters needed to fetch bill for this biller.
    """
    response_data, status_code = await forward_to_bbps(
        category="billfetch",
        endpoint_key="input_params",
        method="GET",
        path_params={"biller_id": biller_id}
    )
    return normalize_response(response_data, status_code)


@router.post("/fetch", response_model=BBPSResponse)
async def fetch_bill(request: BillFetchRequest) -> BBPSResponse:
    """
    Fetch bill from BBPS API.
    
    This endpoint fetches bill details for a consumer from the biller.
    The response includes bill amount, due date, customer name, etc.
    """
    payload = request.model_dump(exclude_none=True)
    
    response_data, status_code = await forward_to_bbps(
        category="billfetch",
        endpoint_key="fetch_bill",
        method="POST",
        payload=payload
    )
    return normalize_response(response_data, status_code)


@router.post("/validate-params", response_model=BBPSResponse)
async def validate_input_params(request: ValidateParamsRequest) -> BBPSResponse:
    """
    Validate input parameters before fetching bill.
    Checks if the provided parameters match biller requirements.
    """
    payload = request.model_dump()
    
    response_data, status_code = await forward_to_bbps(
        category="billfetch",
        endpoint_key="validate_params",
        method="POST",
        payload=payload
    )
    return normalize_response(response_data, status_code)


@router.get("/history", response_model=BBPSResponse)
async def get_bill_fetch_history(
    biller_id: Optional[str] = None,
    customer_mobile: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
) -> BBPSResponse:
    """
    Get bill fetch history with optional filters.
    """
    query_params = {"limit": str(limit), "offset": str(offset)}
    if biller_id:
        query_params["biller_id"] = biller_id
    if customer_mobile:
        query_params["customer_mobile"] = customer_mobile
    if from_date:
        query_params["from_date"] = from_date
    if to_date:
        query_params["to_date"] = to_date
    
    response_data, status_code = await forward_to_bbps(
        category="billfetch",
        endpoint_key="history",
        method="GET",
        query_params=query_params
    )
    return normalize_response(response_data, status_code)


@router.get("/history/{fetch_id}", response_model=BBPSResponse)
async def get_bill_fetch_by_id(fetch_id: int) -> BBPSResponse:
    """Get specific bill fetch record by ID."""
    response_data, status_code = await forward_to_bbps(
        category="billfetch",
        endpoint_key="history_by_id",
        method="GET",
        path_params={"fetch_id": str(fetch_id)}
    )
    return normalize_response(response_data, status_code)
