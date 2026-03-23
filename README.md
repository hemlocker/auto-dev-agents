# Auto Dev Agents

全自动开发智能体系统 - 基于 OpenClaw 平台

## 特性

- 🚀 **全自动开发流程**：从需求到部署的完整 PDCA 循环
- 🧩 **可配置工作流**：灵活的阶段定义和模板支持
- 🔄 **智能子任务拆分**：按技术层或功能模块动态拆分
- 📊 **依赖自动推断**：基于规则引擎智能识别模块依赖
- 📦 **大输入分批处理**：自动检测并分批处理超大输入
- 🏗️ **多项目类型支持**：前后端分离、纯后端、DDD、微服务等

## 快速开始

### 安装

```bash
git clone https://github.com/hemlocker/auto-dev-agents.git
cd auto-dev-agents
pip install -r requirements.txt
```

### 运行测试

```bash
# 使用测试数据运行完整 PDCA 循环
./test-data/run-test.sh my-project

# 或手动执行
python3 scripts/run.py -p my-project --full-cycle --execute
```

## 使用方式

### 基本命令

```bash
# 查看状态
python3 scripts/run.py -p my-project --status

# 执行完整 PDCA 循环
python3 scripts/run.py -p my-project --full-cycle --execute

# 执行指定阶段
python3 scripts/run.py -p my-project --stages requirement,design --execute

# 使用模板
python3 scripts/run.py -p my-project --template dev-only --execute
```

### 项目类型

```bash
# 前后端分离（默认）
python3 scripts/run.py -p my-project --project-type fullstack --execute

# 纯后端项目
python3 scripts/run.py -p my-project --project-type backend_only --execute

# Django 单体应用
python3 scripts/run.py -p my-project --project-type django_monolith --execute

# 微服务项目
python3 scripts/run.py -p my-project --project-type microservices --execute
```

### 子任务拆分策略

```bash
# 按技术层拆分（水平切片）
python3 scripts/run.py -p my-project --subtask-strategy layer --execute

# 按功能模块拆分（垂直切片）
python3 scripts/run.py -p my-project --subtask-strategy module --execute

# 自动选择（推荐）
python3 scripts/run.py -p my-project --subtask-strategy auto --execute
```

## 工作流阶段

### PLAN 阶段
| 阶段 | 说明 | 输出 |
|------|------|------|
| requirement | 需求分析 | 用户需求、软件需求、RTM |
| design | 系统设计 | 架构设计、详细设计、API规范 |

### DO 阶段
| 阶段 | 说明 | 输出 |
|------|------|------|
| development | 代码开发 | 后端代码、前端代码 |
| testing | 测试验证 | 单元测试、集成测试、测试报告 |
| deployment | 部署配置 | Docker、Nginx、部署脚本 |

### CHECK 阶段
| 阶段 | 说明 | 输出 |
|------|------|------|
| operations | 运维配置 | Prometheus、Grafana、告警规则 |
| monitor | 质量监控 | 质量报告、SLA统计 |

### ACT 阶段
| 阶段 | 说明 | 输出 |
|------|------|------|
| optimizer | 持续优化 | 优化建议、改进计划 |

## 项目类型模板

| 项目类型 | 子任务特点 | 适用场景 |
|----------|------------|----------|
| `fullstack` | 前后端分离，7个子任务 | Web 应用 |
| `backend_only` | 纯后端，6个子任务 | API 服务、CLI 工具 |
| `frontend_only` | 纯前端，5个子任务 | SPA 应用 |
| `django_monolith` | Django单体，6个子任务 | Django 项目 |
| `microservices` | 微服务，5个子任务 | 微服务架构 |

## 子任务拆分策略

### Layer 策略（水平切片）

```
子任务1: models（所有模块的数据模型）
子任务2: repositories（所有模块的仓储）
子任务3: services（所有模块的服务）
子任务4: controllers（所有模块的控制器）
```

**适用：** 小型项目、传统分层团队

### Module 策略（垂直切片）

```
子任务1: shared_infra（公共基础设施）
子任务2: user_module（用户模块完整实现）
子任务3: device_module（设备模块完整实现）
子任务4: order_module（订单模块完整实现）
```

**适用：** 中大型项目、模块化架构、支持并行开发

### Auto 策略

- ≤2个模块 → 自动选择 `layer`
- >2个模块 → 自动选择 `module`

## 模块依赖推断

系统自动从需求文档中推断模块依赖关系：

```python
需求描述:
"设备需要关联所属用户"
"维修需要关联设备和维修人员"

自动推断:
- device 依赖 user
- repair 依赖 user + device
- 开发顺序: user → device → repair
```

### 推断规则

| 规则 | 模式 | 示例 |
|------|------|------|
| foreign_key | "A关联B" | 设备关联用户 → device依赖user |
| composition | "A包含B" | 订单包含设备 → order依赖device |
| reference | "A需要B信息" | 维修需要设备 → repair依赖device |
| business_pattern | 业务模式 | 订单自动依赖用户 |

## 配置说明

```yaml
# config.yaml

# 项目配置
projects:
  type: fullstack  # 项目类型

# 工作流配置
workflow:
  template: full-pdca      # 预设模板
  subtask_strategy: auto    # 子任务拆分策略

# 执行配置
execution:
  stage_delay_seconds: 30
  timeout_seconds: 1800
  
  context:
    max_input_tokens: 150000  # 最大输入 token
    max_file_count: 50        # 最大文件数
    batch_size: 15            # 分批文件数
```

## 目录结构

```
auto-dev-agents/
├── scripts/
│   ├── run.py              # CLI 入口
│   ├── workflow/           # 核心模块
│   │   ├── models.py       # 数据模型、子任务定义
│   │   ├── executors.py    # 执行器
│   │   └── state.py        # 状态管理
│   ├── state_manager.py
│   ├── context_manager.py
│   ├── input_monitor.py
│   └── quality_gate.py
├── prompts/                # 智能体提示词
│   ├── requirement/
│   ├── design/
│   └── ...
├── projects/               # 项目数据
├── test-data/              # 测试数据
└── config.yaml             # 配置文件
```

## 模型限制

当前配置针对以下模型限制优化：

| 参数 | 值 |
|------|-----|
| contextWindow | 202,752 |
| maxTokens | 16,384 |
| 安全输入 | 150,000 tokens |

## 开发进度

### v0.1.2

- ✅ 可配置工作流阶段（方案 A+B）
- ✅ 错误处理和依赖检查
- ✅ Gateway 认证自动加载
- ✅ 子任务拆分 + 增量执行
- ✅ 大输入分批处理
- ✅ 模块依赖智能推断引擎
- ✅ 子任务拆分策略选择（layer/module/auto）
- ✅ 项目类型模板支持
- ✅ 代码模块化重构

## 许可证

MIT