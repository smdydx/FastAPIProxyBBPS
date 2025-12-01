import httpx
from typing import Any, Dict, Optional, List
from datetime import datetime
import json

from app.core.config import settings
from app.core.logging import logger
from app.core.security import generate_transaction_id, generate_reference_id


class BBPSAPIService:
    def __init__(self):
        self.base_url = settings.BBPS_API_BASE_URL
        self.api_key = settings.BBPS_API_KEY
        self.api_secret = settings.BBPS_API_SECRET
        self.ou_id = settings.BBPS_OU_ID
        self.agent_id = settings.BBPS_AGENT_ID
        self.timeout = settings.REQUEST_TIMEOUT
        self.max_retries = settings.MAX_RETRIES
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-API-Key": self.api_key,
            "X-OU-ID": self.ou_id,
            "X-Agent-ID": self.agent_id,
            "X-Request-ID": generate_reference_id("REQ"),
            "X-Timestamp": datetime.utcnow().isoformat()
        }
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    if method.upper() == "GET":
                        response = await client.get(url, headers=headers, params=params)
                    elif method.upper() == "POST":
                        response = await client.post(url, headers=headers, json=data)
                    elif method.upper() == "PUT":
                        response = await client.put(url, headers=headers, json=data)
                    else:
                        raise ValueError(f"Unsupported HTTP method: {method}")
                    
                    response.raise_for_status()
                    return {
                        "success": True,
                        "data": response.json(),
                        "status_code": response.status_code
                    }
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:
                    return {
                        "success": False,
                        "error": str(e),
                        "status_code": e.response.status_code if e.response else 500
                    }
            except httpx.RequestError as e:
                logger.error(f"Request error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:
                    return {
                        "success": False,
                        "error": str(e),
                        "status_code": 503
                    }
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:
                    return {
                        "success": False,
                        "error": str(e),
                        "status_code": 500
                    }
        
        return {"success": False, "error": "Max retries exceeded", "status_code": 503}
    
    async def fetch_bill(
        self,
        biller_id: str,
        consumer_number: str,
        input_params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        endpoint = "/billfetch/fetch"
        data = {
            "billerId": biller_id,
            "consumerNumber": consumer_number,
            "inputParams": input_params or {},
            "agentId": self.agent_id,
            "ouId": self.ou_id
        }
        
        logger.info(f"Fetching bill for biller: {biller_id}, consumer: {consumer_number}")
        return await self._make_request("POST", endpoint, data)
    
    async def pay_bill(
        self,
        biller_id: str,
        consumer_number: str,
        amount: float,
        payment_mode: str,
        input_params: Optional[Dict] = None,
        customer_info: Optional[Dict] = None
    ) -> Dict[str, Any]:
        transaction_id = generate_transaction_id("PAY")
        
        endpoint = "/billpayment/pay"
        data = {
            "transactionId": transaction_id,
            "billerId": biller_id,
            "consumerNumber": consumer_number,
            "amount": amount,
            "paymentMode": payment_mode,
            "inputParams": input_params or {},
            "customerInfo": customer_info or {},
            "agentId": self.agent_id,
            "ouId": self.ou_id
        }
        
        logger.info(f"Processing payment for biller: {biller_id}, amount: {amount}")
        result = await self._make_request("POST", endpoint, data)
        result["transaction_id"] = transaction_id
        return result
    
    async def get_payment_status(self, transaction_id: str) -> Dict[str, Any]:
        endpoint = f"/billpayment/status/{transaction_id}"
        return await self._make_request("GET", endpoint)
    
    async def fetch_biller_mdm(self, biller_id: str) -> Dict[str, Any]:
        endpoint = f"/mdm/biller/{biller_id}"
        return await self._make_request("GET", endpoint)
    
    async def fetch_category_mdm(self, category: str) -> Dict[str, Any]:
        endpoint = f"/mdm/category/{category}"
        return await self._make_request("GET", endpoint)
    
    async def get_billers(
        self,
        category: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        endpoint = "/billers"
        params = {}
        if category:
            params["category"] = category
        if status:
            params["status"] = status
        return await self._make_request("GET", endpoint, params=params)
    
    async def search_billers(self, query: str) -> Dict[str, Any]:
        endpoint = "/billers/search"
        params = {"q": query}
        return await self._make_request("GET", endpoint, params=params)
    
    async def get_biller_input_params(self, biller_id: str) -> Dict[str, Any]:
        endpoint = f"/billers/{biller_id}/inputparams"
        return await self._make_request("GET", endpoint)
    
    async def register_complaint(
        self,
        transaction_id: str,
        complaint_type: str,
        description: str,
        complainant_info: Dict[str, str]
    ) -> Dict[str, Any]:
        endpoint = "/complaints/register"
        data = {
            "transactionId": transaction_id,
            "complaintType": complaint_type,
            "description": description,
            "complainant": complainant_info,
            "agentId": self.agent_id
        }
        
        logger.info(f"Registering complaint for transaction: {transaction_id}")
        return await self._make_request("POST", endpoint, data)
    
    async def get_complaint_status(self, complaint_id: str) -> Dict[str, Any]:
        endpoint = f"/complaints/{complaint_id}/status"
        return await self._make_request("GET", endpoint)
    
    async def validate_consumer(
        self,
        biller_id: str,
        consumer_number: str,
        input_params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        endpoint = "/validate/consumer"
        data = {
            "billerId": biller_id,
            "consumerNumber": consumer_number,
            "inputParams": input_params or {}
        }
        return await self._make_request("POST", endpoint, data)
    
    async def get_plans(self, biller_id: str) -> Dict[str, Any]:
        endpoint = f"/billers/{biller_id}/plans"
        return await self._make_request("GET", endpoint)
    
    async def recharge(
        self,
        biller_id: str,
        consumer_number: str,
        amount: float,
        plan_id: Optional[str] = None
    ) -> Dict[str, Any]:
        transaction_id = generate_transaction_id("RCH")
        
        endpoint = "/recharge"
        data = {
            "transactionId": transaction_id,
            "billerId": biller_id,
            "consumerNumber": consumer_number,
            "amount": amount,
            "planId": plan_id,
            "agentId": self.agent_id
        }
        
        result = await self._make_request("POST", endpoint, data)
        result["transaction_id"] = transaction_id
        return result
    
    async def get_banks(self) -> Dict[str, Any]:
        endpoint = "/banks"
        return await self._make_request("GET", endpoint)
    
    async def search_ifsc(self, query: str) -> Dict[str, Any]:
        endpoint = "/banks/ifsc/search"
        params = {"q": query}
        return await self._make_request("GET", endpoint, params=params)
    
    async def health_check(self) -> Dict[str, Any]:
        endpoint = "/health"
        return await self._make_request("GET", endpoint)


bbps_api_service = BBPSAPIService()
