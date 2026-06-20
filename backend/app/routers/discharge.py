from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import get_current_active_user, require_roles
from app.routers.instruction import _has_active_stop_discharge

router = APIRouter(prefix="/api/discharge", tags=["排放计划"])


def _generate_plan_no(db: Session) -> str:
    now = datetime.now()
    prefix = f"DP{now.strftime('%Y%m%d')}"
    last = db.query(models.DischargePlan).filter(
        models.DischargePlan.plan_no.like(f"{prefix}%")
    ).order_by(models.DischargePlan.plan_no.desc()).first()
    seq = 1
    if last:
        try:
            seq = int(last.plan_no[-4:]) + 1
        except (ValueError, IndexError):
            seq = 1
    return f"{prefix}{seq:04d}"


@router.get("", response_model=List[schemas.DischargePlanResponse])
async def get_discharge_plans(
    status: Optional[models.DischargeStatus] = None,
    plan_date_from: Optional[date] = None,
    plan_date_to: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    query = db.query(models.DischargePlan)
    if status:
        query = query.filter(models.DischargePlan.status == status)
    if plan_date_from:
        query = query.filter(models.DischargePlan.plan_date >= plan_date_from)
    if plan_date_to:
        query = query.filter(models.DischargePlan.plan_date <= plan_date_to)
    return query.order_by(models.DischargePlan.plan_date.desc(), models.DischargePlan.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{plan_id}", response_model=schemas.DischargePlanResponse)
async def get_discharge_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    plan = db.query(models.DischargePlan).filter(models.DischargePlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="排放计划不存在")
    return plan


@router.post("", response_model=schemas.DischargePlanResponse)
async def create_discharge_plan(
    data: schemas.DischargePlanCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("DISPATCH", "SAFETY_HEAD"))
):
    has_active_stop, active_instructions = _has_active_stop_discharge(db)
    if has_active_stop:
        instruction_nos = ", ".join([i.instruction_no for i in active_instructions])
        raise HTTPException(
            status_code=400,
            detail=f"存在未解除的停排指令（{instruction_nos}），禁止新增排放计划"
        )

    plan_no = _generate_plan_no(db)
    plan = models.DischargePlan(
        plan_no=plan_no,
        **data.model_dump(),
        created_by=current_user.id,
        status=models.DischargeStatus.DRAFT
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.post("/{plan_id}/approve", response_model=schemas.DischargePlanResponse)
async def approve_discharge_plan(
    plan_id: int,
    data: schemas.DischargePlanApprove,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("SAFETY_HEAD"))
):
    plan = db.query(models.DischargePlan).filter(models.DischargePlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="排放计划不存在")
    if plan.status != models.DischargeStatus.DRAFT:
        raise HTTPException(status_code=400, detail="只有草稿状态可以审批")

    has_active_stop, active_instructions = _has_active_stop_discharge(db)
    if has_active_stop:
        instruction_nos = ", ".join([i.instruction_no for i in active_instructions])
        raise HTTPException(
            status_code=400,
            detail=f"存在未解除的停排指令（{instruction_nos}），禁止审批排放计划"
        )

    plan.status = data.status
    plan.approver_id = current_user.id
    if data.operator_id:
        plan.operator_id = data.operator_id
    db.commit()
    db.refresh(plan)
    return plan


@router.post("/{plan_id}/execute", response_model=schemas.DischargePlanResponse)
async def execute_discharge_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("DISPATCH"))
):
    plan = db.query(models.DischargePlan).filter(models.DischargePlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="排放计划不存在")
    if plan.status != models.DischargeStatus.APPROVED:
        raise HTTPException(status_code=400, detail="只有已审批状态可以执行")

    has_active_stop, active_instructions = _has_active_stop_discharge(db)
    if has_active_stop:
        instruction_nos = ", ".join([i.instruction_no for i in active_instructions])
        raise HTTPException(
            status_code=400,
            detail=f"存在未解除的停排指令（{instruction_nos}），禁止执行排放计划"
        )

    plan.status = models.DischargeStatus.EXECUTING
    plan.operator_id = current_user.id
    db.commit()
    db.refresh(plan)
    return plan


@router.post("/{plan_id}/complete", response_model=schemas.DischargePlanResponse)
async def complete_discharge_plan(
    plan_id: int,
    actual_volume: float,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("DISPATCH", "SAFETY_HEAD"))
):
    plan = db.query(models.DischargePlan).filter(models.DischargePlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="排放计划不存在")
    if plan.status != models.DischargeStatus.EXECUTING:
        raise HTTPException(status_code=400, detail="只有执行中状态可以完成")

    plan.status = models.DischargeStatus.COMPLETED
    plan.actual_volume = actual_volume
    db.commit()
    db.refresh(plan)
    return plan


@router.post("/{plan_id}/cancel", response_model=schemas.DischargePlanResponse)
async def cancel_discharge_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("SAFETY_HEAD"))
):
    plan = db.query(models.DischargePlan).filter(models.DischargePlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="排放计划不存在")
    if plan.status in [models.DischargeStatus.COMPLETED, models.DischargeStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="当前状态不可取消")

    plan.status = models.DischargeStatus.CANCELLED
    db.commit()
    db.refresh(plan)
    return plan
