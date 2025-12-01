import httpx
import time
from typing import Any, Dict, Optional, Tuple
from datetime import datetime

from app.core.config import settings
from app.core.logging import logger, log_request, log_response, log_error


class ProxyForwarder:
    def __init__(self):
        self.timeout = settings.REQUEST_TIMEOUT
        self.max_retries = settings.MAX_RETRIES
        self.retry_delay = settings.RETRY_DELAY
    
    async def forward_request(
        self,
        category: str,
        endpoint_key: str,
        method: str = "POST",
        payload: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        path_params: Optional[Dict[str, str]] = None
    ) -> Tuple[Dict[str, Any], int]:
        target_url = settings.get_full_url(category, endpoint_key, path_params)
        
        if not target_url:
            return {
                "success": False,
                "message": f"No URL configured for category '{category}' endpoint '{endpoint_key}'",
                "error_code": "CONFIG_ERROR"
            }, 500
        
        request_id = log_request(
            category=category,
            endpoint=endpoint_key,
            method=method,
            request_data=payload,
            headers=headers
        )
        
        start_time = time.time()
        
        default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Request-ID": request_id,
            "X-BBPS-Category": category,
            "X-Timestamp": datetime.utcnow().isoformat()
        }
        
        if headers:
            default_headers.update(headers)
        
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    if method.upper() == "GET":
                        response = await client.get(
                            target_url,
                            headers=default_headers,
                            params=query_params
                        )
                    elif method.upper() == "POST":
                        response = await client.post(
                            target_url,
                            headers=default_headers,
                            json=payload,
                            params=query_params
                        )
                    elif method.upper() == "PUT":
                        response = await client.put(
                            target_url,
                            headers=default_headers,
                            json=payload,
                            params=query_params
                        )
                    elif method.upper() == "DELETE":
                        response = await client.delete(
                            target_url,
                            headers=default_headers,
                            params=query_params
                        )
                    else:
                        return {
                            "success": False,
                            "message": f"Unsupported HTTP method: {method}",
                            "error_code": "INVALID_METHOD"
                        }, 400
                
                duration_ms = (time.time() - start_time) * 1000
                
                try:
                    response_data: Dict[str, Any] = response.json()
                except:
                    response_data = {"raw_response": response.text}
                
                response_data["request_id"] = request_id
                response_data["timestamp"] = datetime.utcnow().isoformat()
                
                if response.status_code >= 200 and response.status_code < 300:
                    response_data["success"] = True
                else:
                    response_data["success"] = False
                
                log_response(
                    request_id=request_id,
                    category=category,
                    status_code=response.status_code,
                    response_data=response_data,
                    duration_ms=duration_ms
                )
                
                return response_data, response.status_code
                
            except httpx.TimeoutException as e:
                last_error = e
                log_error(category, endpoint_key, e, request_id)
                if attempt < self.max_retries - 1:
                    await self._delay_retry(attempt)
                    
            except httpx.ConnectError as e:
                last_error = e
                log_error(category, endpoint_key, e, request_id)
                if attempt < self.max_retries - 1:
                    await self._delay_retry(attempt)
                    
            except Exception as e:
                last_error = e
                log_error(category, endpoint_key, e, request_id)
                break
        
        duration_ms = (time.time() - start_time) * 1000
        error_response = {
            "success": False,
            "message": "Failed to connect to BBPS backend",
            "error_code": "CONNECTION_ERROR",
            "details": str(last_error) if last_error else "Unknown error",
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        log_response(
            request_id=request_id,
            category=category,
            status_code=503,
            error=str(last_error),
            duration_ms=duration_ms
        )
        
        return error_response, 503
    
    async def _delay_retry(self, attempt: int) -> None:
        import asyncio
        delay = self.retry_delay * (2 ** attempt)
        logger.info(f"Retrying in {delay} seconds (attempt {attempt + 1}/{self.max_retries})")
        await asyncio.sleep(delay)


proxy_forwarder = ProxyForwarder()


async def forward_to_bbps(
    category: str,
    endpoint_key: str,
    method: str = "POST",
    payload: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    query_params: Optional[Dict[str, str]] = None,
    path_params: Optional[Dict[str, str]] = None
) -> Tuple[Dict[str, Any], int]:
    return await proxy_forwarder.forward_request(
        category=category,
        endpoint_key=endpoint_key,
        method=method,
        payload=payload,
        headers=headers,
        query_params=query_params,
        path_params=path_params
    )
