from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel
import csv
import io
import aiofiles
import uuid

from app.core.database import get_db
from app.core.auth import get_current_active_client, ClientInfo, require_scopes
from app.core.logging import logger
from app.core.config import settings
from app.core.security import generate_reference_id
from app.models.optimized_models import Biller, BillerMDM, BillerInputParam, CSVUpload, BillerStatus

router = APIRouter()


class BillerCreateRequest(BaseModel):
    biller_id: str
    biller_name: str
    biller_alias: Optional[str] = None
    category: str
    sub_category: Optional[str] = None
    is_adhoc: bool = False
    supports_billvalidation: bool = True
    supports_payment: bool = True
    biller_description: Optional[str] = None
    coverage: Optional[str] = None
    min_amount: float = 0
    max_amount: float = 1000000
    payment_modes: List[str] = []
    payment_channels: List[str] = []


class BillerUpdateRequest(BaseModel):
    biller_name: Optional[str] = None
    biller_alias: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    status: Optional[str] = None
    is_adhoc: Optional[bool] = None
    supports_billvalidation: Optional[bool] = None
    supports_payment: Optional[bool] = None
    biller_description: Optional[str] = None
    coverage: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    payment_modes: Optional[List[str]] = None
    payment_channels: Optional[List[str]] = None


class InputParamRequest(BaseModel):
    param_name: str
    param_label: Optional[str] = None
    param_type: str = "text"
    is_mandatory: bool = True
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    regex_pattern: Optional[str] = None
    options: Optional[List[str]] = None
    order_index: int = 0


@router.post("/billers")
async def create_biller(
    request: BillerCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_client: ClientInfo = Depends(require_scopes("admin"))
):
    try:
        existing = await db.scalar(
            select(Biller).where(Biller.biller_id == request.biller_id)
        )
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Biller with ID {request.biller_id} already exists"
            )
        
        biller = Biller(
            biller_id=request.biller_id,
            biller_name=request.biller_name,
            biller_alias=request.biller_alias,
            category=request.category,
            sub_category=request.sub_category,
            is_adhoc=request.is_adhoc,
            supports_billvalidation=request.supports_billvalidation,
            supports_payment=request.supports_payment,
            biller_description=request.biller_description,
            coverage=request.coverage,
            min_amount=request.min_amount,
            max_amount=request.max_amount,
            payment_modes=request.payment_modes,
            payment_channels=request.payment_channels,
            status=BillerStatus.ACTIVE
        )
        
        db.add(biller)
        await db.flush()
        
        return {
            "success": True,
            "message": "Biller created successfully",
            "data": {"biller_id": biller.biller_id}
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create biller error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/billers/{biller_id}")
async def update_biller(
    biller_id: str,
    request: BillerUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_client: ClientInfo = Depends(require_scopes("admin"))
):
    try:
        biller = await db.scalar(
            select(Biller).where(Biller.biller_id == biller_id)
        )
        if not biller:
            raise HTTPException(status_code=404, detail="Biller not found")
        
        update_data = request.dict(exclude_unset=True, exclude_none=True)
        
        for field, value in update_data.items():
            if field == "status":
                value = BillerStatus(value)
            setattr(biller, field, value)
        
        return {
            "success": True,
            "message": "Biller updated successfully",
            "data": {"biller_id": biller_id}
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update biller error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/billers/{biller_id}")
async def delete_biller(
    biller_id: str,
    db: AsyncSession = Depends(get_db),
    current_client: ClientInfo = Depends(require_scopes("admin"))
):
    try:
        biller = await db.scalar(
            select(Biller).where(Biller.biller_id == biller_id)
        )
        if not biller:
            raise HTTPException(status_code=404, detail="Biller not found")
        
        biller.status = BillerStatus.INACTIVE
        
        return {
            "success": True,
            "message": "Biller deactivated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete biller error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/billers/{biller_id}/input-params")
async def add_input_param(
    biller_id: str,
    request: InputParamRequest,
    db: AsyncSession = Depends(get_db),
    current_client: ClientInfo = Depends(require_scopes("admin"))
):
    try:
        biller = await db.scalar(
            select(Biller).where(Biller.biller_id == biller_id)
        )
        if not biller:
            raise HTTPException(status_code=404, detail="Biller not found")
        
        param = BillerInputParam(
            biller_id=biller_id,
            param_name=request.param_name,
            param_label=request.param_label or request.param_name,
            param_type=request.param_type,
            is_mandatory=request.is_mandatory,
            min_length=request.min_length,
            max_length=request.max_length,
            regex_pattern=request.regex_pattern,
            options=request.options,
            order_index=request.order_index
        )
        
        db.add(param)
        await db.flush()
        
        return {
            "success": True,
            "message": "Input parameter added successfully",
            "data": {"param_id": param.id}
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add input param error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/billers/{biller_id}/input-params")
async def get_input_params(
    biller_id: str,
    db: AsyncSession = Depends(get_db),
    current_client: ClientInfo = Depends(get_current_active_client)
):
    try:
        result = await db.execute(
            select(BillerInputParam)
            .where(BillerInputParam.biller_id == biller_id)
            .order_by(BillerInputParam.order_index)
        )
        params = result.scalars().all()
        
        return {
            "success": True,
            "data": [
                {
                    "id": p.id,
                    "param_name": p.param_name,
                    "param_label": p.param_label,
                    "param_type": p.param_type,
                    "is_mandatory": p.is_mandatory,
                    "min_length": p.min_length,
                    "max_length": p.max_length,
                    "regex_pattern": p.regex_pattern,
                    "options": p.options,
                    "order_index": p.order_index
                }
                for p in params
            ]
        }
    except Exception as e:
        logger.error(f"Get input params error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/billers/{biller_id}/input-params/{param_id}")
async def delete_input_param(
    biller_id: str,
    param_id: int,
    db: AsyncSession = Depends(get_db),
    current_client: ClientInfo = Depends(require_scopes("admin"))
):
    try:
        param = await db.scalar(
            select(BillerInputParam).where(
                BillerInputParam.id == param_id,
                BillerInputParam.biller_id == biller_id
            )
        )
        if not param:
            raise HTTPException(status_code=404, detail="Input parameter not found")
        
        await db.delete(param)
        
        return {
            "success": True,
            "message": "Input parameter deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete input param error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_biller_csv(upload_id: str, file_path: str, db_factory):
    async with db_factory() as db:
        upload = await db.scalar(
            select(CSVUpload).where(CSVUpload.upload_id == upload_id)
        )
        if not upload:
            return
        
        upload.status = "processing"
        await db.commit()
        
        try:
            async with aiofiles.open(file_path, mode='r') as f:
                content = await f.read()
            
            reader = csv.DictReader(io.StringIO(content))
            rows = list(reader)
            
            upload.total_records = len(rows)
            success_count = 0
            failed_count = 0
            processing_log = []
            
            for row in rows:
                try:
                    biller_id = row.get('biller_id', '').strip()
                    biller_name = row.get('biller_name', '').strip()
                    category = row.get('category', '').strip()
                    
                    if not biller_id or not biller_name or not category:
                        failed_count += 1
                        processing_log.append({
                            "row": row,
                            "error": "Missing required fields"
                        })
                        continue
                    
                    existing = await db.scalar(
                        select(Biller).where(Biller.biller_id == biller_id)
                    )
                    
                    if existing:
                        existing.biller_name = biller_name
                        existing.category = category
                        existing.sub_category = row.get('sub_category', '').strip() or None
                        existing.biller_alias = row.get('biller_alias', '').strip() or None
                        existing.coverage = row.get('coverage', '').strip() or None
                    else:
                        biller = Biller(
                            biller_id=biller_id,
                            biller_name=biller_name,
                            category=category,
                            sub_category=row.get('sub_category', '').strip() or None,
                            biller_alias=row.get('biller_alias', '').strip() or None,
                            coverage=row.get('coverage', '').strip() or None,
                            status=BillerStatus.ACTIVE
                        )
                        db.add(biller)
                    
                    success_count += 1
                    upload.processed_records += 1
                    
                except Exception as e:
                    failed_count += 1
                    processing_log.append({
                        "row": row,
                        "error": str(e)
                    })
            
            upload.success_records = success_count
            upload.failed_records = failed_count
            upload.status = "completed"
            upload.completed_at = datetime.utcnow()
            upload.processing_log = processing_log[:100]
            
            await db.commit()
            
        except Exception as e:
            upload.status = "failed"
            upload.error_message = str(e)
            await db.commit()
            logger.error(f"CSV processing error: {e}")


@router.post("/upload/billers")
async def upload_billers_csv(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    current_client: ClientInfo = Depends(require_scopes("admin"))
):
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=400,
                detail="Only CSV files are allowed"
            )
        
        content = await file.read()
        if len(content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed ({settings.MAX_UPLOAD_SIZE} bytes)"
            )
        
        upload_id = generate_reference_id("UPL")
        file_path = settings.CSV_UPLOAD_DIR / f"{upload_id}_{file.filename}"
        
        async with aiofiles.open(file_path, mode='wb') as f:
            await f.write(content)
        
        upload = CSVUpload(
            upload_id=upload_id,
            filename=file.filename,
            file_path=str(file_path),
            file_size=len(content),
            upload_type="billers",
            status="pending",
            uploaded_by=current_client.client_id
        )
        
        db.add(upload)
        await db.flush()
        
        from app.core.database import get_session_factory
        if background_tasks:
            background_tasks.add_task(
                process_biller_csv,
                upload_id,
                str(file_path),
                get_session_factory()
            )
        
        return {
            "success": True,
            "message": "File uploaded successfully. Processing started.",
            "data": {
                "upload_id": upload_id,
                "filename": file.filename,
                "file_size": len(content)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload billers CSV error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/upload/{upload_id}")
async def get_upload_status(
    upload_id: str,
    db: AsyncSession = Depends(get_db),
    current_client: ClientInfo = Depends(require_scopes("admin"))
):
    try:
        upload = await db.scalar(
            select(CSVUpload).where(CSVUpload.upload_id == upload_id)
        )
        if not upload:
            raise HTTPException(status_code=404, detail="Upload not found")
        
        return {
            "success": True,
            "data": {
                "upload_id": upload.upload_id,
                "filename": upload.filename,
                "upload_type": upload.upload_type,
                "status": upload.status,
                "total_records": upload.total_records,
                "processed_records": upload.processed_records,
                "success_records": upload.success_records,
                "failed_records": upload.failed_records,
                "error_message": upload.error_message,
                "created_at": upload.created_at.isoformat() if upload.created_at else None,
                "completed_at": upload.completed_at.isoformat() if upload.completed_at else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get upload status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_biller_stats(
    db: AsyncSession = Depends(get_db),
    current_client: ClientInfo = Depends(get_current_active_client)
):
    try:
        total = await db.scalar(select(func.count(Biller.id)))
        
        by_status = {}
        for status in BillerStatus:
            count = await db.scalar(
                select(func.count(Biller.id)).where(Biller.status == status)
            )
            by_status[status.value] = count
        
        result = await db.execute(
            select(Biller.category, func.count(Biller.id))
            .group_by(Biller.category)
        )
        by_category = dict(result.all())
        
        return {
            "success": True,
            "data": {
                "total": total,
                "by_status": by_status,
                "by_category": by_category
            }
        }
    except Exception as e:
        logger.error(f"Get biller stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
