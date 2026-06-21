from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from app.models import AlertLevel, InstructionType, InstructionStatus, DischargeStatus, RetestStatus


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class RoleBase(BaseModel):
    role_code: str
    role_name: str
    description: Optional[str] = None


class RoleResponse(RoleBase):
    id: int

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    username: str
    real_name: str
    phone: Optional[str] = None
    email: Optional[str] = None


class UserCreate(UserBase):
    password: str
    role_id: int


class UserResponse(UserBase):
    id: int
    role_id: Optional[int] = None
    role: Optional[RoleResponse] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class MonitorTypeBase(BaseModel):
    type_code: str
    type_name: str
    unit: str
    default_warning_threshold: Optional[Decimal] = None
    default_danger_threshold: Optional[Decimal] = None
    description: Optional[str] = None


class MonitorTypeResponse(MonitorTypeBase):
    id: int

    class Config:
        from_attributes = True


class MonitorPointBase(BaseModel):
    point_code: str
    point_name: str
    monitor_type_id: int
    location: Optional[str] = None
    warning_threshold: Optional[Decimal] = None
    danger_threshold: Optional[Decimal] = None
    is_active: bool = True


class MonitorPointCreate(MonitorPointBase):
    pass


class MonitorPointResponse(MonitorPointBase):
    id: int
    monitor_type: Optional[MonitorTypeResponse] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MonitorDataCreate(BaseModel):
    point_id: int
    value: Decimal
    time: Optional[datetime] = None
    remark: Optional[str] = None


class MonitorDataBatchCreate(BaseModel):
    records: List[MonitorDataCreate]


class MonitorDataResponse(BaseModel):
    time: datetime
    point_id: int
    value: Decimal
    recorded_by: Optional[int] = None
    remark: Optional[str] = None

    class Config:
        from_attributes = True


class MonitorDataQuery(BaseModel):
    point_ids: Optional[List[int]] = None
    monitor_type_ids: Optional[List[int]] = None
    start_time: datetime
    end_time: datetime
    bucket: Optional[str] = None


class AnomalyRecordBase(BaseModel):
    point_id: int
    alert_level: AlertLevel = AlertLevel.WARNING
    trigger_type: str
    trigger_value: Decimal
    threshold_value: Decimal
    consecutive_count: int = 1
    start_time: datetime
    end_time: Optional[datetime] = None


class AnomalyConfirm(BaseModel):
    confirmation_note: str
    is_confirmed: bool = True


class AnomalyRecordResponse(AnomalyRecordBase):
    id: int
    is_confirmed: bool = False
    confirmed_by: Optional[int] = None
    confirmed_at: Optional[datetime] = None
    confirmation_note: Optional[str] = None
    status: str = "OPEN"
    point: Optional[MonitorPointResponse] = None
    confirmer: Optional[UserResponse] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DisposalInstructionBase(BaseModel):
    instruction_type: InstructionType
    title: str
    content: str
    related_anomaly_ids: Optional[List[int]] = None
    effective_from: datetime
    effective_to: Optional[datetime] = None


class DisposalInstructionCreate(DisposalInstructionBase):
    pass


class DisposalInstructionIssue(BaseModel):
    pass


class DisposalInstructionLift(BaseModel):
    lift_reason: str


class DisposalInstructionResponse(DisposalInstructionBase):
    id: int
    instruction_no: str
    status: InstructionStatus = InstructionStatus.DRAFT
    issued_by: Optional[int] = None
    issued_at: Optional[datetime] = None
    lifted_by: Optional[int] = None
    lifted_at: Optional[datetime] = None
    lift_reason: Optional[str] = None
    issuer: Optional[UserResponse] = None
    lifter: Optional[UserResponse] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DischargePlanBase(BaseModel):
    plan_date: date
    planned_volume: Decimal
    discharge_location: Optional[str] = None
    remark: Optional[str] = None


class DischargePlanCreate(DischargePlanBase):
    pass


class DischargePlanApprove(BaseModel):
    status: DischargeStatus = DischargeStatus.APPROVED
    operator_id: Optional[int] = None


class DischargePlanResponse(DischargePlanBase):
    id: int
    plan_no: str
    actual_volume: Optional[Decimal] = None
    operator_id: Optional[int] = None
    approver_id: Optional[int] = None
    status: DischargeStatus = DischargeStatus.DRAFT
    created_by: Optional[int] = None
    creator: Optional[UserResponse] = None
    operator: Optional[UserResponse] = None
    approver: Optional[UserResponse] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DisposalRecordBase(BaseModel):
    instruction_id: Optional[int] = None
    anomaly_id: Optional[int] = None
    action_type: str
    action_content: str
    snapshot_start_time: datetime
    snapshot_end_time: datetime
    snapshot_point_ids: Optional[List[int]] = None
    result: Optional[str] = None


class DisposalRecordCreate(DisposalRecordBase):
    pass


class DisposalRecordResponse(DisposalRecordBase):
    id: int
    handler_id: int
    handler: Optional[UserResponse] = None
    instruction: Optional[DisposalInstructionResponse] = None
    anomaly: Optional[AnomalyRecordResponse] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AlertSummary(BaseModel):
    warning_count: int = 0
    danger_count: int = 0
    critical_count: int = 0
    unconfirmed_count: int = 0


class StopDischargeCheck(BaseModel):
    has_active_stop: bool
    active_instructions: List[DisposalInstructionResponse] = []


class RetestPlanBase(BaseModel):
    point_id: int
    anomaly_id: Optional[int] = None
    responsible_engineer_id: int
    retest_reason: str
    trigger_value: Optional[Decimal] = None
    threshold_value: Optional[Decimal] = None
    consecutive_count: int = 2
    planned_retest_time: datetime


class RetestPlanCreate(RetestPlanBase):
    pass


class RetestPlanUpdate(BaseModel):
    responsible_engineer_id: Optional[int] = None
    planned_retest_time: Optional[datetime] = None
    retest_reason: Optional[str] = None


class RetestPlanComplete(BaseModel):
    retest_value: Decimal
    retest_note: Optional[str] = None


class RetestPlanResponse(RetestPlanBase):
    id: int
    plan_no: str
    actual_retest_time: Optional[datetime] = None
    retest_value: Optional[Decimal] = None
    retest_note: Optional[str] = None
    status: RetestStatus = RetestStatus.PENDING
    completed_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    point: Optional[MonitorPointResponse] = None
    anomaly: Optional[AnomalyRecordResponse] = None
    responsible_engineer: Optional[UserResponse] = None
    completer: Optional[UserResponse] = None

    class Config:
        from_attributes = True


class RetestDashboardSummary(BaseModel):
    pending_count: int = 0
    in_progress_count: int = 0
    overdue_count: int = 0
    total_count: int = 0
