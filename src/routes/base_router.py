from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Any, Dict, List, Optional
from datetime import datetime

from src.services.proxy_forwarder import forward_to_bbps
from src.models.requests import (
    FetchBillersRequest,
    FetchBillRequest,
    PayBillRequest,
    BillStatusRequest,
    RechargeRequest,
    FetchPlansRequest
)
from src.models.responses import BBPSResponse


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


def create_category_router(category: str, category_display: str) -> APIRouter:
    router = APIRouter(prefix=f"/{category}", tags=[category_display])
    
    @router.get("/billers", response_model=BBPSResponse)
    async def fetch_billers(
        state: Optional[str] = None,
        city: Optional[str] = None,
        search_term: Optional[str] = None
    ) -> BBPSResponse:
        query_params = {}
        if state:
            query_params["state"] = state
        if city:
            query_params["city"] = city
        if search_term:
            query_params["search"] = search_term
        
        response_data, status_code = await forward_to_bbps(
            category=category,
            endpoint_key="fetch_billers",
            method="GET",
            query_params=query_params if query_params else None
        )
        
        return normalize_response(response_data, status_code)
    
    @router.post("/fetch-bill", response_model=BBPSResponse)
    async def fetch_bill(request: FetchBillRequest) -> BBPSResponse:
        payload = request.model_dump(exclude_none=True)
        
        response_data, status_code = await forward_to_bbps(
            category=category,
            endpoint_key="fetch_bill",
            method="POST",
            payload=payload
        )
        
        return normalize_response(response_data, status_code)
    
    @router.post("/pay-bill", response_model=BBPSResponse)
    async def pay_bill(request: PayBillRequest) -> BBPSResponse:
        payload = request.model_dump(exclude_none=True)
        
        response_data, status_code = await forward_to_bbps(
            category=category,
            endpoint_key="pay_bill",
            method="POST",
            payload=payload
        )
        
        return normalize_response(response_data, status_code)
    
    @router.post("/status", response_model=BBPSResponse)
    async def bill_status(request: BillStatusRequest) -> BBPSResponse:
        payload = request.model_dump(exclude_none=True)
        
        response_data, status_code = await forward_to_bbps(
            category=category,
            endpoint_key="bill_status",
            method="POST",
            payload=payload
        )
        
        return normalize_response(response_data, status_code)
    
    return router


def create_recharge_router(category: str, category_display: str) -> APIRouter:
    router = create_category_router(category, category_display)
    
    @router.post("/recharge", response_model=BBPSResponse)
    async def recharge(request: RechargeRequest) -> BBPSResponse:
        payload = request.model_dump(exclude_none=True)
        
        response_data, status_code = await forward_to_bbps(
            category=category,
            endpoint_key="recharge",
            method="POST",
            payload=payload
        )
        
        return normalize_response(response_data, status_code)
    
    @router.get("/plans", response_model=BBPSResponse)
    async def fetch_plans(
        biller_id: str,
        consumer_id: Optional[str] = None,
        circle: Optional[str] = None
    ) -> BBPSResponse:
        query_params = {"biller_id": biller_id}
        if consumer_id:
            query_params["consumer_id"] = consumer_id
        if circle:
            query_params["circle"] = circle
        
        response_data, status_code = await forward_to_bbps(
            category=category,
            endpoint_key="fetch_plans",
            method="GET",
            query_params=query_params
        )
        
        return normalize_response(response_data, status_code)
    
    return router
