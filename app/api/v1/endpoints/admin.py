from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.auth import get_current_active_client, ClientInfo, require_scopes
from app.core.logging import logger
from app.models.optimized_models import (
    Client, APIKey, Biller, Transaction, Complaint, AuditLog, CSVUpload
)
from app.core.security import generate_api_key, hash_api_key, get_password_hash

router = APIRouter()


@router.get("/dashboard")
async def get_admin_dashboard(
    db: AsyncSession = Depends(get_db),
    current_client: ClientInfo = Depends(require_scopes("admin"))
):
    try:
        total_clients = await db.scalar(select(func.count(Client.id)))
        active_clients = await db.scalar(
            select(func.count(Client.id)).where(Client.is_active == True)
        )
        
        total_billers = await db.scalar(select(func.count(Biller.id)))
        active_billers = await db.scalar(
            select(func.count(Biller.id)).where(Biller.status == "active")
        )
        
        total_transactions = await db.scalar(select(func.count(Transaction.id)))
        
        today = datetime.utcnow().date()
        today_transactions = await db.scalar(
            select(func.count(Transaction.id)).where(
                func.date(Transaction.created_at) == today
            )
        )
        
        today_volume = await db.scalar(
            select(func.sum(Transaction.total_amount)).where(
                func.date(Transaction.created_at) == today
            )
        ) or 0
        
        open_complaints = await db.scalar(
            select(func.count(Complaint.id)).where(Complaint.status == "open")
        )
        
        return {
            "success": True,
            "data": {
                "clients": {
                    "total": total_clients,
                    "active": active_clients
                },
                "billers": {
                    "total": total_billers,
                    "active": active_billers
                },
                "transactions": {
                    "total": total_transactions,
                    "today": today_transactions,
                    "today_volume": float(today_volume)
                },
                "complaints": {
                    "open": open_complaints
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/clients")
async def list_clients(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_client: ClientInfo = Depends(require_scopes("admin"))
):
    try:
        query = select(Client)
        if is_active is not None:
            query = query.where(Client.is_active == is_active)
        
        query = query.offset(skip).limit(limit).order_by(Client.created_at.desc())
        
        result = await db.execute(query)
        clients = result.scalars().all()
        
        count_query = select(func.count(Client.id))
        if is_active is not None:
            count_query = count_query.where(Client.is_active == is_active)
        total = await db.scalar(count_query)
        
        return {
            "success": True,
            "data": {
                "items": [
                    {
                        "id": c.id,
                        "client_id": c.client_id,
                        "client_name": c.client_name,
                        "is_active": c.is_active,
                        "rate_limit": c.rate_limit,
                        "contact_email": c.contact_email,
                        "created_at": c.created_at.isoformat() if c.created_at else None,
                        "last_login_at": c.last_login_at.isoformat() if c.last_login_at else None
                    }
                    for c in clients
                ],
                "total": total,
                "skip": skip,
                "limit": limit
            }
        }
    except Exception as e:
        logger.error(f"List clients error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clients")
async def create_client(
    client_id: str,
    client_name: str,
    client_secret: str,
    contact_email: Optional[str] = None,
    contact_phone: Optional[str] = None,
    rate_limit: int = 100,
    scopes: List[str] = ["read", "write"],
    db: AsyncSession = Depends(get_db),
    current_client: ClientInfo = Depends(require_scopes("admin"))
):
    try:
        existing = await db.scalar(
            select(Client).where(Client.client_id == client_id)
        )
        if existing:
            raise HTTPException(
                status_code=400, 
                detail=f"Client with ID {client_id} already exists"
            )
        
        new_client = Client(
            client_id=client_id,
            client_name=client_name,
            client_secret_hash=get_password_hash(client_secret),
            contact_email=contact_email,
            contact_phone=contact_phone,
            rate_limit=rate_limit,
            scopes=scopes,
            is_active=True
        )
        
        db.add(new_client)
        await db.flush()
        
        return {
            "success": True,
            "message": "Client created successfully",
            "data": {
                "id": new_client.id,
                "client_id": new_client.client_id,
                "client_name": new_client.client_name
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create client error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/clients/{client_id}")
async def update_client(
    client_id: str,
    client_name: Optional[str] = None,
    is_active: Optional[bool] = None,
    rate_limit: Optional[int] = None,
    contact_email: Optional[str] = None,
    contact_phone: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_client: ClientInfo = Depends(require_scopes("admin"))
):
    try:
        client = await db.scalar(
            select(Client).where(Client.client_id == client_id)
        )
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        if client_name is not None:
            client.client_name = client_name
        if is_active is not None:
            client.is_active = is_active
        if rate_limit is not None:
            client.rate_limit = rate_limit
        if contact_email is not None:
            client.contact_email = contact_email
        if contact_phone is not None:
            client.contact_phone = contact_phone
        
        return {
            "success": True,
            "message": "Client updated successfully",
            "data": {"client_id": client_id}
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update client error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clients/{client_id}/api-keys")
async def create_api_key(
    client_id: str,
    key_name: str = "default",
    scopes: List[str] = ["read", "write"],
    expires_days: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_client: ClientInfo = Depends(require_scopes("admin"))
):
    try:
        client = await db.scalar(
            select(Client).where(Client.client_id == client_id)
        )
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        raw_key = generate_api_key()
        key_hash = hash_api_key(raw_key)
        
        expires_at = None
        if expires_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_days)
        
        api_key = APIKey(
            key_hash=key_hash,
            key_prefix=raw_key[:12],
            client_id=client.id,
            name=key_name,
            scopes=scopes,
            expires_at=expires_at
        )
        
        db.add(api_key)
        await db.flush()
        
        return {
            "success": True,
            "message": "API key created successfully",
            "data": {
                "api_key": raw_key,
                "key_prefix": raw_key[:12],
                "name": key_name,
                "expires_at": expires_at.isoformat() if expires_at else None
            },
            "warning": "Please save this API key securely. It will not be shown again."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create API key error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions")
async def list_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    biller_id: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_client: ClientInfo = Depends(require_scopes("admin"))
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
                        "id": t.id,
                        "transaction_id": t.transaction_id,
                        "biller_id": t.biller_id,
                        "consumer_number": t.consumer_number,
                        "total_amount": t.total_amount,
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


@router.get("/audit-logs")
async def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    from_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_client: ClientInfo = Depends(require_scopes("admin"))
):
    try:
        query = select(AuditLog)
        
        if entity_type:
            query = query.where(AuditLog.entity_type == entity_type)
        if action:
            query = query.where(AuditLog.action == action)
        if from_date:
            query = query.where(AuditLog.created_at >= from_date)
        
        query = query.offset(skip).limit(limit).order_by(AuditLog.created_at.desc())
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        return {
            "success": True,
            "data": {
                "items": [
                    {
                        "id": log.id,
                        "entity_type": log.entity_type,
                        "entity_id": log.entity_id,
                        "action": log.action,
                        "actor_id": log.actor_id,
                        "created_at": log.created_at.isoformat() if log.created_at else None
                    }
                    for log in logs
                ],
                "skip": skip,
                "limit": limit
            }
        }
    except Exception as e:
        logger.error(f"List audit logs error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/csv-uploads")
async def list_csv_uploads(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    upload_type: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_client: ClientInfo = Depends(require_scopes("admin"))
):
    try:
        query = select(CSVUpload)
        
        if upload_type:
            query = query.where(CSVUpload.upload_type == upload_type)
        if status:
            query = query.where(CSVUpload.status == status)
        
        query = query.offset(skip).limit(limit).order_by(CSVUpload.created_at.desc())
        
        result = await db.execute(query)
        uploads = result.scalars().all()
        
        return {
            "success": True,
            "data": {
                "items": [
                    {
                        "id": u.id,
                        "upload_id": u.upload_id,
                        "filename": u.filename,
                        "upload_type": u.upload_type,
                        "total_records": u.total_records,
                        "processed_records": u.processed_records,
                        "success_records": u.success_records,
                        "failed_records": u.failed_records,
                        "status": u.status,
                        "created_at": u.created_at.isoformat() if u.created_at else None
                    }
                    for u in uploads
                ],
                "skip": skip,
                "limit": limit
            }
        }
    except Exception as e:
        logger.error(f"List CSV uploads error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
