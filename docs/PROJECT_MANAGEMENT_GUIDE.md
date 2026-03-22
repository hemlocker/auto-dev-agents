# 项目管理指南

**更新时间：** 2026-03-21 12:40  
**版本：** 2.1

---

## 📁 项目结构

### 按项目组织

```
auto-dev-agents/
├── projects/                    # 项目目录
│   ├── project_001/             # 项目 1
│   │   ├── input/               # 项目输入
│   │   │   ├── feedback/        # 用户反馈
│   │   │   ├── meetings/        # 会议记录
│   │   │   └── emails/          # 邮件
│   │   ├── output/              # 项目输出
│   │   │   ├── requirements/    # 需求文档
│   │   │   ├── design/          # 设计文档
│   │   │   ├── src/             # 源代码
│   │   │   ├── tests/           # 测试代码
│   │   │   └── deploy/          # 部署包
│   │   ├── logs/                # 项目日志
│   │   └── project.json         # 项目配置
│   ├── project_002/             # 项目 2
│   └── ...
│
├── input/                       # 全局输入（可选）
├── output/                      # 全局输出（可选）
└── ...
```

---

## 🚀 项目管理

### 创建项目

```bash
# 创建新项目
python3 scripts/project_manager.py create <项目名称> --goal "<项目目标>"

# 示例
python3 scripts/project_manager.py create order_system --goal "订单管理系统"
python3 scripts/project_manager.py create user_mgmt --goal "用户管理系统"
```

### 列出项目

```bash
# 列出所有项目
python3 scripts/project_manager.py list

# 输出示例：
项目名称                           状态              创建时间                 目标                            
----------------------------------------------------------------------------------------------------
order_system                   created         2026-03-21           订单管理系统                      
user_mgmt                      created         2026-03-21           用户管理系统                      
```

### 查看项目状态

```bash
# 查看项目状态
python3 scripts/project_manager.py status <项目名称>

# 示例
python3 scripts/project_manager.py status order_system
```

### 删除项目

```bash
# 删除项目（先预览）
python3 scripts/project_manager.py delete <项目名称>

# 确认删除
python3 scripts/project_manager.py delete <项目名称> --confirm
```

### 导出/导入项目

```bash
# 导出项目
python3 scripts/project_manager.py export <项目名称> --output <文件名>.zip

# 导入项目
python3 scripts/project_manager.py import <文件名>.zip
```

---

## 📋 项目工作流

### 1. 创建项目

```bash
# 创建项目
python3 scripts/project_manager.py create my_project --goal "我的项目"

# 查看项目结构
tree projects/my_project/
```

### 2. 添加需求

```bash
# 添加用户需求
cat > projects/my_project/input/feedback/feature_001.md << 'EOF'
# 功能需求：用户登录

作为 注册用户
我想要 通过用户名密码登录
以便于 访问我的个人账户

## 验收标准
- 支持用户名密码登录
- 支持记住登录状态
- 登录失败有明确提示
EOF
```

### 3. 运行智能体

```bash
# 为特定项目运行智能体
python3 scripts/start_agents.py --project my_project

# 或使用管理脚本
python3 scripts/manage_agents.py run RequirementAgent --project my_project
```

### 4. 查看输出

```bash
# 查看项目输出
ls -lh projects/my_project/output/

# 查看需求文档
cat projects/my_project/output/requirements/user_requirements.md

# 查看设计文档
cat projects/my_project/output/design/architecture.md
```

### 5. 查看日志

```bash
# 查看项目日志
python3 scripts/view_logs.py agents --project my_project

# 实时跟踪
python3 scripts/view_logs.py tail --project my_project
```

---

## 📊 项目配置

### project.json 结构

```json
{
  "name": "项目名称",
  "created_at": "创建时间",
  "updated_at": "最后更新",
  "status": "项目状态",
  "goal": "项目目标",
  "workflow_results": [
    {
      "timestamp": "执行时间",
      "success": true,
      "avg_quality": 0.85,
      "completed_stages": 8,
      "total_stages": 8
    }
  ]
}
```

### 项目状态

| 状态 | 说明 |
|------|------|
| created | 已创建 |
| running | 运行中 |
| completed | 已完成 |
| paused | 已暂停 |
| failed | 失败 |

---

## 🔄 多项目管理

### 并行项目

可以同时运行多个项目：

```bash
# 项目 A 在后台运行
python3 scripts/start_agents.py --project project_a &

# 项目 B 在后台运行
python3 scripts/start_agents.py --project project_b &

# 查看两个项目状态
python3 scripts/project_manager.py status project_a
python3 scripts/project_manager.py status project_b
```

### 项目隔离

每个项目完全隔离：
- 独立的输入目录
- 独立的输出目录
- 独立的日志文件
- 独立的配置文件

---

## 📖 最佳实践

### 项目命名

- ✅ 使用小写字母
- ✅ 使用下划线分隔
- ✅ 名称简短有意义
- ❌ 避免空格和特殊字符

示例：
- ✅ `order_system`
- ✅ `user_management`
- ❌ `Order System`
- ❌ `user-management`

### 项目组织

- ✅ 一个项目一个目标
- ✅ 及时清理完成的项目
- ✅ 定期导出重要项目
- ✅ 使用有意义的文件名

### 输入管理

- ✅ 按类型组织输入文件
- ✅ 使用有意义的文件名
- ✅ 添加时间戳
- ✅ 记录需求来源

示例：
```
input/feedback/
├── 20260321_001_user_login.md
├── 20260321_002_user_register.md
└── 20260322_001_order_search.md
```

---

## 🔧 高级用法

### 项目批处理

```bash
# 批量创建项目
for project in project_a project_b project_c; do
  python3 scripts/project_manager.py create $project --goal "项目$project"
done

# 批量导出项目
for project in $(python3 scripts/project_manager.py list | tail -n +4 | awk '{print $1}'); do
  python3 scripts/project_manager.py export $project
done
```

### 项目归档

```bash
# 导出并删除旧项目
python3 scripts/project_manager.py export old_project --output old_project_archive.zip
python3 scripts/project_manager.py delete old_project --confirm
```

---

## 📖 相关文档

- [README.md](../README.md) - 项目说明
- [SCRIPTS_GUIDE.md](./SCRIPTS_GUIDE.md) - 脚本使用指南
- [PROJECT_FINAL_STATUS.md](./PROJECT_FINAL_STATUS.md) - 项目状态

---

**状态：** ✅ 完整  
**版本：** 2.1  
**最后更新：** 2026-03-21
