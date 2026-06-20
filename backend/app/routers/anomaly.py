from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import get_current_active_user, require_roles

router = APIRouter(prefix="/api/anomaly", tags=["异常管理"])


@router.get("/records", response_model=List[schemas.AnomalyRecordResponse])
async def get_anomaly_records(
    status: Optional[str] = None,
    alert_level: Optional[models.AlertLevel] = None,
    is_confirmed: Optional[bool] = None,
    point_id: Optional[int] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    query = db.query(models.AnomalyRecord)
    if status:
        query = query.filter(models.AnomalyRecord.status == status)
    if alert_level:
        query = query.filter(models.AnomalyRecord.alert_level == alert_level)
    if is_confirmed is not None:
        query = query.filter(models.AnomalyRecord.is_confirmed == is_confirmed)
    if point_id:
        query = query.filter(models.AnomalyRecord.point_id == point_id)
    if start_time:
        query = query.filter(models.AnomalyRecord.start_time >= start_time)
    if end_time:
        query = query.filter(models.AnomalyRecord.start_time <= end_time)

    return query.order_by(models.AnomalyRecord.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/records/{record_id}", response_model=schemas.AnomalyRecordResponse)
async def get_anomaly_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    record = db.query(models.AnomalyRecord).filter(models.AnomalyRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="异常记录不存在")
    return record


@router.post("/records/{record_id}/confirm", response_model=schemas.AnomalyRecordResponse)
async def confirm_anomaly(
    record_id: int,
    confirm_data: schemas.AnomalyConfirm,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("GEOLOGIST", "SAFETY_HEAD"))
):
    record = db.query(models.AnomalyRecord).filter(models.AnomalyRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="异常记录不存在")
    if record.is_confirmed:
        raise HTTPException(status_code=400, detail="该异常已确认")

    record.is_confirmed = confirm_data.is_confirmed
    record.confirmed_by = current_user.id
    record.confirmed_at = datetime.utcnow()
    record.confirmation_note = confirm_data.confirmation_note
    db.commit()
    db.refresh(record)
    return record


@router.post("/records/{record_id}/close", response_model=schemas.AnomalyRecordResponse)
async def close_anomaly(
    record_id: int,
    note: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("GEOLOGIST", "SAFETY_HEAD"))
):
    record = db.query(models.AnomalyRecord).filter(models.AnomalyRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="异常记录不存在")
    if record.status == "CLOSED":
        raise HTTPException(status_code=400, detail="该异常已关闭")

    record.status = "CLOSED"
    record.end_time = datetime.utcnow()
    if not record.confirmation_note:
        record.confirmation_note = note
    else:
        record.confirmation_note = record.confirmation_note + "\n关闭说明: " + note
    db.commit()
    db.refresh(record)
    return record
