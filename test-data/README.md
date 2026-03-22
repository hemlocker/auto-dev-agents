# 标准测试输入数据

> 用于验证智能体运行的标准数据集，分为三个阶段

---

## 数据结构

```
test-data/
├── README.md                    # 本文件
├── stage-1-initial/             # 阶段1：初始需求
│   ├── project.json             # 项目配置
│   └── input/
│       └── feedback/
│           └── project_goal.md  # 项目目标
├── stage-2-features/            # 阶段2：功能扩展
│   └── input/
│       └── feedback/
│           ├── feature-1.md     # 新功能需求1
│           └── feature-2.md     # 新功能需求2
└── stage-3-issues/              # 阶段3：问题反馈
    └── input/
        └── tickets/
            ├── issue-1.md       # 问题工单1
            └── issue-2.md       # 问题工单2
```

---

## 阶段说明

### 阶段1：初始需求

**目的**: 验证智能体从零开始创建项目的能力

**输入**:
- 项目目标：设备管理系统
- 核心功能：CRUD

**预期输出**:
- 完整的需求文档
- 系统设计
- 可运行的代码
- 测试用例
- 部署配置

---

### 阶段2：功能扩展

**目的**: 验证智能体增量开发能力

**输入**:
- 新功能需求：导入导出、打印功能

**预期输出**:
- 新功能实现
- 更新的测试用例
- 更新的文档

---

### 阶段3：问题反馈

**目的**: 验证智能体处理问题和优化的能力

**输入**:
- 问题工单：测试流程缺失、性能问题

**预期输出**:
- 问题分析
- 修复方案
- 优化计划

---

## 使用方式

```bash
# 阶段1测试
cp -r test-data/stage-1-initial/* projects/test-project/
python3 scripts/workflow.py -p test-project --start

# 阶段2测试（基于阶段1）
cp -r test-data/stage-2-features/input/* projects/test-project/input/
python3 scripts/workflow.py -p test-project --stages development,testing

# 阶段3测试（基于阶段2）
cp -r test-data/stage-3-issues/input/* projects/test-project/input/
python3 scripts/workflow.py -p test-project --stages optimizer
```

---

## 验收标准

| 阶段 | 检查项 | 预期结果 |
|------|--------|----------|
| 1 | 需求文档 | 包含用户故事和验收标准 |
| 1 | 设计文档 | 包含架构和数据库设计 |
| 1 | 可运行代码 | npm run dev 可启动 |
| 1 | 测试覆盖 | ≥70% |
| 2 | 新功能实现 | 导入导出功能可用 |
| 2 | 回归测试 | 原有功能未破坏 |
| 3 | 问题修复 | 问题得到解决 |
| 3 | 优化建议 | 有具体改进方案 |