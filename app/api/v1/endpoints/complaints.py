from fastapi import APIRouter, Query
from typing import Optional

from app.services.proxy import forward_to_bbps
from app.api.deps import normalize_response
from app.schemas.responses import BBPSResponse
from app.schemas.bbps import ComplaintRegisterRequest

router = APIRouter(prefix="/complaints", tags=["Complaints"])


@router.post("/register", response_model=BBPSResponse)
async def register_complaint(request: ComplaintRegisterRequest) -> BBPSResponse:
    payload = request.model_dump(exclude_none=True)
    
    response_data, status_code = await forward_to_bbps(
        category="complaints",
        endpoint_key="register",
        method="POST",
        payload=payload
    )
    return normalize_response(response_data, status_code)


@router.get("/status/{complaint_id}", response_model=BBPSResponse)
async def get_complaint_status(complaint_id: str) -> BBPSResponse:
    response_data, status_code = await forward_to_bbps(
        category="complaints",
        endpoint_key="status",
        method="GET",
        path_params={"complaint_id": complaint_id}
    )
    return normalize_response(response_data, status_code)


@router.get("", response_model=BBPSResponse)
async def list_complaints(
    transaction_id: Optional[str] = None,
    status: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
) -> BBPSResponse:
    query_params = {"limit": str(limit), "offset": str(offset)}
    if transaction_id:
        query_params["transaction_id"] = transaction_id
    if status:
        query_params["status"] = status
    if from_date:
        query_params["from_date"] = from_date
    if to_date:
        query_params["to_date"] = to_date
    
    response_data, status_code = await forward_to_bbps(
        category="complaints",
        endpoint_key="list",
        method="GET",
        query_params=query_params
    )
    return normalize_response(response_data, status_code)


@router.put("/{complaint_id}", response_model=BBPSResponse)
async def update_complaint(
    complaint_id: str,
    status: Optional[str] = None,
    remarks: Optional[str] = None
) -> BBPSResponse:
    payload = {}
    if status:
        payload["status"] = status
    if remarks:
        payload["remarks"] = remarks
    
    response_data, status_code = await forward_to_bbps(
        category="complaints",
        endpoint_key="update",
        method="PUT",
        path_params={"complaint_id": complaint_id},
        payload=payload
    )
    return normalize_response(response_data, status_code)
