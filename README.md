# 健身/瑜伽/教培 AI 管理系统 - Phase 1 MVP

> **版本**: v0.1.0 (MVP)  
> **状态**: 可运行  
> **目标**: 单店跑通完整营业闭环——建档→排课→预约→签到→销课

## 🚀 快速启动

```bash
# 1. 进入项目目录
cd fit-saas-mvp

# 2. 一键启动
./start.sh

# 3. 创建管理员账号
./create_admin.sh

# 4. 访问
# 后端 API: http://localhost:8000
# API 文档: http://localhost:8000/docs
```

## 📁 项目结构

```
fit-saas-mvp/
├── backend/              # FastAPI 后端
│   ├── api/v1/           # API 路由
│   │   ├── auth.py       # 认证
│   │   ├── members.py    # 会员
│   │   ├── courses.py    # 课程
│   │   ├── bookings.py   # 预约
│   │   └── coaches.py    # 教练
│   ├── models/           # 数据库模型
│   ├── schemas/          # Pydantic Schema
│   ├── crud/             # 数据操作层
│   ├── core/             # 核心功能 (安全、权限)
│   └── worker.py         # Celery 异步任务
├── frontend/             # React 前端
│   └── src/pages/        # 页面组件
├── alembic/              # 数据库迁移
├── docker-compose.yml    # Docker 编排
├── Dockerfile
├── start.sh              # 启动脚本
└── README.md
```

## 📦 Phase 1 模块

| 模块 | 功能 | API 端点 |
|------|------|---------|
| **会员管理** | 建档、卡种、等级、消费 | `/api/v1/members/*` |
| **课程管理** | 增删改查、排期 | `/api/v1/courses/*` |
| **预约签到** | 预约、签到、取消 | `/api/v1/bookings/*` |
| **教练管理** | 档案、排班、统计 | `/api/v1/coaches/*` |
| **认证授权** | 登录、JWT、RBAC | `/api/v1/auth/*` |

## 🔧 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.12 + FastAPI |
| 数据库 | PostgreSQL 16 |
| 缓存 | Redis |
| 异步 | Celery |
| 前端 | React 18 + TypeScript + Ant Design |
| 部署 | Docker Compose |

## 🔐 权限系统

基于 RBAC 的角色权限控制：

| 角色 | 权限范围 |
|------|---------|
| 超级管理员 | 全部权限 |
| 老板/店长 | 只读 + 营销 |
| 教练 | 自己的学员 + 课程 |
| 前台 | 会员 + 课程 + 预约 |
| 财务 | 财务相关 |

## 📊 API 文档

启动后访问 `http://localhost:8000/docs` 查看完整的 Swagger 文档。

### 示例请求

```bash
# 登录
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 获取会员列表
curl -X GET http://localhost:8000/api/v1/members \
  -H "Authorization: Bearer YOUR_TOKEN"

# 创建会员
curl -X POST http://localhost:8000/api/v1/members \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "张三", "phone": "13800138000"}'
```

## 🗄️ 数据库

```bash
# 进入数据库
docker-compose exec postgres psql -U fituser -d fit_saas

# 查看表
\dt

# 查看会员
SELECT * FROM members;
```

## 📦 Phase 2 模块

| 模块 | 功能 | 状态 |
|------|------|------|
| **经营分析看板** | 营收、会员、预约、课程统计 | ✅ 已上线 |
| **潜客 CRM** | 潜客跟进、状态流转、转化 | ✅ 已上线 |
| **消息通知** | 系统通知、到期提醒 | ✅ 已上线 |
| **AI 智能助手** | 体测记录、课程推荐 | ✅ 已上线 |
| **营销活动** | 活动创建、渠道推送、效果追踪 | ✅ 已上线 |
| **微信支付 V3** | Native/JSAPI 支付、退款、通知验签 | ✅ 已对接 (需配置商户参数) |

> **微信支付**: 需要在 `.env` 中配置 `WECHAT_PAY_*` 参数后才可真实调用，未配置时自动使用模拟模式。

## 📈 下一步 (Phase 3)

- [ ] 连锁店管理/多门店
- [ ] 小程序端
- [ ] 营销自动化
- [ ] 深度数据分析
- [ ] 自定义字段/表单

## 📄 许可证

MIT License