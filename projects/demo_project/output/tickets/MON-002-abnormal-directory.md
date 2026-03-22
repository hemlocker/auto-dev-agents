# Ticket: MON-002 - 异常目录未清理

## 问题描述
项目源码目录中存在异常目录 `output/src/{backend`，这是模板变量未正确替换导致的，严重影响项目结构规范性。

## 问题详情

### 异常目录信息
- **路径**: `/root/.openclaw/workspace/projects/auto-dev-agents/projects/demo_project/output/src/{backend`
- **创建时间**: 2026-03-21 18:18
- **目录内容**: 包含完整的 backend 代码（node_modules、src、config 等）

### 问题根源
这是代码生成过程中模板变量未正确替换导致的：
- 预期：`output/src/backend/`
- 实际：`output/src/{backend` (模板变量 `{backend}` 未替换)

### 影响范围
- 项目目录结构混乱
- 可能影响构建脚本路径解析
- 降低项目专业性
- 在之前质量报告中已被指出，但至今未修复

### 历史追踪
- **2026-03-21 18:30**: 首次在 quality-report-20260321.md 中被指出
- **2026-03-21 21:33**: optimizer 在优化方案中列为 P0 问题
- **2026-03-22 00:15**: 本次检查发现仍未修复

## 优先级
🔴 **P0 - 严重** (重复出现问题，显示执行力不足)

## 解决方案

### 立即执行
```bash
# 删除异常目录
rm -rf "/root/.openclaw/workspace/projects/auto-dev-agents/projects/demo_project/output/src/{backend"

# 验证删除结果
ls -la /root/.openclaw/workspace/projects/auto-dev-agents/projects/demo_project/output/src/
```

### 验证步骤
1. 确认异常目录已删除
2. 确认正常 backend 目录 (`output/src/backend/`) 未受影响
3. 检查是否有其他异常目录

### 流程改进
1. 在代码生成智能体中添加目录验证步骤
2. 创建 validate-output.sh 脚本，检查输出目录合法性
3. 在 PDCA 流程中添加质量检查点

## 验收标准
- [ ] 异常目录 `{backend` 已删除
- [ ] 正常 backend 目录完整无损
- [ ] 添加目录验证脚本
- [ ] 代码生成流程增加模板变量校验

## 发现时间
2026-03-22 00:15 (首次发现：2026-03-21 18:30)

## 发现智能体
monitor (PDCA: CHECK)

## 状态
📋 待修复

## 备注
此问题在上周质量报告中已被指出，optimizer 也将其列为 P0 问题，但至今未修复。建议：
1. 检查任务分配和跟进机制
2. 建立问题修复 SLA（P0 问题 24 小时内修复）
3. 在实施跟踪表中更新状态
