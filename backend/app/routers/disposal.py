from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import get_current_active_user, require_roles

router = APIRouter(prefix="/api/disposal", tags=["处置记录"])


@router.get("", response_model=List[schemas.DisposalRecordResponse])
async def get_disposal_records(
    instruction_id: Optional[int] = None,
    anomaly_id: Optional[int] = None,
    handler_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    query = db.query(models.DisposalRecord)
    if instruction_id:
        query = query.filter(models.DisposalRecord.instruction_id == instruction_id)
    if anomaly_id:
        query = query.filter(models.DisposalRecord.anomaly_id == anomaly_id)
    if handler_id:
        query = query.filter(models.DisposalRecord.handler_id == handler_id)
    return query.order_by(models.DisposalRecord.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{record_id}", response_model=schemas.DisposalRecordResponse)
async def get_disposal_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    record = db.query(models.DisposalRecord).filter(models.DisposalRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="处置记录不存在")
    return record


@router.get("/{record_id}/snapshot-data")
async def get_disposal_snapshot_data(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    record = db.query(models.DisposalRecord).filter(models.DisposalRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="处置记录不存在")

    point_ids = record.snapshot_point_ids or []
    if not point_ids and record.anomaly_id:
        anomaly = db.query(models.AnomalyRecord).filter(
            models.AnomalyRecord.id == record.anomaly_id
        ).first()
        if anomaly:
            point_ids = [anomaly.point_id]

    query = """
        SELECT md.point_id, md.time, md.value, md.remark
        FROM monitor_data md
        WHERE md.time >= :start_time AND md.time <= :end_time
    """
    params = {
        "start_time": record.snapshot_start_time,
        "end_time": record.snapshot_end_time
    }

    if point_ids:
        query += " AND md.point_id = ANY(:point_ids)"
        params["point_ids"] = point_ids

    query += " ORDER BY md.point_id, md.time"

    result = db.execute(query, params)
    rows = result.fetchall()

    data = {}
    points_info = {}
    for row in rows:
        pid = row[0]
        if pid not in data:
            data[pid] = []
            point = db.query(models.MonitorPoint).filter(models.MonitorPoint.id == pid).first()
            if point:
                points_info[pid] = {
                    "id": point.id,
                    "point_code": point.point_code,
                    "point_name": point.point_name,
                    "warning_threshold": float(point.warning_threshold) if point.warning_threshold else None,
                    "danger_threshold": float(point.danger_threshold) if point.danger_threshold else None,
                }
        data[pid].append({
            "time": row[1],
            "value": float(row[2]),
            "remark": row[3]
        })

    return {
        "record": schemas.DisposalRecordResponse.model_validate(record).model_dump(),
        "snapshot_data": data,
        "points_info": points_info
    }


@router.post("", response_model=schemas.DisposalRecordResponse)
async def create_disposal_record(
    data: schemas.DisposalRecordCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("DISPATCH", "GEOLOGIST", "SAFETY_HEAD"))
):
    record = models.DisposalRecord(
        **data.model_dump(),
        handler_id=current_user.id
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
