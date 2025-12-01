from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class SingleBillerMDMRequest(BaseModel):
    biller_id: str = Field(..., description="Biller ID to fetch MDM for")


class MultipleBillerMDMRequest(BaseModel):
    biller_ids: List[str] = Field(..., description="List of biller IDs to fetch MDM for")


class CategoryMDMRequest(BaseModel):
    category: str = Field(..., description="Category name to fetch MDM for")


class MDMSearchRequest(BaseModel):
    search_term: Optional[str] = Field(None, description="Search term")
    category: Optional[str] = Field(None, description="Filter by category")
    limit: int = Field(50, ge=1, le=500, description="Number of results")
    offset: int = Field(0, ge=0, description="Offset for pagination")


class AgentDeviceInfo(BaseModel):
    ip: str = Field(..., description="IP address of the device")
    init_channel: str = Field(..., description="Channel (AGT, INT, MOB, INTB, etc.)")
    mac: Optional[str] = Field(None, description="MAC address of the device")


class BillFetchRequest(BaseModel):
    app_provider: str = Field(..., description="App provider code (LCR, ODH, etc.)")
    fetched_by_user: str = Field(..., description="User ID initiating the fetch")
    reference_no: str = Field(..., description="User-supplied reference number")
    biller_id: str = Field(..., description="Biller ID (14 chars)")
    input_params: Dict[str, str] = Field(..., description="Input parameters as key-value pairs")
    customer_mobile: str = Field(..., description="Customer mobile number")
    customer_email: Optional[str] = Field(None, description="Customer email (optional)")
    amount: Optional[str] = Field(None, description="Amount for recharge billers")
    agent_device_info: Optional[AgentDeviceInfo] = Field(None, description="Agent device information")


class BillPaymentRequest(BaseModel):
    app_provider: str = Field(..., description="App provider code")
    paid_by_user: str = Field(..., description="User ID making payment")
    reference_no: str = Field(..., description="User-supplied reference number")
    biller_id: str = Field(..., description="Biller ID")
    input_params: Dict[str, str] = Field(..., description="Input parameters")
    amount: str = Field(..., description="Payment amount")
    customer_mobile: str = Field(..., description="Customer mobile number")
    customer_email: Optional[str] = Field(None, description="Customer email")
    payment_mode: str = Field(..., description="Payment mode (CASH, ONLINE, etc.)")
    agent_device_info: Optional[AgentDeviceInfo] = Field(None, description="Agent device information")


class ComplaintRegisterRequest(BaseModel):
    transaction_id: str = Field(..., description="Original transaction ID")
    complaint_type: str = Field(..., description="Type of complaint")
    description: str = Field(..., description="Complaint description")
    customer_mobile: str = Field(..., description="Customer mobile number")
    customer_email: Optional[str] = Field(None, description="Customer email")


class BillFetchHistoryRequest(BaseModel):
    biller_id: Optional[str] = Field(None, description="Filter by biller ID")
    customer_mobile: Optional[str] = Field(None, description="Filter by customer mobile")
    from_date: Optional[str] = Field(None, description="From date (YYYY-MM-DD)")
    to_date: Optional[str] = Field(None, description="To date (YYYY-MM-DD)")
    limit: int = Field(50, ge=1, le=500, description="Number of results")
    offset: int = Field(0, ge=0, description="Offset for pagination")


class ValidateParamsRequest(BaseModel):
    biller_id: str = Field(..., description="Biller ID")
    input_params: Dict[str, str] = Field(..., description="Parameters to validate")
