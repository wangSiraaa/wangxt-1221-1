from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import get_current_active_user, require_roles

router = APIRouter(prefix="/api/instruction", tags=["处置指令"])


def _generate_instruction_no(db: Session) -> str:
    now = datetime.now()
    prefix = f"INS{now.strftime('%Y%m%d')}"
    last = db.query(models.DisposalInstruction).filter(
        models.DisposalInstruction.instruction_no.like(f"{prefix}%")
    ).order_by(models.DisposalInstruction.instruction_no.desc()).first()
    seq = 1
    if last:
        try:
            seq = int(last.instruction_no[-4:]) + 1
        except (ValueError, IndexError):
            seq = 1
    return f"{prefix}{seq:04d}"


def _has_active_stop_discharge(db: Session) -> tuple:
    now = datetime.utcnow()
    active = db.query(models.DisposalInstruction).filter(
        models.DisposalInstruction.instruction_type == models.InstructionType.STOP_DISCHARGE,
        models.DisposalInstruction.status == models.InstructionStatus.ISSUED,
        models.DisposalInstruction.effective_from <= now,
        (models.DisposalInstruction.effective_to.is_(None) | (models.DisposalInstruction.effective_to >= now))
    ).all()
    return (len(active) > 0, active)


@router.get("/stop-check", response_model=schemas.StopDischargeCheck)
async def check_stop_discharge(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    has_active, instructions = _has_active_stop_discharge(db)
    return schemas.StopDischargeCheck(
        has_active_stop=has_active,
        active_instructions=[schemas.DisposalInstructionResponse.model_validate(i) for i in instructions]
    )


@router.get("", response_model=List[schemas.DisposalInstructionResponse])
async def get_instructions(
    instruction_type: Optional[models.InstructionType] = None,
    status: Optional[models.InstructionStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    query = db.query(models.DisposalInstruction)
    if instruction_type:
        query = query.filter(models.DisposalInstruction.instruction_type == instruction_type)
    if status:
        query = query.filter(models.DisposalInstruction.status == status)
    return query.order_by(models.DisposalInstruction.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{instruction_id}", response_model=schemas.DisposalInstructionResponse)
async def get_instruction(
    instruction_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    instruction = db.query(models.DisposalInstruction).filter(
        models.DisposalInstruction.id == instruction_id
    ).first()
    if not instruction:
        raise HTTPException(status_code=404, detail="指令不存在")
    return instruction


@router.post("", response_model=schemas.DisposalInstructionResponse)
async def create_instruction(
    data: schemas.DisposalInstructionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("SAFETY_HEAD"))
):
    instruction_no = _generate_instruction_no(db)
    instruction = models.DisposalInstruction(
        instruction_no=instruction_no,
        **data.model_dump(),
        issued_by=current_user.id,
        status=models.InstructionStatus.DRAFT
    )
    db.add(instruction)
    db.commit()
    db.refresh(instruction)
    return instruction


@router.post("/{instruction_id}/issue", response_model=schemas.DisposalInstructionResponse)
async def issue_instruction(
    instruction_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("SAFETY_HEAD"))
):
    instruction = db.query(models.DisposalInstruction).filter(
        models.DisposalInstruction.id == instruction_id
    ).first()
    if not instruction:
        raise HTTPException(status_code=404, detail="指令不存在")
    if instruction.status not in [models.InstructionStatus.DRAFT, models.InstructionStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="只有草稿或已取消状态可以签发")

    instruction.status = models.InstructionStatus.ISSUED
    instruction.issued_at = datetime.utcnow()
    db.commit()
    db.refresh(instruction)

    return instruction


@router.post("/{instruction_id}/lift", response_model=schemas.DisposalInstructionResponse)
async def lift_instruction(
    instruction_id: int,
    data: schemas.DisposalInstructionLift,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("SAFETY_HEAD"))
):
    instruction = db.query(models.DisposalInstruction).filter(
        models.DisposalInstruction.id == instruction_id
    ).first()
    if not instruction:
        raise HTTPException(status_code=404, detail="指令不存在")
    if instruction.status != models.InstructionStatus.ISSUED:
        raise HTTPException(status_code=400, detail="只有已签发状态可以解除")

    instruction.status = models.InstructionStatus.LIFTED
    instruction.lifted_by = current_user.id
    instruction.lifted_at = datetime.utcnow()
    instruction.lift_reason = data.lift_reason
    db.commit()
    db.refresh(instruction)
    return instruction


@router.post("/{instruction_id}/cancel", response_model=schemas.DisposalInstructionResponse)
async def cancel_instruction(
    instruction_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("SAFETY_HEAD"))
):
    instruction = db.query(models.DisposalInstruction).filter(
        models.DisposalInstruction.id == instruction_id
    ).first()
    if not instruction:
        raise HTTPException(status_code=404, detail="指令不存在")
    if instruction.status != models.InstructionStatus.DRAFT:
        raise HTTPException(status_code=400, detail="只有草稿状态可以取消")

    instruction.status = models.InstructionStatus.CANCELLED
    db.commit()
    db.refresh(instruction)
    return instruction
