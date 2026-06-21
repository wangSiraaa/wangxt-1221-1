-- ========================================
-- 矿山尾矿库安全监测系统数据库初始化脚本
-- PostgreSQL + TimescaleDB
-- ========================================

-- 启用 TimescaleDB 扩展
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ========================================
-- 一、用户与权限（普通关系表）
-- ========================================

-- 角色表
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    role_code VARCHAR(50) UNIQUE NOT NULL,
    role_name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    real_name VARCHAR(100) NOT NULL,
    role_id INTEGER REFERENCES roles(id),
    phone VARCHAR(20),
    email VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 初始化角色数据
INSERT INTO roles (role_code, role_name, description) VALUES
    ('DISPATCH', '值班调度', '负责录入监测数据、查看监测曲线'),
    ('GEOLOGIST', '地测工程师', '负责确认异常趋势、分析数据'),
    ('SAFETY_HEAD', '安监负责人', '负责签发降级/停排指令、审批处置')
ON CONFLICT (role_code) DO NOTHING;

-- 初始化用户（密码均为 123456，实际部署时请修改）
-- 密码 hash 使用 bcrypt 生成，这里预置演示账号
INSERT INTO users (username, password_hash, real_name, role_id, phone) VALUES
    ('dispatch', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewYGy0kGHbY0VdPi', '张调度', 1, '13800138001'),
    ('geologist', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewYGy0kGHbY0VdPi', '李工程师', 2, '13800138002'),
    ('safety', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewYGy0kGHbY0VdPi', '王主任', 3, '13800138003')
ON CONFLICT (username) DO NOTHING;

-- ========================================
-- 二、监测点配置（普通关系表）
-- ========================================

-- 监测类型字典
CREATE TABLE IF NOT EXISTS monitor_types (
    id SERIAL PRIMARY KEY,
    type_code VARCHAR(50) UNIQUE NOT NULL,
    type_name VARCHAR(100) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    default_warning_threshold NUMERIC(15, 4),
    default_danger_threshold NUMERIC(15, 4),
    description TEXT
);

INSERT INTO monitor_types (type_code, type_name, unit, default_warning_threshold, default_danger_threshold, description) VALUES
    ('SEEPAGE_PRESSURE', '渗压', 'kPa', 80.0, 120.0, '尾矿库渗压监测，单位千帕'),
    ('DISPLACEMENT', '位移', 'mm', 50.0, 100.0, '坝体位移监测，单位毫米'),
    ('RAINFALL', '降雨', 'mm', 100.0, 200.0, '降雨量监测，单位毫米（24小时累计）')
ON CONFLICT (type_code) DO NOTHING;

-- 监测点表
CREATE TABLE IF NOT EXISTS monitor_points (
    id SERIAL PRIMARY KEY,
    point_code VARCHAR(50) UNIQUE NOT NULL,
    point_name VARCHAR(100) NOT NULL,
    monitor_type_id INTEGER REFERENCES monitor_types(id),
    location VARCHAR(200),
    warning_threshold NUMERIC(15, 4),
    danger_threshold NUMERIC(15, 4),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO monitor_points (point_code, point_name, monitor_type_id, location, warning_threshold, danger_threshold) VALUES
    ('SP-001', '1号渗压监测点', 1, '初期坝上游坡', 80.0, 120.0),
    ('SP-002', '2号渗压监测点', 1, '堆积坝中段', 85.0, 130.0),
    ('SP-003', '3号渗压监测点', 1, '下游坡脚', 75.0, 110.0),
    ('DP-001', '1号位移监测点', 2, '坝顶A点', 50.0, 100.0),
    ('DP-002', '2号位移监测点', 2, '坝顶B点', 50.0, 100.0),
    ('DP-003', '3号位移监测点', 2, '坝肩C点', 45.0, 90.0),
    ('RF-001', '库区气象站', 3, '尾矿库办公区', 100.0, 200.0)
ON CONFLICT (point_code) DO NOTHING;

-- ========================================
-- 三、监测时序数据（TimescaleDB 超表）
-- ========================================

-- 监测数据表（时序数据）
CREATE TABLE IF NOT EXISTS monitor_data (
    time TIMESTAMPTZ NOT NULL,
    point_id INTEGER NOT NULL REFERENCES monitor_points(id),
    value NUMERIC(15, 4) NOT NULL,
    recorded_by INTEGER REFERENCES users(id),
    remark TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 转换为 TimescaleDB 超表
SELECT create_hypertable('monitor_data', 'time', if_not_exists => TRUE);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_monitor_data_point_id ON monitor_data (point_id, time DESC);

-- ========================================
-- 四、异常与预警（普通关系表）
-- ========================================

-- 预警级别
CREATE TYPE alert_level AS ENUM ('NORMAL', 'WARNING', 'DANGER', 'CRITICAL');

-- 异常记录表
CREATE TABLE IF NOT EXISTS anomaly_records (
    id SERIAL PRIMARY KEY,
    point_id INTEGER NOT NULL REFERENCES monitor_points(id),
    alert_level alert_level NOT NULL DEFAULT 'WARNING',
    trigger_type VARCHAR(50) NOT NULL,
    trigger_value NUMERIC(15, 4) NOT NULL,
    threshold_value NUMERIC(15, 4) NOT NULL,
    consecutive_count INTEGER DEFAULT 1,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    is_confirmed BOOLEAN DEFAULT FALSE,
    confirmed_by INTEGER REFERENCES users(id),
    confirmed_at TIMESTAMP,
    confirmation_note TEXT,
    status VARCHAR(20) DEFAULT 'OPEN',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- 五、处置指令（普通关系表）
-- ========================================

-- 指令类型
CREATE TYPE instruction_type AS ENUM ('DOWNGRADE', 'STOP_DISCHARGE');

-- 指令状态
CREATE TYPE instruction_status AS ENUM ('DRAFT', 'ISSUED', 'EXECUTING', 'LIFTED', 'CANCELLED');

-- 处置指令表
CREATE TABLE IF NOT EXISTS disposal_instructions (
    id SERIAL PRIMARY KEY,
    instruction_no VARCHAR(50) UNIQUE NOT NULL,
    instruction_type instruction_type NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    related_anomaly_ids INTEGER[],
    issued_by INTEGER NOT NULL REFERENCES users(id),
    issued_at TIMESTAMP,
    effective_from TIMESTAMPTZ NOT NULL,
    effective_to TIMESTAMPTZ,
    status instruction_status DEFAULT 'DRAFT',
    lifted_by INTEGER REFERENCES users(id),
    lifted_at TIMESTAMP,
    lift_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- 六、排放计划（普通关系表）
-- ========================================

-- 排放计划状态
CREATE TYPE discharge_status AS ENUM ('DRAFT', 'APPROVED', 'EXECUTING', 'COMPLETED', 'CANCELLED', 'SUSPENDED');

-- 排放计划表
CREATE TABLE IF NOT EXISTS discharge_plans (
    id SERIAL PRIMARY KEY,
    plan_no VARCHAR(50) UNIQUE NOT NULL,
    plan_date DATE NOT NULL,
    planned_volume NUMERIC(15, 2) NOT NULL,
    actual_volume NUMERIC(15, 2),
    discharge_location VARCHAR(200),
    operator_id INTEGER REFERENCES users(id),
    approver_id INTEGER REFERENCES users(id),
    status discharge_status DEFAULT 'DRAFT',
    remark TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- 七、处置记录（普通关系表，可回看数据曲线）
-- ========================================

-- 处置记录表
CREATE TABLE IF NOT EXISTS disposal_records (
    id SERIAL PRIMARY KEY,
    instruction_id INTEGER REFERENCES disposal_instructions(id),
    anomaly_id INTEGER REFERENCES anomaly_records(id),
    handler_id INTEGER NOT NULL REFERENCES users(id),
    action_type VARCHAR(50) NOT NULL,
    action_content TEXT NOT NULL,
    snapshot_start_time TIMESTAMPTZ NOT NULL,
    snapshot_end_time TIMESTAMPTZ NOT NULL,
    snapshot_point_ids INTEGER[],
    result TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_anomaly_records_status ON anomaly_records(status);
CREATE INDEX IF NOT EXISTS idx_anomaly_records_point_time ON anomaly_records(point_id, start_time DESC);
CREATE INDEX IF NOT EXISTS idx_instructions_status ON disposal_instructions(status);
CREATE INDEX IF NOT EXISTS idx_discharge_plans_date ON discharge_plans(plan_date DESC);
CREATE INDEX IF NOT EXISTS idx_disposal_records_instruction ON disposal_records(instruction_id);

-- ========================================
-- 八、复测计划（普通关系表）
-- ========================================

-- 复测计划状态
CREATE TYPE retest_status AS ENUM ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED');

-- 复测计划表
CREATE TABLE IF NOT EXISTS retest_plans (
    id SERIAL PRIMARY KEY,
    plan_no VARCHAR(50) UNIQUE NOT NULL,
    point_id INTEGER NOT NULL REFERENCES monitor_points(id),
    anomaly_id INTEGER REFERENCES anomaly_records(id),
    responsible_engineer_id INTEGER NOT NULL REFERENCES users(id),
    retest_reason TEXT NOT NULL,
    trigger_value NUMERIC(15, 4),
    threshold_value NUMERIC(15, 4),
    consecutive_count INTEGER DEFAULT 2,
    planned_retest_time TIMESTAMPTZ NOT NULL,
    actual_retest_time TIMESTAMPTZ,
    retest_value NUMERIC(15, 4),
    retest_note TEXT,
    status retest_status DEFAULT 'PENDING',
    completed_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_retest_plans_status ON retest_plans(status);
CREATE INDEX IF NOT EXISTS idx_retest_plans_engineer ON retest_plans(responsible_engineer_id);
CREATE INDEX IF NOT EXISTS idx_retest_plans_planned_time ON retest_plans(planned_retest_time DESC);
