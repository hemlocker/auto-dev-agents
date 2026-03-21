# 项目结构改进报告

**更新时间：** 2026-03-21 12:45  
**状态：** ✅ 完成

---

## 🎯 改进内容

### 之前的问题

❌ **全局输入输出**
```
input/           # 所有项目共用
output/          # 所有项目共用
```

**问题：**
- 多个项目混在一起
- 难以区分项目文件
- 容易误删其他项目文件
- 无法并行运行项目

---

### 现在的解决方案

✅ **按项目组织**
```
projects/
├── project_001/
│   ├── input/          # 项目 1 输入
│   ├── output/         # 项目 1 输出
│   └── project.json    # 项目 1 配置
├── project_002/
│   ├── input/          # 项目 2 输入
│   ├── output/         # 项目 2 输出
│   └── project.json    # 项目 2 配置
└── ...
```

**优势：**
- ✅ 项目完全隔离
- ✅ 易于管理
- ✅ 支持并行运行
- ✅ 易于导出/导入
- ✅ 清晰的项目历史

---

## 📁 项目结构

### 目录结构

```
projects/
└── <项目名称>/
    ├── input/                    # 项目输入
    │   ├── feedback/             # 用户反馈
    │   ├── meetings/             # 会议记录
    │   └── emails/               # 邮件
    │
    ├── output/                   # 项目输出
    │   ├── requirements/         # 需求文档
    │   ├── design/               # 设计文档
    │   ├── src/                  # 源代码
    │   ├── tests/                # 测试代码
    │   ├── deploy/               # 部署包
    │   └── operations/           # 运维报告
    │
    ├── logs/                     # 项目日志
    │   ├── agents/               # 智能体日志
    │   └── workflows/            # 工作流日志
    │
    └── project.json              # 项目配置
```

### 项目配置

**文件：** `project.json`

```json
{
  "name": "项目名称",
  "created_at": "2026-03-21T12:40:15",
  "updated_at": "2026-03-21T12:40:15",
  "status": "created",
  "goal": "项目目标",
  "workflow_results": [
    {
      "timestamp": "2026-03-21T12:45:00",
      "success": true,
      "avg_quality": 0.85,
      "completed_stages": 8,
      "total_stages": 8
    }
  ]
}
```

---

## 🔧 管理命令

### 创建项目

```bash
# 基本用法
python3 scripts/project_manager.py create <项目名称>

# 指定目标
python3 scripts/project_manager.py create order_system --goal "订单管理系统"

# 输出示例
✅ 项目创建成功：order_system
   项目路径：/path/to/projects/order_system
   项目目标：订单管理系统
```

### 列出项目

```bash
python3 scripts/project_manager.py list

# 输出示例
项目名称                           状态              创建时间                 目标                            
----------------------------------------------------------------------------------------------------
order_system                   created         2026-03-21           订单管理系统                      
user_mgmt                      created         2026-03-21           用户管理系统                      
```

### 查看状态

```bash
python3 scripts/project_manager.py status <项目名称>

# 输出示例
项目名称：order_system
项目目标：订单管理系统
创建时间：2026-03-21T12:40:15
最后更新：2026-03-21T12:40:15
当前状态：created

输出文件:
   requirements/: 0 个文件
   design/: 0 个文件
   src/: 0 个文件
   ...
```

### 删除项目

```bash
# 预览
python3 scripts/project_manager.py delete order_system

# 确认
python3 scripts/project_manager.py delete order_system --confirm
```

### 导出/导入

```bash
# 导出
python3 scripts/project_manager.py export order_system --output order_system.zip

# 导入
python3 scripts/project_manager.py import order_system.zip
```

---

## 📋 使用流程

### 1. 创建项目

```bash
# 创建项目
python3 scripts/project_manager.py create my_project --goal "我的项目"
```

### 2. 添加需求

```bash
# 添加用户需求
cat > projects/my_project/input/feedback/feature_001.md << 'EOF'
# 功能需求

作为 用户
我想要 功能
以便于 价值

## 验收标准
- 标准 1
- 标准 2
EOF
```

### 3. 运行智能体

```bash
# 为项目运行智能体
python3 scripts/start_agents.py --project my_project
```

### 4. 查看结果

```bash
# 查看输出
ls -lh projects/my_project/output/

# 查看文档
cat projects/my_project/output/requirements/user_requirements.md
```

### 5. 管理项目

```bash
# 查看状态
python3 scripts/project_manager.py status my_project

# 导出项目
python3 scripts/project_manager.py export my_project

# 删除项目
python3 scripts/project_manager.py delete my_project --confirm
```

---

## 📊 项目统计

### 示例项目

**名称：** demo_project  
**目标：** 订单管理系统演示  
**创建时间：** 2026-03-21 12:40  
**状态：** created

**目录结构：**
```
projects/demo_project/
├── input/
│   ├── feedback/
│   ├── meetings/
│   └── emails/
├── output/
│   ├── requirements/
│   ├── design/
│   ├── src/
│   ├── tests/
│   ├── deploy/
│   └── operations/
├── logs/
│   ├── agents/
│   └── workflows/
└── project.json
```

---

## 🎯 优势对比

| 特性 | 之前（全局） | 现在（按项目） |
|------|-------------|---------------|
| 项目隔离 | ❌ | ✅ |
| 多项目并行 | ❌ | ✅ |
| 项目管理 | ❌ | ✅ |
| 导出/导入 | ❌ | ✅ |
| 项目历史 | ❌ | ✅ |
| 清晰结构 | ❌ | ✅ |

---

## 📖 相关文档

- [项目管理指南](./PROJECT_MANAGEMENT_GUIDE.md) - 详细使用说明
- [README.md](../README.md) - 项目说明
- [SCRIPTS_GUIDE.md](./SCRIPTS_GUIDE.md) - 脚本使用指南

---

**状态：** ✅ 完成  
**版本：** 2.1  
**最后更新：** 2026-03-21 12:45
