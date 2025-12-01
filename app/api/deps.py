"""API Dependencies - Common dependencies for route handlers"""
from typing import Any, Dict, List, Optional
from datetime import datetime

from app.schemas.responses import BBPSResponse


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
