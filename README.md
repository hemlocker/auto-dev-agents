# 全自动开发智能体系统

**项目名称：** Auto-Dev-Agents  
**架构：** 基于 OpenClaw 平台  
**描述：** 利用 OpenClaw 平台能力，实现软件开发全流程自动化

---

## 🎯 项目目标

将软件开发全流程（需求→设计→编码→测试→部署→运维）交给 AI 智能体团队自动完成。

**核心理念：** 复用 OpenClaw 平台能力，不重复造轮子。

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│              全自动开发智能体系统 (v2.0)                         │
│                    基于 OpenClaw 平台                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   OpenClaw 平台能力                      │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │   │
│  │  │ Sessions │ │   Cron   │ │  Memory  │ │  Tools   │   │   │
│  │  │ 会话管理  │ │ 定时任务  │ │  知识库  │ │  工具集  │   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐                │   │
│  │  │  Agent   │ │ Spawn    │ │  Model   │                │   │
│  │  │  智能体   │ │ 子会话   │ │  大模型  │                │   │
│  │  └──────────┘ └──────────┘ └──────────┘                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   智能体工作流                           │   │
│  │                                                           │   │
│  │   Requirement → Design → Development → Testing           │   │
│  │        ↓                                       ↓          │   │
│  │   Optimizer ← Monitor ← Operations ← Deployment          │   │
│  │                                                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   项目数据                               │   │
│  │   projects/{project}/input  → 输入（反馈、会议、工单）   │   │
│  │   projects/{project}/output → 输出（文档、代码、部署）   │   │
│  │   prompts/                  → 提示词库                  │   │
│  │   knowledge/                → 知识库                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 项目结构

```
auto-dev-agents/
├── prompts/                  # 提示词库
│   ├── coordinator/system.md # 协调智能体提示词
│   ├── requirement/system.md # 需求智能体提示词
│   ├── design/system.md      # 设计智能体提示词
│   ├── development/system.md # 开发智能体提示词
│   ├── testing/system.md     # 测试智能体提示词
│   ├── deployment/system.md  # 部署智能体提示词
│   ├── operations/system.md  # 运维智能体提示词
│   ├── monitor/system.md     # 监控智能体提示词
│   └── optimizer/system.md   # 优化智能体提示词
│
├── knowledge/                # 知识库
│   ├── agents/              # 智能体知识
│   ├── checklists/          # 检查清单
│   └── templates/           # 文档模板
│
├── projects/                 # 项目目录（运行时创建，已加入 gitignore）
│   └── {project_name}/      # 按项目名称创建
│       ├── project.json     # 项目配置
│       ├── input/           # 项目输入
│       └── output/          # 项目输出
│
├── scripts/                  # 脚本工具
│   ├── create_project.py    # 创建项目
│   └── run_workflow.py      # 运行工作流
│
├── docs/                     # 文档
│
├── .openclaw/                # OpenClaw 配置
│   └── cron.yaml            # 定时任务配置
│
├── config.yaml               # 项目配置
├── README.md                 # 项目说明
└── requirements.txt          # Python 依赖
```

---

## 🤖 智能体团队

| 智能体 | 角色 | 职责 | 提示词 |
|--------|------|------|--------|
| **Coordinator** | 协调者 | 任务分配、流程控制 | prompts/coordinator/ |
| **Requirement** | 需求分析师 | 需求收集、分析、转换 | prompts/requirement/ |
| **Design** | 架构师 | 架构设计、详细设计 | prompts/design/ |
| **Development** | 开发工程师 | 编码实现、代码审查 | prompts/development/ |
| **Testing** | 测试专家 | 测试执行、质量验证 | prompts/testing/ |
| **Deployment** | 运维工程师 | 部署上线、配置管理 | prompts/deployment/ |
| **Operations** | 运维监控 | 系统监控、问题收集 | prompts/operations/ |
| **Monitor** | 质量监控 | 质量检查、告警通知 | prompts/monitor/ |
| **Optimizer** | 流程优化 | 流程改进、性能优化 | prompts/optimizer/ |

---

## 🚀 快速开始

### 1. 创建项目

```bash
cd /root/.openclaw/workspace/projects/auto-dev-agents

# 创建新项目
python3 scripts/create_project.py --name my_project --goal "订单管理系统"
```

### 2. 编辑项目目标

```bash
# 编辑项目目标文件
vim projects/my_project/input/feedback/project_goal.md
```

### 3. 运行工作流

**方式 1：命令行运行**
```bash
# 运行需求分析阶段
python3 scripts/run_workflow.py --project my_project --stages requirement

# 运行完整工作流
python3 scripts/run_workflow.py --project my_project
```

**方式 2：OpenClaw 子会话**

在 OpenClaw 中使用 sessions_spawn 创建子会话运行智能体任务：

```
用 sessions_spawn 运行需求分析智能体，任务：分析 projects/my_project 的需求
```

---

## 🔧 与 OpenClaw 集成

### 使用 OpenClaw 会话能力

本系统设计为**复用 OpenClaw 平台能力**：

| OpenClaw 能力 | 本系统用途 |
|--------------|-----------|
| `sessions_spawn` | 创建子会话运行智能体任务 |
| `sessions_list` | 查看运行中的智能体会话 |
| `sessions_send` | 向智能体发送指令 |
| `memory_search` | 智能体知识检索 |
| `cron` | 定时触发工作流 |
| `browser` | 智能体网页交互 |
| `exec` | 智能体执行命令 |

### 示例：在 OpenClaw 中运行智能体

```
用户：帮我运行 demo_project 的需求分析

助手：好的，我来创建子会话运行需求分析智能体...

[sessions_spawn(
  runtime="subagent",
  task="分析 projects/demo_project 的需求，参考 prompts/requirement/system.md",
  cwd="/root/.openclaw/workspace/projects/auto-dev-agents"
)]
```

---

## 📋 使用示例

### 示例 1：启动新项目

```bash
# 创建项目
python3 scripts/create_project.py \
  --name order_system \
  --goal "订单管理系统，支持订单创建、查询、统计"

# 编辑需求
vim projects/order_system/input/feedback/project_goal.md

# 在 OpenClaw 中运行
# 对 OpenClaw 说："运行 order_system 的开发工作流"
```

### 示例 2：查看项目状态

```bash
# 查看项目配置
cat projects/{project_name}/project.json

# 查看输出
ls -la projects/{project_name}/output/
```

---

## 🔧 配置说明

### 项目配置 (config.yaml)

```yaml
version: "2.0"

projects:
  dir: "projects"
  default: ""  # 首次使用需创建项目

workflow:
  stages:
    - name: "requirement"
      agent: "RequirementAgent"
      prompt: "prompts/requirement/system.md"
    # ... 其他阶段

  execution:
    stage_delay_minutes: 5
    quality_threshold: 0.85
    max_iterations: 3

openclaw:
  use_default_model: true
  runtime: "subagent"
```

### Cron 配置 (.openclaw/cron.yaml)

通过 OpenClaw 的 cron 功能定时触发工作流。

---

## 📖 相关文档

- [智能体架构设计](docs/AGENT_ARCHITECTURE.md)
- [项目管理指南](docs/PROJECT_MANAGEMENT_GUIDE.md)
- [OpenClaw 文档](https://docs.openclaw.ai)

---

## 🆚 v1 vs v2 对比

| 特性 | v1（旧版） | v2（基于 OpenClaw） |
|------|-----------|-------------------|
| LLM 调用 | 自己实现 | 复用 OpenClaw |
| 智能体类 | Python 类 | OpenClaw 会话 |
| 工作流编排 | Python 脚本 | OpenClaw sessions_spawn |
| 知识存储 | 自己实现 | OpenClaw memory |
| 工具调用 | 自己实现 | OpenClaw tools |
| 代码量 | ~3500 行 | ~500 行 |
| 依赖 | 多个 Python 包 | 仅 pyyaml |

---

**版本：** v0.1.1
**架构：** 基于 OpenClaw 平台