from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_active_client, ClientInfo, get_optional_client
from app.core.cache import cache
from app.core.logging import logger
from app.core.security import generate_transaction_id, generate_reference_id
from app.models.optimized_models import Transaction, BillFetchRecord, Complaint, TransactionStatus
from app.services.bbps_api_service_async import bbps_api_service

router = APIRouter()


class FetchBillRequest(BaseModel):
    biller_id: str
    consumer_number: str
    input_params: Optional[Dict[str, Any]] = None


class PayBillRequest(BaseModel):
    biller_id: str
    consumer_number: str
    amount: float
    payment_mode: str = "CASH"
    input_params: Optional[Dict[str, Any]] = None
    customer_info: Optional[Dict[str, str]] = None


class ValidateConsumerRequest(BaseModel):
    biller_id: str
    consumer_number: str
    input_params: Optional[Dict[str, Any]] = None


class RechargeRequest(BaseModel):
    biller_id: str
    consumer_number: str
    amount: float
    plan_id: Optional[str] = None


class RegisterComplaintRequest(BaseModel):
    transaction_id: str
    complaint_type: str
    description: str
    complainant_name: str
    complainant_mobile: str
    complainant_email: Optional[str] = None


@router.post("/bill/fetch")
async def fetch_bill(
    request: FetchBillRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_client: ClientInfo = Depends(get_current_active_client)
):
    try:
        fetch_id = generate_reference_id("FETCH")
        
        result = await bbps_api_service.fetch_bill(
            biller_id=request.biller_id,
            consumer_number=request.consumer_number,
            input_params=request.input_params
        )
        
        fetch_record = BillFetchRecord(
            fetch_id=fetch_id,
            biller_id=request.biller_id,
            consumer_number=request.consumer_number,
            input_params=request.input_params,
            is_successful=result.get("success", False),
            response_code=str(result.get("status_code", "")),
            response_message=result.get("error"),
            raw_response=result.get("data")
        )
        
        if result.get("success") and result.get("data"):
            data = result["data"]
            fetch_record.bill_amount = data.get("billAmount")
            fetch_record.bill_date = data.get("billDate")
            fetch_record.due_date = data.get("dueDate")
            fetch_record.bill_number = data.get("billNumber")
            fetch_record.customer_name = data.get("customerName")
        
        db.add(fetch_record)
        
        return {
            "success": result.get("success", False),
            "fetch_id": fetch_id,
            "data": result.get("data"),
            "error": result.get("error"),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Bill fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bill/pay")
async def pay_bill(
    request: PayBillRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_client: ClientInfo = Depends(get_current_active_client)
):
    try:
        client = await db.scalar(
            select(Transaction).join(Transaction.client).filter(
                Transaction.client.has(client_id=current_client.client_id)
            ).limit(1)
        )
        
        result = await bbps_api_service.pay_bill(
            biller_id=request.biller_id,
            consumer_number=request.consumer_number,
            amount=request.amount,
            payment_mode=request.payment_mode,
            input_params=request.input_params,
            customer_info=request.customer_info
        )
        
        transaction = Transaction(
            transaction_id=result.get("transaction_id", generate_transaction_id("TXN")),
            biller_id=request.biller_id,
            consumer_number=request.consumer_number,
            consumer_name=request.customer_info.get("name") if request.customer_info else None,
            consumer_mobile=request.customer_info.get("mobile") if request.customer_info else None,
            consumer_email=request.customer_info.get("email") if request.customer_info else None,
            bill_amount=request.amount,
            convenience_fee=0,
            total_amount=request.amount,
            payment_mode=request.payment_mode,
            status=TransactionStatus.SUCCESS if result.get("success") else TransactionStatus.FAILED,
            status_message=result.get("error"),
            bbps_response=result.get("data")
        )
        
        if result.get("success") and result.get("data"):
            data = result["data"]
            transaction.bbps_transaction_id = data.get("bbpsTransactionId")
            transaction.bbps_reference_id = data.get("bbpsReferenceId")
            transaction.completed_at = datetime.utcnow()
        
        db.add(transaction)
        
        return {
            "success": result.get("success", False),
            "transaction_id": transaction.transaction_id,
            "bbps_transaction_id": transaction.bbps_transaction_id,
            "data": result.get("data"),
            "error": result.get("error"),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Bill payment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transaction/{transaction_id}")
async def get_transaction_status(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
    current_client: ClientInfo = Depends(get_current_active_client)
):
    try:
        transaction = await db.scalar(
            select(Transaction).where(Transaction.transaction_id == transaction_id)
        )
        
        if not transaction:
            bbps_result = await bbps_api_service.get_payment_status(transaction_id)
            return {
                "success": True,
                "source": "bbps",
                "data": bbps_result.get("data"),
                "error": bbps_result.get("error")
            }
        
        return {
            "success": True,
            "source": "local",
            "data": {
                "transaction_id": transaction.transaction_id,
                "biller_id": transaction.biller_id,
                "consumer_number": transaction.consumer_number,
                "amount": transaction.total_amount,
                "status": transaction.status.value if transaction.status else None,
                "status_message": transaction.status_message,
                "bbps_transaction_id": transaction.bbps_transaction_id,
                "created_at": transaction.created_at.isoformat() if transaction.created_at else None,
                "completed_at": transaction.completed_at.isoformat() if transaction.completed_at else None
            }
        }
    except Exception as e:
        logger.error(f"Get transaction status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions")
async def list_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    biller_id: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_client: ClientInfo = Depends(get_current_active_client)
):
    try:
        query = select(Transaction)
        
        if status:
            query = query.where(Transaction.status == status)
        if biller_id:
            query = query.where(Transaction.biller_id == biller_id)
        if from_date:
            query = query.where(Transaction.created_at >= from_date)
        if to_date:
            query = query.where(Transaction.created_at <= to_date)
        
        query = query.offset(skip).limit(limit).order_by(Transaction.created_at.desc())
        
        result = await db.execute(query)
        transactions = result.scalars().all()
        
        return {
            "success": True,
            "data": {
                "items": [
                    {
                        "transaction_id": t.transaction_id,
                        "biller_id": t.biller_id,
                        "consumer_number": t.consumer_number,
                        "amount": t.total_amount,
                        "status": t.status.value if t.status else None,
                        "created_at": t.created_at.isoformat() if t.created_at else None
                    }
                    for t in transactions
                ],
                "skip": skip,
                "limit": limit
            }
        }
    except Exception as e:
        logger.error(f"List transactions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate/consumer")
async def validate_consumer(
    request: ValidateConsumerRequest,
    current_client: ClientInfo = Depends(get_current_active_client)
):
    try:
        result = await bbps_api_service.validate_consumer(
            biller_id=request.biller_id,
            consumer_number=request.consumer_number,
            input_params=request.input_params
        )
        
        return {
            "success": result.get("success", False),
            "data": result.get("data"),
            "error": result.get("error"),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Validate consumer error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plans/{biller_id}")
async def get_biller_plans(
    biller_id: str,
    current_client: ClientInfo = Depends(get_current_active_client)
):
    try:
        cache_key = f"plans:{biller_id}"
        cached = await cache.get(cache_key)
        if cached:
            return {"success": True, "data": cached, "source": "cache"}
        
        result = await bbps_api_service.get_plans(biller_id)
        
        if result.get("success") and result.get("data"):
            await cache.set(cache_key, result["data"], ttl=3600)
        
        return {
            "success": result.get("success", False),
            "data": result.get("data"),
            "error": result.get("error"),
            "source": "bbps"
        }
    except Exception as e:
        logger.error(f"Get plans error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recharge")
async def process_recharge(
    request: RechargeRequest,
    db: AsyncSession = Depends(get_db),
    current_client: ClientInfo = Depends(get_current_active_client)
):
    try:
        result = await bbps_api_service.recharge(
            biller_id=request.biller_id,
            consumer_number=request.consumer_number,
            amount=request.amount,
            plan_id=request.plan_id
        )
        
        transaction = Transaction(
            transaction_id=result.get("transaction_id", generate_transaction_id("RCH")),
            biller_id=request.biller_id,
            consumer_number=request.consumer_number,
            bill_amount=request.amount,
            total_amount=request.amount,
            payment_mode="RECHARGE",
            status=TransactionStatus.SUCCESS if result.get("success") else TransactionStatus.FAILED,
            bbps_response=result.get("data")
        )
        
        db.add(transaction)
        
        return {
            "success": result.get("success", False),
            "transaction_id": transaction.transaction_id,
            "data": result.get("data"),
            "error": result.get("error"),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Recharge error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/complaints/register")
async def register_complaint(
    request: RegisterComplaintRequest,
    db: AsyncSession = Depends(get_db),
    current_client: ClientInfo = Depends(get_current_active_client)
):
    try:
        complaint_id = generate_reference_id("CMP")
        
        result = await bbps_api_service.register_complaint(
            transaction_id=request.transaction_id,
            complaint_type=request.complaint_type,
            description=request.description,
            complainant_info={
                "name": request.complainant_name,
                "mobile": request.complainant_mobile,
                "email": request.complainant_email
            }
        )
        
        complaint = Complaint(
            complaint_id=complaint_id,
            transaction_id=request.transaction_id,
            complainant_name=request.complainant_name,
            complainant_mobile=request.complainant_mobile,
            complainant_email=request.complainant_email,
            complaint_type=request.complaint_type,
            complaint_description=request.description,
            bbps_response=result.get("data")
        )
        
        if result.get("success") and result.get("data"):
            complaint.bbps_complaint_id = result["data"].get("complaintId")
        
        db.add(complaint)
        
        return {
            "success": result.get("success", False),
            "complaint_id": complaint_id,
            "bbps_complaint_id": complaint.bbps_complaint_id,
            "data": result.get("data"),
            "error": result.get("error"),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Register complaint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/complaints/{complaint_id}")
async def get_complaint_status(
    complaint_id: str,
    db: AsyncSession = Depends(get_db),
    current_client: ClientInfo = Depends(get_current_active_client)
):
    try:
        complaint = await db.scalar(
            select(Complaint).where(Complaint.complaint_id == complaint_id)
        )
        
        if not complaint:
            raise HTTPException(status_code=404, detail="Complaint not found")
        
        if complaint.bbps_complaint_id:
            bbps_result = await bbps_api_service.get_complaint_status(complaint.bbps_complaint_id)
            if bbps_result.get("success") and bbps_result.get("data"):
                return {
                    "success": True,
                    "complaint_id": complaint_id,
                    "bbps_status": bbps_result["data"],
                    "local_status": complaint.status.value if complaint.status else None
                }
        
        return {
            "success": True,
            "data": {
                "complaint_id": complaint.complaint_id,
                "transaction_id": complaint.transaction_id,
                "complaint_type": complaint.complaint_type,
                "description": complaint.complaint_description,
                "status": complaint.status.value if complaint.status else None,
                "resolution": complaint.resolution,
                "created_at": complaint.created_at.isoformat() if complaint.created_at else None,
                "resolved_at": complaint.resolved_at.isoformat() if complaint.resolved_at else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get complaint status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/complaints")
async def list_complaints(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    complaint_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_client: ClientInfo = Depends(get_current_active_client)
):
    try:
        query = select(Complaint)
        
        if status:
            query = query.where(Complaint.status == status)
        if complaint_type:
            query = query.where(Complaint.complaint_type == complaint_type)
        
        query = query.offset(skip).limit(limit).order_by(Complaint.created_at.desc())
        
        result = await db.execute(query)
        complaints = result.scalars().all()
        
        return {
            "success": True,
            "data": {
                "items": [
                    {
                        "complaint_id": c.complaint_id,
                        "transaction_id": c.transaction_id,
                        "complaint_type": c.complaint_type,
                        "status": c.status.value if c.status else None,
                        "created_at": c.created_at.isoformat() if c.created_at else None
                    }
                    for c in complaints
                ],
                "skip": skip,
                "limit": limit
            }
        }
    except Exception as e:
        logger.error(f"List complaints error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
