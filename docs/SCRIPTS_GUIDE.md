# 脚本使用指南

**更新时间：** 2026-03-21 11:50  
**版本：** 2.0

---

## 📁 脚本目录

```
scripts/
├── start_agents.py        # 启动脚本
├── stop_agents.py         # 停止脚本
├── manage_agents.py       # 管理脚本
├── view_logs.py           # 日志查看脚本
└── logger.py              # 日志模块
```

---

## 🚀 启动脚本 (start_agents.py)

### 功能
- 启动智能体系统
- 运行完整工作流
- 支持自定义项目目标

### 使用方式

```bash
# 基本用法
python3 scripts/start_agents.py

# 指定项目目标
python3 scripts/start_agents.py --goal "订单管理系统"

# 使用工作流模式
python3 scripts/start_agents.py --workflow

# 使用 Cron 模式
python3 scripts/start_agents.py --cron
```

### 示例

```bash
# 启动新项目
python3 scripts/start_agents.py --goal "用户管理系统"

# 查看实时日志
tail -f logs/agents/coordinator.log
```

---

## 🛑 停止脚本 (stop_agents.py)

### 功能
- 停止运行中的智能体
- 清理 PID 文件
- 保存当前状态

### 使用方式

```bash
# 基本用法
python3 scripts/stop_agents.py

# 强制停止
python3 scripts/stop_agents.py --force

# 查看状态
python3 scripts/stop_agents.py --status

# 停止所有相关进程
python3 scripts/stop_agents.py --all
```

### 示例

```bash
# 正常停止
python3 scripts/stop_agents.py

# 查看运行状态
python3 scripts/stop_agents.py --status

# 强制停止卡住的进程
python3 scripts/stop_agents.py --force
```

---

## 🔧 管理脚本 (manage_agents.py)

### 功能
- 查看智能体状态
- 运行单个智能体
- 查看工作流状态
- 管理系统配置
- 清理输出目录

### 使用方式

```bash
# 查看智能体状态
python3 scripts/manage_agents.py status

# 运行单个智能体
python3 scripts/manage_agents.py run RequirementAgent

# 运行智能体并指定输入
python3 scripts/manage_agents.py run DesignAgent --input output/requirements/

# 停止智能体
python3 scripts/manage_agents.py stop

# 查看配置
python3 scripts/manage_agents.py config --show

# 检查配置
python3 scripts/manage_agents.py config --check

# 查看工作流状态
python3 scripts/manage_agents.py workflow

# 清理输出目录
python3 scripts/manage_agents.py clean --confirm
```

### 示例

```bash
# 查看所有智能体状态
python3 scripts/manage_agents.py status

# 运行需求智能体
python3 scripts/manage_agents.py run RequirementAgent

# 运行设计智能体，使用已有的需求文档
python3 scripts/manage_agents.py run DesignAgent -i output/requirements/

# 查看工作流执行结果
python3 scripts/manage_agents.py workflow

# 清理输出目录（先预览）
python3 scripts/manage_agents.py clean

# 确认清理
python3 scripts/manage_agents.py clean --confirm
```

---

## 📊 日志查看脚本 (view_logs.py)

### 功能
- 查看所有日志文件列表
- 查看特定智能体日志
- 查看工作流日志
- 查看 Cron 日志
- 实时跟踪日志
- 搜索日志内容
- 导出日志

### 使用方式

```bash
# 列出所有日志文件
python3 scripts/view_logs.py list

# 查看所有智能体日志
python3 scripts/view_logs.py agents

# 查看特定智能体日志
python3 scripts/view_logs.py agents --agent RequirementAgent

# 查看最后 N 行
python3 scripts/view_logs.py agents --lines 50

# 查看工作流日志
python3 scripts/view_logs.py workflow

# 查看 Cron 日志
python3 scripts/view_logs.py cron

# 实时跟踪日志
python3 scripts/view_logs.py tail

# 跟踪特定智能体
python3 scripts/view_logs.py tail --agent Coordinator

# 搜索日志
python3 scripts/view_logs.py search "错误"

# 搜索并限制结果数
python3 scripts/view_logs.py search "质量" --limit 20

# 导出日志
python3 scripts/view_logs.py export

# 导出到指定文件
python3 scripts/view_logs.py export --output logs/backup.txt
```

### 示例

```bash
# 查看所有日志文件
python3 scripts/view_logs.py list

# 查看需求智能体日志（最后 100 行）
python3 scripts/view_logs.py agents -a RequirementAgent -n 100

# 实时跟踪协调智能体日志
python3 scripts/view_logs.py tail -a Coordinator

# 搜索所有包含"错误"的日志
python3 scripts/view_logs.py search "错误"

# 搜索质量相关的警告
python3 scripts/view_logs.py search "质量" -l 30

# 导出所有日志用于分析
python3 scripts/view_logs.py export -o logs/all_logs_$(date +%Y%m%d).txt
```

---

## 📝 日志模块 (logger.py)

### 功能
- 统一的日志记录
- 日志级别控制
- 日志文件轮转
- 日志分类存储

### 使用方式

```python
from scripts.logger import (
    get_logger,
    log_agent_action,
    log_stage_execution,
    log_quality_check,
    log_alert
)

# 获取日志记录器
logger = get_logger("MyAgent")

# 记录动作
log_agent_action("MyAgent", "开始执行", "处理输入数据")

# 记录阶段执行
log_stage_execution(
    stage_name="需求收集",
    agent_name="RequirementAgent",
    status="success",
    quality=0.92,
    duration=285.5
)

# 记录质量检查
log_quality_check(
    stage_name="需求收集",
    check_name="需求完整性",
    passed=True,
    value=0.95,
    threshold=0.85
)

# 记录告警
log_alert(
    level="P1",
    stage="编码实现",
    message="测试覆盖率不足",
    value=0.65,
    threshold=0.80
)
```

---

## 🔄 典型工作流

### 1. 启动项目

```bash
# 1. 启动智能体系统
python3 scripts/start_agents.py --goal "订单管理系统"

# 2. 实时查看日志
python3 scripts/view_logs.py tail -a Coordinator
```

### 2. 监控执行

```bash
# 1. 查看智能体状态
python3 scripts/manage_agents.py status

# 2. 查看工作流进度
python3 scripts/manage_agents.py workflow

# 3. 搜索错误日志
python3 scripts/view_logs.py search "错误"
```

### 3. 管理智能体

```bash
# 1. 运行单个智能体
python3 scripts/manage_agents.py run DesignAgent -i output/requirements/

# 2. 查看执行结果
cat output/design/architecture.md

# 3. 查看日志
python3 scripts/view_logs.py agents -a DesignAgent -n 100
```

### 4. 停止系统

```bash
# 1. 正常停止
python3 scripts/stop_agents.py

# 2. 确认已停止
python3 scripts/stop_agents.py --status

# 3. 如有问题，强制停止
python3 scripts/stop_agents.py --force
```

### 5. 清理和维护

```bash
# 1. 清理输出目录
python3 scripts/manage_agents.py clean --confirm

# 2. 导出日志备份
python3 scripts/view_logs.py export -o logs/backup_$(date +%Y%m%d).txt

# 3. 检查配置
python3 scripts/manage_agents.py config --check
```

---

## 📊 日志文件结构

```
logs/
├── agents/                  # 智能体日志
│   ├── CoordinatorAgent.log
│   ├── RequirementAgent.log
│   ├── DesignAgent.log
│   ├── DevelopmentAgent.log
│   ├── TestingAgent.log
│   ├── DeploymentAgent.log
│   ├── OperationsAgent.log
│   ├── MonitorAgent.log
│   └── OptimizerAgent.log
│
├── workflows/               # 工作流日志
│   └── workflow.log
│
├── cron/                    # Cron 日志
│   └── cron.log
│
└── alerts/                  # 告警日志
    └── alerts.log
```

---

## 🔍 日志级别

| 级别 | 说明 | 使用场景 |
|------|------|----------|
| DEBUG | 调试信息 | 开发调试 |
| INFO | 一般信息 | 正常运行信息 |
| WARNING | 警告信息 | 需要注意但不影响运行 |
| ERROR | 错误信息 | 执行失败 |
| CRITICAL | 严重错误 | 系统故障 |

---

## 📖 相关文档

- [README.md](../README.md) - 项目说明
- [QUICKSTART.md](../QUICKSTART.md) - 快速开始
- [PROJECT_FINAL_STATUS.md](./PROJECT_FINAL_STATUS.md) - 项目状态

---

**状态：** ✅ 脚本齐全  
**版本：** 2.0  
**最后更新：** 2026-03-21
