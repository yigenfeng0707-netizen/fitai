# FitAI Agent - 云栖OPC先锋创新挑战赛参赛文档

## 项目概述

**FitAI Agent** 是在已有健身/瑜伽/教培 SaaS 管理系统（FitAI）基础上，叠加 Agentic 架构层，将传统人工操作的工作流重构为 AI Agent 自主规划+执行的智能工作流。

### 核心改造思路

在**不改动现有业务系统和 API**的前提下，在业务层之上叠加 Agent 层：
- 将 28 个现有 API 封装为 18 个 Agent Tools
- 接入阿里云千问大模型（qwen-max）实现 ReAct 循环
- 三大 Agent 角色覆盖健身工作室全场景

### 技术绑定（阿里云MaaS）

| 组件 | 阿里云产品 | 用途 |
|------|-----------|------|
| LLM | 千问 qwen-max（DashScope） | 自然语言理解、推理、生成 |
| API | DashScope OpenAI兼容模式 | function calling 工具调用 |
| 应用 | 百炼应用平台（预留） | Agent 编排与部署 |
| 向量 | 阿里云向量检索（预留） | 长期记忆语义检索 |

## 架构设计

```
┌─────────────────────────────────────────────┐
│              小程序 / Web 前端               │
│         Agent 对话页 + Persona 选择          │
└──────────────────┬──────────────────────────┘
                   │ POST /api/v1/agent/chat
┌──────────────────▼──────────────────────────┐
│              Agent API Layer                 │
│   (FastAPI: /chat, /tools, /health,         │
│    /personas)                                │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│          Agent Orchestrator (ReAct)          │
│                                              │
│  ┌─────────┐  ┌──────────┐  ┌────────────┐ │
│  │ Persona  │  │  Memory  │  │ Reflection │ │
│  │ Selector │  │  Store   │  │  Check     │ │
│  └─────────┘  └──────────┘  └────────────┘ │
│                                              │
│  Loop: LLM Reason → Tool Call → Result →    │
│        Re-Reason → ... → Final Answer       │
└───────┬──────────────────┬──────────────────┘
        │                  │
┌───────▼───────┐  ┌──────▼──────────────────┐
│  Qwen Client  │  │   Tool Registry (18)    │
│  (DashScope)  │  │                          │
│  qwen-max     │  │  member(5)  course(5)   │
│  function     │  │  coach(4)   ops(4)      │
│  calling      │  │                          │
└───────────────┘  └──────────┬──────────────┘
                              │
┌─────────────────────────────▼──────────────┐
│         Existing FitAI Business Layer       │
│   (28 API routes, 22 models, PostgreSQL)    │
│         微信支付 / 课程预约 / 会员管理        │
└─────────────────────────────────────────────┘
```

## 四大 Agentic 能力

### 1. 自主规划（Autonomous Planning）
Agent 接收自然语言请求后，LLM 自主分解为多步骤计划。
- 示例："分析本周营业数据" → Agent 自动规划：先调 `get_dashboard_insights`，再调 `get_revenue_stats`，最后综合分析

### 2. 工具调用（Tool Calling）
18 个工具覆盖四大业务域，通过 OpenAI function calling 协议执行：
- **会员域**（5）：档案查询、体测记录、消费记录、预约记录、出勤率
- **课程域**（5）：课程搜索、排课查询、预约/取消、冲突检测
- **教练域**（4）：教练档案、列表、排班、绩效统计
- **运营域**（4）：仪表盘洞察、营收统计、会员留存、沉睡会员

### 3. 长期记忆（Long-term Memory）
`MemberMemoryStore` 聚合多维度结构化数据：
- 会员基本信息（等级、卡类型、消费总额）
- 最近 3 次体测记录 + 趋势对比（体重变化、体脂变化）
- 最近 10 条预约出勤率
- 消费汇总（订单数、总金额）
- 所有交互记录持久化到 `agent_interaction_log` 表

### 4. 反思迭代（Reflection）
ReAct 循环内置反思检查：
- 如果调用了工具但回复过短（<80字符），自动要求 LLM 补充更详细分析
- 最多 8 轮迭代，防止无限循环
- 每轮工具结果反馈给 LLM 重新推理

## 三大 Agent 角色

### Health Consultant（健康顾问）
面向会员/教练，专注个人健康旅程：
- 体测趋势分析（对比历史数据，识别改善/退化）
- 课程推荐（匹配目标 + 排课 + 冲突检测）
- 出勤模式分析（识别缺勤模式，建议改善）
- 预约辅助（查找 + 预约适合的课程）
- 工具集：12 个（含预约/取消写入权限）

### Studio Ops Assistant（运营助手）
面向门店 owner/管理员，充当 24/7 运营分析师：
- 营收分析（日/周/月趋势，异常识别）
- 教练绩效对比（排名，识别优劣）
- 排课优化（冲突检测，时段利用率）
- 会员留存（流失预警，干预时机）
- 工具集：16 个（全量只读）

### Growth Engine（增长引擎）
面向营销/增长，充当增长黑客：
- 沉睡会员唤醒（分群 + 个性化触达策略）
- 续费预测（到期卡 + 使用模式分析）
- 高价值会员识别（消费模式 + 升级推荐）
- 留存分析（分段 + 干预建议）
- 工具集：7 个（聚焦消费/留存/营收数据）

## OPC 评审对标

### 商业潜力
- **已有商业化验证**：FitAI 已有真实客户使用，微信支付闭环跑通
- **Agent 改造提升价值**：从人工操作升级为 AI 自主执行，降低门店运营人力成本
- **可复制性**：Agent 层架构可复用到任何垂直行业 SaaS

### 技术深度
- **ReAct 循环**：完整的 Reason → Act → Observe → Re-Reason 闭环
- **RBAC + Persona 双层权限**：角色权限 × 角色工具集的交集控制
- **结构化记忆**：多维度数据聚合，趋势对比，上下文注入
- **阿里云MaaS绑定**：qwen-max + DashScope function calling

### 创新性
- **工作流重构**：从"人查数据→人做决策→人执行"到"AI规划→AI调工具→AI给建议"
- **三大角色设计**：同一 Agent 基础设施服务不同利益相关者
- **工具层复用**：现有 API 零改动封装为 Agent Tools

## Demo 场景

### 场景1：会员体测趋势分析（Health Consultant）
```
User: "帮我查看42号会员最近的体测数据并分析趋势"
Agent:
  → 调用 get_member_profile(member_id=42)
  → 调用 get_body_tests(member_id=42, limit=5)
  → 综合分析: "张三最近3次体测显示体重从65.2kg降至63.8kg，
    体脂率从24.1%降至22.8%，下降趋势良好。肌肉量略有增加。
    建议保持当前训练频率，可适当增加力量训练。"
```

### 场景2：教练绩效对比（Studio Ops）
```
User: "对比本月教练们的绩效表现"
Agent:
  → 调用 list_coaches()
  → 逐个调用 get_coach_stats(coach_id=X) for each coach
  → 综合排名: "本月教练绩效排名：
    1. 李教练 - 课时48h，满意度4.9，出勤率96%
    2. 王教练 - 课时42h，满意度4.7，出勤率92%
    3. 张教练 - 课时35h，满意度4.5，出勤率88%
    建议：张教练出勤率偏低，建议检查排课合理性。"
```

### 场景3：沉睡会员唤醒（Growth Engine）
```
User: "设计一个沉睡会员唤醒方案，针对最有价值的20个"
Agent:
  → 调用 get_dormant_members(days=30, limit=20)
  → 调用 get_member_consumption 逐个查消费
  → 按LTV排序 + 个性化策略: "Top 20沉睡会员按LTV排序，
    前5位均为年卡会员，平均消费2.8万元。
    建议分层触达：
    - Top 5: 1对1私教体验课邀约
    - 6-15: 限时优惠续卡折扣
    - 16-20: 社群活动邀请"
```

## 部署指南

### 1. 环境配置
```bash
# .env
DASHSCOPE_API_KEY=sk-your-key-here
QWEN_MODEL=qwen-max
BAILIAN_APP_ID=your-app-id
AGENT_MAX_ITERATIONS=8
AGENT_REFLECTION_ENABLED=true
```

### 2. 数据库迁移
```bash
cd backend
alembic upgrade head
# 创建 agent_interaction_log 表
```

### 3. 启动后端
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 4. 验证 Agent 服务
```bash
# 健康检查
curl http://localhost:8000/api/v1/agent/health

# 查看工具列表
curl http://localhost:8000/api/v1/agent/tools

# 查看 Personas
curl http://localhost:8000/api/v1/agent/personas

# 发送聊天
curl -X POST http://localhost:8000/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"message": "本周营业数据概览", "persona": "studio_ops"}'
```

### 5. 小程序
```bash
cd miniapp
npm install
npm run dev:weapp
# 微信开发者工具导入 dist 目录
```

## 文件结构

```
backend/agent/
├── __init__.py
├── bootstrap.py              # Agent 单例初始化
├── orchestrator.py           # ReAct 循环核心
├── personas.py               # 三大角色定义
├── demo_scenarios.py         # OPC Demo 场景
├── run_tests.py              # 验证测试脚本
├── llm/
│   └── qwen_client.py        # 千问 DashScope 客户端
├── tools/
│   ├── registry.py           # 工具注册表
│   ├── member_tools.py       # 5个会员工具
│   ├── course_tools.py       # 5个课程工具
│   ├── coach_tools.py        # 4个教练工具
│   └── ops_tools.py          # 4个运营工具
└── memory/
    └── member_memory.py      # 长期记忆存储

backend/api/v1/
└── agent.py                  # Agent API 端点

backend/models/
└── agent_log.py              # 交互日志模型

alembic/versions/
└── 011_add_agent_log.py      # 数据库迁移

miniapp/src/
├── services/agent.ts         # Agent API 客户端
└── pages/agent/
    ├── index.tsx             # 对话页组件
    ├── index.scss            # 样式
    └── index.config.ts       # 页面配置
```

## 测试验证

```bash
python -m backend.agent.run_tests

# 输出:
# Config: PASS
# Imports: PASS (12/12 modules)
# Tool Registry: PASS (18 tools, OpenAI format)
# Personas: PASS (3 roles, tool sets)
# Demo Scenarios: PASS (9 scenarios)
# Total: 5/5 passed
```
