# 矿山尾矿库安全监测系统

## 系统概述

本系统面向矿山尾矿库安全监测场景，覆盖**值班调度**、**地测工程师**、**安监负责人**三类角色，实现渗压、位移、降雨三类监测数据的录入、异常趋势确认、处置指令签发、排放计划管控和处置记录回溯全流程。

## 核心业务规则

1. **三类监测对象**：渗压（kPa）、位移（mm）、降雨（mm/24h），每个监测点独立配置预警阈值和危险阈值。
2. **连续两次超阈值升级**：同一监测点在短时间内（2小时窗口）连续两次超过阈值，不做普通预警，直接升级为 **严重（CRITICAL）** 级别。
3. **地测工程师确认异常**：异常记录由地测工程师或安监负责人填写确认意见后才算确认。
4. **停排指令管控排放计划**：存在未解除的停排指令期间，**禁止新增、审批或执行**任何排放计划。
5. **处置记录可回看**：每条处置记录固化当时的监测数据快照（时间范围+监测点），可在详情页查看原始数据曲线。

## 角色分工

| 角色编码 | 角色名称 | 主要职责 |
|---------|---------|---------|
| DISPATCH | 值班调度 | 录入监测数据、执行排放计划、查看曲线 |
| GEOLOGIST | 地测工程师 | 确认异常趋势、分析数据、查看曲线 |
| SAFETY_HEAD | 安监负责人 | 签发降级/停排指令、审批排放计划、全功能权限 |

## 技术架构

- **前端**：Vue 3 + Vite + Element Plus + ECharts (vue-echarts) + Pinia + Vue Router + Axios
- **后端**：FastAPI + SQLAlchemy + Pydantic + PyJWT + passlib(bcrypt)
- **数据库**：PostgreSQL 14+ 安装 TimescaleDB 扩展
  - 时序监测数据 → TimescaleDB 超表 `monitor_data`
  - 业务审批数据 → 普通关系表（用户、异常、指令、排放计划、处置记录）

## 目录结构

```
1221/
├── backend/                    # FastAPI 后端
│   ├── main.py                 # 应用入口
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env.example
│   └── app/
│       ├── __init__.py
│       ├── config.py           # 配置
│       ├── database.py         # DB 连接
│       ├── models.py           # SQLAlchemy ORM 模型
│       ├── schemas.py          # Pydantic 模型
│       ├── auth.py             # 认证鉴权（JWT + 角色权限）
│       ├── db/
│       │   └── init.sql        # 数据库初始化脚本（含演示数据）
│       └── routers/
│           ├── __init__.py
│           ├── auth.py         # 登录、用户信息
│           ├── monitor.py      # 监测点、监测数据、异常统计
│           ├── anomaly.py      # 异常记录查询/确认/关闭
│           ├── instruction.py  # 处置指令（创建/签发/解除/取消+停排检查）
│           ├── discharge.py    # 排放计划（停排校验强制阻止新增）
│           └── disposal.py     # 处置记录+数据快照回看
└── frontend/                   # Vue 3 前端
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── main.js
        ├── App.vue
        ├── router/index.js     # 路由（含角色守卫）
        ├── stores/user.js      # Pinia 用户状态
        ├── utils/
        │   ├── request.js      # Axios 封装
        │   └── auth.js         # Token & 用户缓存
        ├── api/                # 各模块 API 封装
        │   ├── auth.js
        │   ├── monitor.js
        │   ├── anomaly.js
        │   ├── instruction.js
        │   ├── discharge.js
        │   └── disposal.js
        ├── styles/main.scss
        └── views/
            ├── Login.vue
            ├── Layout.vue
            ├── Dashboard.vue
            ├── monitor/
            │   ├── DataEntry.vue   # 数据录入（值班调度）
            │   └── ChartView.vue   # 曲线查看
            ├── anomaly/
            │   ├── List.vue        # 异常列表（地测工程师确认）
            │   └── Detail.vue      # 异常详情+关联曲线
            ├── instruction/
            │   ├── List.vue        # 指令列表（安监负责人签发/解除）
            │   └── Create.vue      # 创建指令
            ├── discharge/
            │   ├── List.vue        # 排放计划（停排状态拦截）
            │   └── Create.vue      # 新增计划（停排状态强制禁用）
            └── disposal/
                ├── List.vue        # 处置记录列表
                └── Detail.vue      # 处置详情+固化数据快照曲线
```

## 快速启动

### 一、数据库准备（PostgreSQL + TimescaleDB）

1. 安装 PostgreSQL 14+ 和 TimescaleDB 扩展。
2. 创建数据库并执行初始化脚本：

```bash
createdb -U postgres tailings_monitor
psql -U postgres -d tailings_monitor -f backend/app/db/init.sql
```

脚本会自动：
- 启用 TimescaleDB 扩展并将 `monitor_data` 转为超表
- 插入 3 个角色（DISPATCH / GEOLOGIST / SAFETY_HEAD）
- 插入 3 个演示用户（密码均为 `123456`）
- 插入 3 种监测类型、7 个监测点

### 二、后端启动

```bash
cd backend
cp .env.example .env    # 根据实际情况修改数据库连接
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API 文档：http://localhost:8000/docs

### 三、前端启动

```bash
cd frontend
npm install
npm run dev
```

访问：http://localhost:5173

## 演示账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| dispatch | 123456 | 值班调度 |
| geologist | 123456 | 地测工程师 |
| safety | 123456 | 安监负责人 |

## 关键业务流程演示

### 1. 值班调度录入监测数据
1. 以 `dispatch` 登录 → 进入【监测管理 → 数据录入】
2. 选择监测点，输入监测值和时间，提交
3. 系统自动与阈值对比：
   - 单次超阈值 → 预警（WARNING）或危险（DANGER）异常
   - 2小时内连续两次超阈值 → 直接升级为 **严重（CRITICAL）**
4. 若触发异常，顶部预警徽标数字 +1

### 2. 地测工程师确认异常趋势
1. 以 `geologist` 登录 → 进入【异常预警 → 异常列表】
2. CRITICAL 级别顶部会有红色横幅提示
3. 点击【确认异常】，填写异常趋势分析与确认意见
4. 点击详情可查看异常发生前后 24 小时的原始监测曲线

### 3. 安监负责人签发停排指令
1. 以 `safety` 登录 → 进入【处置指令 → 签发指令】
2. 选择类型为【停排指令】，填写标题、内容、有效期，可关联异常
3. 可先保存草稿，也可直接签发
4. 签发后：
   - 【排放计划】页顶部出现红色横幅，且【新增计划】按钮被禁用
   - 任何新增/审批/执行排放计划的请求，后端也会强制拦截

### 4. 管控排放计划
1. 停排指令生效中时：
   - 调度无法新增计划
   - 安监负责人无法审批计划
   - 已审批的计划无法开始执行
2. 安监负责人在【处置指令】列表对该停排指令执行【解除】后，恢复正常

### 5. 处置记录与数据回看
1. 在【处置记录】中新增记录，选择时间范围和监测点形成数据快照
2. 点击记录进入详情：
   - 查看处置动作、处置人、处置时间
   - 下方 ECharts 曲线展示**当时固化的数据快照**（非实时数据），可用于事后追溯分析

## 后端核心接口一览

| 方法 | 路径 | 说明 |
|-----|------|------|
| POST | `/api/auth/login` | 登录获取 JWT |
| GET  | `/api/auth/me` | 当前用户信息 |
| GET  | `/api/monitor/types` | 监测类型 |
| GET  | `/api/monitor/points` | 监测点列表 |
| POST | `/api/monitor/data` | 录入单条监测数据（自动触发异常检测） |
| POST | `/api/monitor/data/batch` | 批量录入 |
| GET  | `/api/monitor/data` | 查询监测曲线（支持 1m/5m/15m/1h/1d 聚合） |
| GET  | `/api/monitor/data/latest` | 各监测点最新值 |
| GET  | `/api/monitor/alerts/summary` | 异常统计概览 |
| GET  | `/api/anomaly/records` | 异常列表 |
| POST | `/api/anomaly/records/{id}/confirm` | 确认异常（GEOLOGIST / SAFETY_HEAD） |
| POST | `/api/anomaly/records/{id}/close` | 关闭异常 |
| GET  | `/api/instruction/stop-check` | 当前是否存在未解除的停排指令 |
| GET  | `/api/instruction` | 处置指令列表 |
| POST | `/api/instruction` | 创建指令（草稿） |
| POST | `/api/instruction/{id}/issue` | 签发指令 |
| POST | `/api/instruction/{id}/lift` | 解除指令 |
| GET  | `/api/discharge` | 排放计划列表（全程停排校验） |
| POST | `/api/discharge` | 新增排放计划（停排状态下 400 拦截） |
| POST | `/api/discharge/{id}/approve` | 审批排放计划 |
| POST | `/api/discharge/{id}/execute` | 开始执行 |
| POST | `/api/discharge/{id}/complete` | 完成排放 |
| GET  | `/api/disposal` | 处置记录列表 |
| POST | `/api/disposal` | 新增处置记录（含数据快照范围） |
| GET  | `/api/disposal/{id}/snapshot-data` | 回看处置当时的固化数据曲线 |
