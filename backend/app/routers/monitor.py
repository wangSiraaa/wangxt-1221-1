from typing import List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from app.database import get_db
from app import models, schemas
from app.auth import get_current_active_user, require_roles

router = APIRouter(prefix="/api/monitor", tags=["监测管理"])


@router.get("/types", response_model=List[schemas.MonitorTypeResponse])
async def get_monitor_types(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    return db.query(models.MonitorType).all()


@router.get("/points", response_model=List[schemas.MonitorPointResponse])
async def get_monitor_points(
    monitor_type_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    query = db.query(models.MonitorPoint)
    if monitor_type_id is not None:
        query = query.filter(models.MonitorPoint.monitor_type_id == monitor_type_id)
    if is_active is not None:
        query = query.filter(models.MonitorPoint.is_active == is_active)
    return query.order_by(models.MonitorPoint.point_code).all()


@router.get("/points/{point_id}", response_model=schemas.MonitorPointResponse)
async def get_monitor_point(
    point_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    point = db.query(models.MonitorPoint).filter(models.MonitorPoint.id == point_id).first()
    if not point:
        raise HTTPException(status_code=404, detail="监测点不存在")
    return point


@router.post("/points", response_model=schemas.MonitorPointResponse)
async def create_monitor_point(
    point_data: schemas.MonitorPointCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("SAFETY_HEAD", "GEOLOGIST"))
):
    existing = db.query(models.MonitorPoint).filter(
        models.MonitorPoint.point_code == point_data.point_code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="监测点编码已存在")
    point = models.MonitorPoint(**point_data.model_dump())
    db.add(point)
    db.commit()
    db.refresh(point)
    return point


def _check_and_create_anomaly(
    db: Session,
    point: models.MonitorPoint,
    value: Decimal,
    record_time: datetime
):
    from app.routers.retest import create_auto_retest_plan

    warning_threshold = point.warning_threshold
    danger_threshold = point.danger_threshold

    if not warning_threshold and not danger_threshold:
        return None

    alert_level = None
    threshold = None
    trigger_type = None

    if danger_threshold and value >= danger_threshold:
        alert_level = models.AlertLevel.DANGER
        threshold = danger_threshold
        trigger_type = "DANGER_THRESHOLD"
    elif warning_threshold and value >= warning_threshold:
        alert_level = models.AlertLevel.WARNING
        threshold = warning_threshold
        trigger_type = "WARNING_THRESHOLD"

    if not alert_level:
        return None

    two_hours_ago = record_time - timedelta(hours=2)
    recent_data = db.query(models.MonitorData).filter(
        models.MonitorData.point_id == point.id,
        models.MonitorData.time >= two_hours_ago,
        models.MonitorData.time <= record_time
    ).order_by(models.MonitorData.time.desc()).limit(2).all()

    consecutive_count = 0
    for d in recent_data:
        if threshold and d.value >= threshold:
            consecutive_count += 1
        else:
            break

    became_critical = False
    if consecutive_count >= 2:
        alert_level = models.AlertLevel.CRITICAL
        trigger_type = "CONSECUTIVE_THRESHOLD"
        became_critical = True

    open_anomaly = db.query(models.AnomalyRecord).filter(
        models.AnomalyRecord.point_id == point.id,
        models.AnomalyRecord.status == "OPEN"
    ).first()

    anomaly = None
    if open_anomaly:
        old_level = open_anomaly.alert_level
        open_anomaly.consecutive_count = consecutive_count if consecutive_count > open_anomaly.consecutive_count else open_anomaly.consecutive_count
        open_anomaly.trigger_value = value
        if alert_level == models.AlertLevel.CRITICAL and open_anomaly.alert_level != models.AlertLevel.CRITICAL:
            open_anomaly.alert_level = models.AlertLevel.CRITICAL
            became_critical = True
        db.commit()
        db.refresh(open_anomaly)
        anomaly = open_anomaly
    else:
        anomaly = models.AnomalyRecord(
            point_id=point.id,
            alert_level=alert_level,
            trigger_type=trigger_type,
            trigger_value=value,
            threshold_value=threshold,
            consecutive_count=consecutive_count,
            start_time=record_time,
            status="OPEN"
        )
        db.add(anomaly)
        db.commit()
        db.refresh(anomaly)

    if became_critical and anomaly:
        create_auto_retest_plan(db, anomaly, point)

    return anomaly


@router.post("/data")
async def create_monitor_data(
    data: schemas.MonitorDataCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("DISPATCH", "GEOLOGIST"))
):
    point = db.query(models.MonitorPoint).filter(models.MonitorPoint.id == data.point_id).first()
    if not point:
        raise HTTPException(status_code=404, detail="监测点不存在")
    if not point.is_active:
        raise HTTPException(status_code=400, detail="监测点已停用")

    record_time = data.time or datetime.utcnow()
    monitor_data = models.MonitorData(
        time=record_time,
        point_id=data.point_id,
        value=data.value,
        recorded_by=current_user.id,
        remark=data.remark
    )
    db.add(monitor_data)

    anomaly = _check_and_create_anomaly(db, point, data.value, record_time)

    db.commit()
    db.refresh(monitor_data)

    result = {
        "data": monitor_data,
        "anomaly_generated": anomaly is not None,
    }
    if anomaly:
        result["anomaly"] = schemas.AnomalyRecordResponse.model_validate(anomaly).model_dump()
    return result


@router.post("/data/batch")
async def batch_create_monitor_data(
    batch_data: schemas.MonitorDataBatchCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("DISPATCH", "GEOLOGIST"))
):
    results = []
    for record in batch_data.records:
        point = db.query(models.MonitorPoint).filter(models.MonitorPoint.id == record.point_id).first()
        if not point or not point.is_active:
            continue

        record_time = record.time or datetime.utcnow()
        monitor_data = models.MonitorData(
            time=record_time,
            point_id=record.point_id,
            value=record.value,
            recorded_by=current_user.id,
            remark=record.remark
        )
        db.add(monitor_data)

        anomaly = _check_and_create_anomaly(db, point, record.value, record_time)
        results.append({
            "point_id": record.point_id,
            "success": True,
            "anomaly_generated": anomaly is not None
        })

    db.commit()
    return {"results": results, "total": len(results)}


@router.get("/data")
async def query_monitor_data(
    point_ids: Optional[str] = Query(None, description="监测点ID，逗号分隔"),
    start_time: datetime = Query(..., description="开始时间"),
    end_time: datetime = Query(..., description="结束时间"),
    bucket: Optional[str] = Query(None, description="时间聚合: 1m,5m,15m,1h,1d"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    point_id_list = [int(pid.strip()) for pid in point_ids.split(",")] if point_ids else None

    if bucket:
        bucket_map = {
            "1m": "1 minute",
            "5m": "5 minutes",
            "15m": "15 minutes",
            "1h": "1 hour",
            "1d": "1 day",
        }
        bucket_interval = bucket_map.get(bucket)
        if not bucket_interval:
            raise HTTPException(status_code=400, detail="不支持的聚合粒度")

        query = """
            SELECT
                time_bucket(:bucket, md.time) AS bucket_time,
                md.point_id,
                AVG(md.value) AS avg_value,
                MAX(md.value) AS max_value,
                MIN(md.value) AS min_value,
                COUNT(*) AS sample_count
            FROM monitor_data md
            WHERE md.time >= :start_time AND md.time <= :end_time
        """
        params = {"bucket": bucket_interval, "start_time": start_time, "end_time": end_time}

        if point_id_list:
            query += " AND md.point_id = ANY(:point_ids)"
            params["point_ids"] = point_id_list

        query += " GROUP BY bucket_time, md.point_id ORDER BY bucket_time, md.point_id"
        result = db.execute(query, params)
        rows = result.fetchall()

        data = {}
        for row in rows:
            pid = row[1]
            if pid not in data:
                data[pid] = []
            data[pid].append({
                "time": row[0],
                "point_id": pid,
                "avg_value": float(row[2]) if row[2] else None,
                "max_value": float(row[3]) if row[3] else None,
                "min_value": float(row[4]) if row[4] else None,
                "sample_count": row[5]
            })
        return {"data": data, "aggregated": True, "bucket": bucket}
    else:
        query = db.query(models.MonitorData).filter(
            models.MonitorData.time >= start_time,
            models.MonitorData.time <= end_time
        )
        if point_id_list:
            query = query.filter(models.MonitorData.point_id.in_(point_id_list))

        records = query.order_by(models.MonitorData.time).all()

        data = {}
        for r in records:
            pid = r.point_id
            if pid not in data:
                data[pid] = []
            data[pid].append({
                "time": r.time,
                "point_id": pid,
                "value": float(r.value),
                "recorded_by": r.recorded_by,
                "remark": r.remark
            })
        return {"data": data, "aggregated": False}


@router.get("/data/latest")
async def get_latest_monitor_data(
    point_ids: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    point_id_list = [int(pid.strip()) for pid in point_ids.split(",")] if point_ids else None

    query = """
        SELECT DISTINCT ON (md.point_id)
            md.point_id,
            md.time,
            md.value,
            md.recorded_by,
            md.remark
        FROM monitor_data md
    """
    params = {}
    if point_id_list:
        query += " WHERE md.point_id = ANY(:point_ids)"
        params["point_ids"] = point_id_list
    query += " ORDER BY md.point_id, md.time DESC"

    result = db.execute(query, params)
    rows = result.fetchall()

    data = {}
    for row in rows:
        pid = row[0]
        data[pid] = {
            "time": row[1],
            "point_id": pid,
            "value": float(row[2]),
            "recorded_by": row[3],
            "remark": row[4]
        }
    return {"data": data}


@router.get("/alerts/summary", response_model=schemas.AlertSummary)
async def get_alert_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    open_anomalies = db.query(models.AnomalyRecord).filter(
        models.AnomalyRecord.status == "OPEN"
    ).all()

    summary = schemas.AlertSummary()
    for a in open_anomalies:
        if a.alert_level == models.AlertLevel.WARNING:
            summary.warning_count += 1
        elif a.alert_level == models.AlertLevel.DANGER:
            summary.danger_count += 1
        elif a.alert_level == models.AlertLevel.CRITICAL:
            summary.critical_count += 1
        if not a.is_confirmed:
            summary.unconfirmed_count += 1
    return summary
