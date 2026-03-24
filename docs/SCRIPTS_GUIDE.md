# 脚本使用指南

**更新时间：** 2026-03-24
**版本：** 3.0

> ⚠️ **注意**：本项目不包含 `start_agents.py`、`stop_agents.py`、`manage_agents.py`、`view_logs.py`、`logger.py` 等脚本。这些脚本是早期设计阶段遗留的文档，请勿参考使用。

> ✅ **实际入口**：`scripts/run.py` 是唯一的 CLI 入口。

---

## 📁 实际脚本目录

```
scripts/
├── run.py                          # 主入口 - 工作流执行器
├── state_manager.py                # 统一状态管理器
├── context_manager.py               # 上下文管理器
├── quality_gate.py                 # 质量门禁
├── input_monitor.py                # 输入监控触发器
├── create_project.py               # 项目创建工具
├── incremental_update.py           # 增量更新工具
├── ticket_dedup.py                 # 工单去重工具
└── workflow/
    ├── models.py                   # 数据模型、子任务定义
    ├── executors.py                # 子智能体执行器、输入分析器
    ├── state.py                    # 工作流状态管理
    ├── distributed_state.py        # 分布式状态管理器（断点续传）
    ├── revision_history.py          # 修订历史管理
    ├── versioned_output.py          # 版本化输出管理
    ├── manifest.py                  # 清单管理
    └── csv_parser.py                # CSV 输入解析器
```

---

## 🚀 主入口 (run.py)

### 功能
- 工作流执行（单阶段 / 批量 / 完整 PDCA 循环）
- 子任务拆分执行（支持断点续传）
- 版本化增量更新
- 状态查看

### 使用方式

```bash
# 查看状态
python3 scripts/run.py -p my-project --status

# 执行指定阶段
python3 scripts/run.py -p my-project --stages requirement,design --execute

# 执行完整 PDCA 循环
python3 scripts/run.py -p my-project --full-cycle --execute

# 使用模板
python3 scripts/run.py -p my-project --template dev-only --execute

# 指定项目类型和子任务策略
python3 scripts/run.py -p my-project --project-type fullstack --subtask-strategy module --execute

# 查看版本状态
python3 scripts/run.py -p my-project --version-status
```

### 示例

```bash
# 前后端分离项目
python3 scripts/run.py -p my-project --project-type fullstack --stages requirement,design,development --execute

# 纯后端项目
python3 scripts/run.py -p my-project --project-type backend_only --stages requirement,design --execute
```

---

## 📊 状态管理

### 状态管理器 (state_manager.py)

统一状态管理器，提供工作流状态、智能体状态、事件日志、反馈追踪等功能。

```bash
python3 scripts/state_manager.py -p my-project --summary
python3 scripts/state_manager.py -p my-project --events
python3 scripts/state_manager.py -p my-project --decisions
```

### 工作流状态 (workflow/state.py)

轻量级工作流状态管理，专注于执行进度追踪。

### 分布式状态 (workflow/distributed_state.py)

支持断点续传和版本化增量更新的分布式状态管理。

```bash
# 重置增量状态
python3 scripts/run.py -p my-project --reset-incremental --execute

# 重置版本状态
python3 scripts/run.py -p my-project --reset-version --execute

# 统一重置增量更新状态
python3 scripts/run.py -p my-project --reset-for-incremental --execute
```

---

## 🔄 典型工作流

### 1. 启动新项目

```bash
# 创建项目
python3 scripts/create_project.py -p my-project --goal "订单管理系统"

# 执行需求分析
python3 scripts/run.py -p my-project --stages requirement --execute
```

### 2. 增量迭代

```bash
# 添加新需求后，增量执行
python3 scripts/run.py -p my-project --stages requirement,design,development --execute

# 查看进度
python3 scripts/run.py -p my-project --status
```

### 3. 监控执行

```bash
# 持续监控状态
python3 scripts/run.py -p my-project --status

# 查看断点续传状态
python3 scripts/run.py -p my-project --version-status
```

---

## 📋 子任务执行

系统支持子任务拆分执行，适用于大型项目的分阶段开发：

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| `layer` | 按技术层拆分（水平切片） | ≤2 个模块 |
| `module` | 按功能模块拆分（垂直切片） | >2 个模块 |
| `auto` | 自动选择 | 推荐默认 |

---

## 📂 输出文件结构

```
projects/{project}/
├── project.json               # 项目元信息
├── input/                     # 输入目录
│   ├── feedback/
│   ├── meetings/
│   ├── emails/
│   └── tickets/
├── output/                    # 输出目录
│   ├── requirements/          # 需求阶段输出
│   ├── design/                # 设计阶段输出
│   ├── src/                   # 开发阶段输出
│   ├── tests/                 # 测试阶段输出
│   ├── deploy/                # 部署阶段输出
│   └── operations/            # 运维阶段输出
└── state/                     # 状态目录
    ├── state.json             # 统一状态
    ├── events.jsonl           # 事件日志
    └── contexts/              # 上下文缓存
```

---

## 📖 相关文档

- [README.md](../README.md) - 项目说明
- [ROADMAP.md](../ROADMAP.md) - 能力路线图
- [AGENT_ARCHITECTURE.md](./AGENT_ARCHITECTURE.md) - 智能体架构

---

**状态：** ⚠️ 文档已修正为匹配实际脚本
**版本：** 3.0
**最后更新：** 2026-03-24
