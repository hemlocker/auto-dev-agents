# Coordinator 智能体知识库

## 角色定位

Coordinator（协调者）是 PDCA 循环的核心调度者，负责：
- 任务分配和流程控制
- 智能体间协调
- 质量门禁检查
- 异常处理和恢复

---

## PDCA 循环标准流程

### PLAN（计划阶段）
```
输入：input/ (用户反馈、会议、邮件、工单)
处理：RequirementAgent → 需求文档
处理：DesignAgent → 设计文档
输出：output/requirements/, output/design/
```

### DO（执行阶段）
```
输入：output/design/
处理：DevelopmentAgent → 源代码
处理：TestingAgent → 测试代码 + 测试报告
处理：DeploymentAgent → 部署配置
输出：output/src/, output/tests/, output/deploy/
```

### CHECK（检查阶段）
```
输入：output/
处理：OperationsAgent → 运维报告 + 问题工单
处理：MonitorAgent → 质量报告 + 问题工单
输出：output/operations/, output/monitor/, input/tickets/
```

### ACT（改进阶段）
```
输入：input/tickets/
处理：OptimizerAgent → 优化方案 + 新工单
输出：output/optimizer/, input/tickets/
触发：新一轮 PDCA 循环
```

---

## 智能体依赖关系

```
RequirementAgent
    ↓
DesignAgent
    ↓
DevelopmentAgent
    ↓
TestingAgent
    ↓
DeploymentAgent
    ↓
OperationsAgent → tickets/
    ↓
MonitorAgent → tickets/
    ↓
OptimizerAgent → tickets/ → 触发新一轮
```

---

## 质量门禁

每个阶段完成后，必须检查：

### PLAN 阶段
- [ ] 需求文档完整性 ≥ 95%
- [ ] 设计文档完整性 ≥ 90%
- [ ] 需求追踪矩阵覆盖率 = 100%

### DO 阶段
- [ ] 代码编译通过
- [ ] 测试通过率 ≥ 80%
- [ ] 部署配置有效

### CHECK 阶段
- [ ] 质量评分 ≥ 80
- [ ] P0 问题数 = 0
- [ ] 运维文档完整

### ACT 阶段
- [ ] 优化方案已生成
- [ ] 工单已创建
- [ ] 执行日志已记录

---

## 异常处理

### 任务失败
1. 记录失败原因到日志
2. 将问题写入 input/tickets/
3. 根据严重程度决定是否继续

### 质量不达标
1. 记录问题详情
2. 通知相关智能体修复
3. 重新执行当前阶段

### 依赖缺失
1. 检查前置条件
2. 自动补充缺失内容
3. 如果无法自动补充，暂停并通知

---

## 调度策略

### 串行执行
```
Requirement → Design → Development → Testing → Deployment → Operations → Monitor → Optimizer
```

### 并行执行（未来支持）
```
        ┌→ Development → Testing ─┐
Design →├                          ├→ Deployment
        └→ Documentation ─────────┘
```

---

## 最佳实践

1. **始终检查输入** - 确保前置条件满足
2. **记录详细日志** - 便于问题追溯
3. **质量优先** - 不达标则不继续
4. **形成闭环** - 确保问题反馈触发改进

---

## 常见问题

### Q: 如何处理循环依赖？
A: 严格按照 PDCA 顺序执行，禁止跨阶段依赖。

### Q: 如何处理超时？
A: 设置合理的 timeout，超时后记录日志并通知。

### Q: 如何恢复中断的流程？
A: 读取 pdca_state.json，从上次中断点继续。

---

## 相关文件

- 提示词：`prompts/coordinator/system.md`
- 检查清单：`knowledge/checklists/`
- 配置：`config.yaml`