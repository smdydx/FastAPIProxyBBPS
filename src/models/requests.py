from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum


class PaymentMode(str, Enum):
    UPI = "UPI"
    NETBANKING = "NETBANKING"
    DEBIT_CARD = "DEBIT_CARD"
    CREDIT_CARD = "CREDIT_CARD"
    WALLET = "WALLET"


class FetchBillersRequest(BaseModel):
    state: Optional[str] = None
    city: Optional[str] = None
    search_term: Optional[str] = None


class FetchBillRequest(BaseModel):
    biller_id: str = Field(..., description="Unique identifier of the biller")
    consumer_id: str = Field(..., description="Consumer/Customer ID for the bill")
    additional_params: Optional[Dict[str, str]] = Field(default=None, description="Additional parameters required by specific billers")


class PayBillRequest(BaseModel):
    biller_id: str = Field(..., description="Unique identifier of the biller")
    consumer_id: str = Field(..., description="Consumer/Customer ID")
    amount: float = Field(..., gt=0, description="Payment amount")
    payment_mode: PaymentMode = Field(..., description="Mode of payment")
    transaction_reference: str = Field(..., description="Unique transaction reference from client")
    additional_params: Optional[Dict[str, str]] = Field(default=None, description="Additional parameters")


class BillStatusRequest(BaseModel):
    transaction_id: str = Field(..., description="BBPS transaction ID")
    biller_id: Optional[str] = None


class RechargeRequest(BaseModel):
    biller_id: str = Field(..., description="Biller/Operator ID")
    consumer_id: str = Field(..., description="Mobile number, DTH ID, etc.")
    amount: float = Field(..., gt=0, description="Recharge amount")
    plan_id: Optional[str] = Field(default=None, description="Plan ID for specific plan recharge")
    payment_mode: PaymentMode = Field(..., description="Mode of payment")
    transaction_reference: str = Field(..., description="Unique transaction reference")


class FetchPlansRequest(BaseModel):
    biller_id: str = Field(..., description="Operator/Biller ID")
    consumer_id: Optional[str] = Field(default=None, description="Mobile number for personalized plans")
    circle: Optional[str] = Field(default=None, description="Telecom circle")


class GenericProxyRequest(BaseModel):
    endpoint: str = Field(..., description="Target endpoint path")
    method: str = Field(default="POST", description="HTTP method")
    payload: Optional[Dict[str, Any]] = Field(default=None, description="Request payload")
    headers: Optional[Dict[str, str]] = Field(default=None, description="Additional headers")
