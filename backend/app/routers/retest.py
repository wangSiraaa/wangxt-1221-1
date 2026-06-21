from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import get_current_active_user, require_roles

router = APIRouter(prefix="/api/retest", tags=["复测计划"])


def _generate_plan_no(db: Session) -> str:
    now = datetime.now()
    prefix = f"RET{now.strftime('%Y%m%d')}"
    last = db.query(models.RetestPlan).filter(
        models.RetestPlan.plan_no.like(f"{prefix}%")
    ).order_by(models.RetestPlan.plan_no.desc()).first()
    seq = 1
    if last:
        try:
            seq = int(last.plan_no[-4:]) + 1
        except (ValueError, IndexError):
            seq = 1
    return f"{prefix}{seq:04d}"


def _find_geologist_id(db: Session) -> Optional[int]:
    geologist = db.query(models.User).join(
        models.Role, models.User.role_id == models.Role.id
    ).filter(
        models.Role.role_code == "GEOLOGIST",
        models.User.is_active == True
    ).first()
    return geologist.id if geologist else None


def create_auto_retest_plan(
    db: Session,
    anomaly: models.AnomalyRecord,
    point: models.MonitorPoint
) -> Optional[models.RetestPlan]:
    existing = db.query(models.RetestPlan).filter(
        models.RetestPlan.anomaly_id == anomaly.id,
        models.RetestPlan.status.in_([
            models.RetestStatus.PENDING,
            models.RetestStatus.IN_PROGRESS
        ])
    ).first()
    if existing:
        return existing

    engineer_id = _find_geologist_id(db)
    if not engineer_id:
        return None

    planned_time = datetime.utcnow() + timedelta(hours=4)

    plan = models.RetestPlan(
        plan_no=_generate_plan_no(db),
        point_id=point.id,
        anomaly_id=anomaly.id,
        responsible_engineer_id=engineer_id,
        retest_reason=f"连续{anomaly.consecutive_count}次超阈值，需现场复测确认",
        trigger_value=anomaly.trigger_value,
        threshold_value=anomaly.threshold_value,
        consecutive_count=anomaly.consecutive_count,
        planned_retest_time=planned_time,
        status=models.RetestStatus.PENDING
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.get("/dashboard/summary", response_model=schemas.RetestDashboardSummary)
async def get_retest_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    now = datetime.utcnow()
    all_active = db.query(models.RetestPlan).filter(
        models.RetestPlan.status.in_([
            models.RetestStatus.PENDING,
            models.RetestStatus.IN_PROGRESS
        ])
    ).all()

    summary = schemas.RetestDashboardSummary()
    summary.total_count = len(all_active)

    for p in all_active:
        if p.status == models.RetestStatus.PENDING:
            summary.pending_count += 1
        elif p.status == models.RetestStatus.IN_PROGRESS:
            summary.in_progress_count += 1
        if p.planned_retest_time < now:
            summary.overdue_count += 1

    return summary


@router.get("/plans", response_model=List[schemas.RetestPlanResponse])
async def get_retest_plans(
    status: Optional[models.RetestStatus] = None,
    point_id: Optional[int] = None,
    responsible_engineer_id: Optional[int] = None,
    only_active: Optional[bool] = Query(False, description="只显示待处理和进行中"),
    include_overdue: Optional[bool] = Query(None, description="是否只显示逾期"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    query = db.query(models.RetestPlan)

    if only_active:
        query = query.filter(models.RetestPlan.status.in_([
            models.RetestStatus.PENDING,
            models.RetestStatus.IN_PROGRESS
        ]))
    elif status:
        query = query.filter(models.RetestPlan.status == status)

    if point_id:
        query = query.filter(models.RetestPlan.point_id == point_id)
    if responsible_engineer_id:
        query = query.filter(models.RetestPlan.responsible_engineer_id == responsible_engineer_id)
    if include_overdue is not None:
        now = datetime.utcnow()
        if include_overdue:
            query = query.filter(models.RetestPlan.planned_retest_time < now)
        else:
            query = query.filter(models.RetestPlan.planned_retest_time >= now)

    return query.order_by(models.RetestPlan.planned_retest_time.asc()).offset(skip).limit(limit).all()


@router.get("/plans/{plan_id}", response_model=schemas.RetestPlanResponse)
async def get_retest_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    plan = db.query(models.RetestPlan).filter(models.RetestPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="复测计划不存在")
    return plan


@router.post("", response_model=schemas.RetestPlanResponse)
async def create_retest_plan(
    data: schemas.RetestPlanCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("SAFETY_HEAD", "GEOLOGIST"))
):
    point = db.query(models.MonitorPoint).filter(models.MonitorPoint.id == data.point_id).first()
    if not point:
        raise HTTPException(status_code=404, detail="监测点不存在")

    engineer = db.query(models.User).filter(models.User.id == data.responsible_engineer_id).first()
    if not engineer:
        raise HTTPException(status_code=404, detail="责任工程师不存在")

    plan_no = _generate_plan_no(db)
    plan = models.RetestPlan(
        plan_no=plan_no,
        **data.model_dump()
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.put("/plans/{plan_id}", response_model=schemas.RetestPlanResponse)
async def update_retest_plan(
    plan_id: int,
    data: schemas.RetestPlanUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("SAFETY_HEAD", "GEOLOGIST"))
):
    plan = db.query(models.RetestPlan).filter(models.RetestPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="复测计划不存在")
    if plan.status not in [models.RetestStatus.PENDING, models.RetestStatus.IN_PROGRESS]:
        raise HTTPException(status_code=400, detail="该计划已完成或取消，无法修改")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(plan, key, value)
    db.commit()
    db.refresh(plan)
    return plan


@router.post("/plans/{plan_id}/start", response_model=schemas.RetestPlanResponse)
async def start_retest(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("DISPATCH", "GEOLOGIST"))
):
    plan = db.query(models.RetestPlan).filter(models.RetestPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="复测计划不存在")
    if plan.status != models.RetestStatus.PENDING:
        raise HTTPException(status_code=400, detail="只有待复测状态可以开始")

    plan.status = models.RetestStatus.IN_PROGRESS
    db.commit()
    db.refresh(plan)
    return plan


@router.post("/plans/{plan_id}/complete", response_model=schemas.RetestPlanResponse)
async def complete_retest(
    plan_id: int,
    data: schemas.RetestPlanComplete,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("DISPATCH", "GEOLOGIST"))
):
    plan = db.query(models.RetestPlan).filter(models.RetestPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="复测计划不存在")
    if plan.status not in [models.RetestStatus.PENDING, models.RetestStatus.IN_PROGRESS]:
        raise HTTPException(status_code=400, detail="该计划已完成或取消，无法复测")

    plan.status = models.RetestStatus.COMPLETED
    plan.actual_retest_time = datetime.utcnow()
    plan.retest_value = data.retest_value
    plan.retest_note = data.retest_note
    plan.completed_by = current_user.id
    db.commit()
    db.refresh(plan)
    return plan


@router.post("/plans/{plan_id}/cancel", response_model=schemas.RetestPlanResponse)
async def cancel_retest(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("SAFETY_HEAD"))
):
    plan = db.query(models.RetestPlan).filter(models.RetestPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="复测计划不存在")
    if plan.status not in [models.RetestStatus.PENDING, models.RetestStatus.IN_PROGRESS]:
        raise HTTPException(status_code=400, detail="该计划已完成或取消")

    plan.status = models.RetestStatus.CANCELLED
    db.commit()
    db.refresh(plan)
    return plan
