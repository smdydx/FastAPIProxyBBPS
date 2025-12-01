from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class BillerInfo(BaseModel):
    biller_id: str
    biller_name: str
    biller_category: str
    state: Optional[str] = None
    city: Optional[str] = None
    logo_url: Optional[str] = None
    input_params: Optional[List[Dict[str, Any]]] = None


class BillDetails(BaseModel):
    biller_id: str
    consumer_id: str
    consumer_name: Optional[str] = None
    bill_amount: float
    bill_date: Optional[str] = None
    due_date: Optional[str] = None
    bill_number: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = None


class PaymentReceipt(BaseModel):
    transaction_id: str
    bbps_reference_id: str
    biller_id: str
    consumer_id: str
    amount: float
    payment_mode: str
    status: str
    timestamp: str
    receipt_number: Optional[str] = None


class TransactionStatus(BaseModel):
    transaction_id: str
    status: str
    status_code: str
    message: Optional[str] = None
    timestamp: str


class RechargePlan(BaseModel):
    plan_id: str
    plan_name: str
    amount: float
    validity: str
    description: Optional[str] = None
    data: Optional[str] = None
    talktime: Optional[str] = None
    sms: Optional[str] = None


class BBPSResponse(BaseModel):
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Response message")
    data: Optional[Any] = Field(default=None, description="Response data")
    request_id: Optional[str] = Field(default=None, description="Unique request identifier")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    errors: Optional[List[Dict[str, str]]] = Field(default=None, description="List of errors if any")


class ProxyErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: str
    details: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
