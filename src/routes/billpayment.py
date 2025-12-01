from fastapi import APIRouter, Query
from typing import Optional

from src.services.proxy_forwarder import forward_to_bbps
from src.routes.base_router import normalize_response
from src.models.responses import BBPSResponse
from src.models.bbps_requests import BillPaymentRequest

router = APIRouter(prefix="/billpayment", tags=["Bill Payment"])


@router.post("/pay", response_model=BBPSResponse)
async def pay_bill(request: BillPaymentRequest) -> BBPSResponse:
    """
    Pay bill through BBPS API.
    
    This endpoint initiates bill payment for a consumer.
    Returns transaction ID and payment status.
    """
    payload = request.model_dump(exclude_none=True)
    
    response_data, status_code = await forward_to_bbps(
        category="billpayment",
        endpoint_key="pay_bill",
        method="POST",
        payload=payload
    )
    return normalize_response(response_data, status_code)


@router.get("/status/{transaction_id}", response_model=BBPSResponse)
async def get_payment_status(transaction_id: str) -> BBPSResponse:
    """Get payment status by transaction ID."""
    response_data, status_code = await forward_to_bbps(
        category="billpayment",
        endpoint_key="status",
        method="GET",
        path_params={"transaction_id": transaction_id}
    )
    return normalize_response(response_data, status_code)


@router.get("/history", response_model=BBPSResponse)
async def get_payment_history(
    biller_id: Optional[str] = None,
    customer_mobile: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
) -> BBPSResponse:
    """Get payment history with optional filters."""
    query_params = {"limit": str(limit), "offset": str(offset)}
    if biller_id:
        query_params["biller_id"] = biller_id
    if customer_mobile:
        query_params["customer_mobile"] = customer_mobile
    if from_date:
        query_params["from_date"] = from_date
    if to_date:
        query_params["to_date"] = to_date
    if status:
        query_params["status"] = status
    
    response_data, status_code = await forward_to_bbps(
        category="billpayment",
        endpoint_key="history",
        method="GET",
        query_params=query_params
    )
    return normalize_response(response_data, status_code)


@router.post("/refund", response_model=BBPSResponse)
async def request_refund(
    transaction_id: str,
    reason: str
) -> BBPSResponse:
    """Request refund for a transaction."""
    payload = {
        "transaction_id": transaction_id,
        "reason": reason
    }
    
    response_data, status_code = await forward_to_bbps(
        category="billpayment",
        endpoint_key="refund",
        method="POST",
        payload=payload
    )
    return normalize_response(response_data, status_code)
