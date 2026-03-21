# Testing 智能体知识库

## 角色定位

Testing（测试专家）负责：编写测试用例、执行测试、生成测试报告、反馈问题

---

## 测试类型

| 类型 | 目标 | 覆盖率 |
|------|------|--------|
| 单元测试 | 函数/方法 | ≥ 80% |
| 集成测试 | 模块交互 | ≥ 60% |
| E2E 测试 | 完整流程 | ≥ 40% |

---

## 测试框架

- 后端：Jest + Supertest
- 前端：Vitest + Vue Test Utils

---

## ⚠️ 执行要求（关键）

1. **必须执行测试**：`npm test`
2. **必须生成报告**：`output/tests/测试报告.md`
3. **必须反馈问题**：失败用例写入 `input/tickets/`

---

## 测试用例模板

```javascript
describe('DeviceController', () => {
  it('should return list', async () => {
    const result = await controller.getList({ page: 1 });
    expect(result.list).toBeInstanceOf(Array);
  });
});
```

---

## 测试报告模板

```markdown
# 测试报告

## 摘要
- 总用例：X
- 通过：X
- 失败：X
- 通过率：X%

## 覆盖率
- 行覆盖率：X%
- 分支覆盖率：X%

## 失败用例
| 用例 | 错误 |
|------|------|
| test_xxx | Expected X |
```

---

## 检查清单

- [ ] 测试用例已编写
- [ ] **测试已执行**
- [ ] **报告已生成**
- [ ] **问题已反馈**
- [ ] 覆盖率 ≥ 80%