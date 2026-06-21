from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Boolean, ForeignKey, Numeric, ARRAY, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class AlertLevel(str, enum.Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    DANGER = "DANGER"
    CRITICAL = "CRITICAL"


class InstructionType(str, enum.Enum):
    DOWNGRADE = "DOWNGRADE"
    STOP_DISCHARGE = "STOP_DISCHARGE"


class InstructionStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    EXECUTING = "EXECUTING"
    LIFTED = "LIFTED"
    CANCELLED = "CANCELLED"


class DischargeStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    SUSPENDED = "SUSPENDED"


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    role_code = Column(String(50), unique=True, nullable=False)
    role_name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    real_name = Column(String(100), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"))
    phone = Column(String(20))
    email = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    role = relationship("Role")


class MonitorType(Base):
    __tablename__ = "monitor_types"

    id = Column(Integer, primary_key=True)
    type_code = Column(String(50), unique=True, nullable=False)
    type_name = Column(String(100), nullable=False)
    unit = Column(String(20), nullable=False)
    default_warning_threshold = Column(Numeric(15, 4))
    default_danger_threshold = Column(Numeric(15, 4))
    description = Column(Text)


class MonitorPoint(Base):
    __tablename__ = "monitor_points"

    id = Column(Integer, primary_key=True)
    point_code = Column(String(50), unique=True, nullable=False)
    point_name = Column(String(100), nullable=False)
    monitor_type_id = Column(Integer, ForeignKey("monitor_types.id"))
    location = Column(String(200))
    warning_threshold = Column(Numeric(15, 4))
    danger_threshold = Column(Numeric(15, 4))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    monitor_type = relationship("MonitorType")


class MonitorData(Base):
    __tablename__ = "monitor_data"

    time = Column(DateTime(timezone=True), primary_key=True)
    point_id = Column(Integer, ForeignKey("monitor_points.id"), primary_key=True)
    value = Column(Numeric(15, 4), nullable=False)
    recorded_by = Column(Integer, ForeignKey("users.id"))
    remark = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AnomalyRecord(Base):
    __tablename__ = "anomaly_records"

    id = Column(Integer, primary_key=True)
    point_id = Column(Integer, ForeignKey("monitor_points.id"), nullable=False)
    alert_level = Column(Enum(AlertLevel), nullable=False, default=AlertLevel.WARNING)
    trigger_type = Column(String(50), nullable=False)
    trigger_value = Column(Numeric(15, 4), nullable=False)
    threshold_value = Column(Numeric(15, 4), nullable=False)
    consecutive_count = Column(Integer, default=1)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True))
    is_confirmed = Column(Boolean, default=False)
    confirmed_by = Column(Integer, ForeignKey("users.id"))
    confirmed_at = Column(DateTime(timezone=True))
    confirmation_note = Column(Text)
    status = Column(String(20), default="OPEN")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    point = relationship("MonitorPoint")
    confirmer = relationship("User", foreign_keys=[confirmed_by])


class DisposalInstruction(Base):
    __tablename__ = "disposal_instructions"

    id = Column(Integer, primary_key=True)
    instruction_no = Column(String(50), unique=True, nullable=False)
    instruction_type = Column(Enum(InstructionType), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    related_anomaly_ids = Column(ARRAY(Integer))
    issued_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    issued_at = Column(DateTime(timezone=True))
    effective_from = Column(DateTime(timezone=True), nullable=False)
    effective_to = Column(DateTime(timezone=True))
    status = Column(Enum(InstructionStatus), default=InstructionStatus.DRAFT)
    lifted_by = Column(Integer, ForeignKey("users.id"))
    lifted_at = Column(DateTime(timezone=True))
    lift_reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    issuer = relationship("User", foreign_keys=[issued_by])
    lifter = relationship("User", foreign_keys=[lifted_by])


class DischargePlan(Base):
    __tablename__ = "discharge_plans"

    id = Column(Integer, primary_key=True)
    plan_no = Column(String(50), unique=True, nullable=False)
    plan_date = Column(Date, nullable=False)
    planned_volume = Column(Numeric(15, 2), nullable=False)
    actual_volume = Column(Numeric(15, 2))
    discharge_location = Column(String(200))
    operator_id = Column(Integer, ForeignKey("users.id"))
    approver_id = Column(Integer, ForeignKey("users.id"))
    status = Column(Enum(DischargeStatus), default=DischargeStatus.DRAFT)
    remark = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    creator = relationship("User", foreign_keys=[created_by])
    operator = relationship("User", foreign_keys=[operator_id])
    approver = relationship("User", foreign_keys=[approver_id])


class DisposalRecord(Base):
    __tablename__ = "disposal_records"

    id = Column(Integer, primary_key=True)
    instruction_id = Column(Integer, ForeignKey("disposal_instructions.id"))
    anomaly_id = Column(Integer, ForeignKey("anomaly_records.id"))
    handler_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action_type = Column(String(50), nullable=False)
    action_content = Column(Text, nullable=False)
    snapshot_start_time = Column(DateTime(timezone=True), nullable=False)
    snapshot_end_time = Column(DateTime(timezone=True), nullable=False)
    snapshot_point_ids = Column(ARRAY(Integer))
    result = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    handler = relationship("User", foreign_keys=[handler_id])
    instruction = relationship("DisposalInstruction")
    anomaly = relationship("AnomalyRecord")


class RetestStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class RetestPlan(Base):
    __tablename__ = "retest_plans"

    id = Column(Integer, primary_key=True)
    plan_no = Column(String(50), unique=True, nullable=False)
    point_id = Column(Integer, ForeignKey("monitor_points.id"), nullable=False)
    anomaly_id = Column(Integer, ForeignKey("anomaly_records.id"))
    responsible_engineer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    retest_reason = Column(Text, nullable=False)
    trigger_value = Column(Numeric(15, 4))
    threshold_value = Column(Numeric(15, 4))
    consecutive_count = Column(Integer, default=2)
    planned_retest_time = Column(DateTime(timezone=True), nullable=False)
    actual_retest_time = Column(DateTime(timezone=True))
    retest_value = Column(Numeric(15, 4))
    retest_note = Column(Text)
    status = Column(Enum(RetestStatus), default=RetestStatus.PENDING)
    completed_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    point = relationship("MonitorPoint", foreign_keys=[point_id])
    anomaly = relationship("AnomalyRecord", foreign_keys=[anomaly_id])
    responsible_engineer = relationship("User", foreign_keys=[responsible_engineer_id])
    completer = relationship("User", foreign_keys=[completed_by])
