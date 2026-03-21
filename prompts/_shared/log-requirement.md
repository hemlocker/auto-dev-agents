# 日志写入规范

每个智能体执行完成后，必须生成执行日志到项目目录。

---

## 日志位置

```
projects/{project_name}/logs/agents/{agent_name}-{timestamp}.log
```

**示例：**
```
projects/demo_project/logs/agents/requirement-20260321-192000.log
projects/demo_project/logs/agents/development-20260321-193000.log
```

---

## 日志格式

```markdown
# {智能体名称} 执行日志

**项目**: {project_name}
**执行时间**: {ISO时间戳}
**阶段**: {PDCA阶段}

---

## 任务

{任务描述}

---

## 执行步骤

1. {步骤1}
2. {步骤2}
3. ...

---

## 输出文件

| 文件 | 说明 |
|------|------|
| {file1} | {desc1} |
| {file2} | {desc2} |

---

## 结果

- 状态: {成功/失败}
- 详情: {详细说明}

---

## 问题/建议

- {问题1}
- {建议1}

---

**执行时长**: {duration}
```

---

## 写入命令

```bash
# 创建日志文件
cat > projects/{project}/logs/agents/{agent}-{timestamp}.log << 'EOF'
{日志内容}
EOF
```

---

## 强制要求

在完成任务前，必须：

1. [ ] 生成执行日志
2. [ ] 写入到 `logs/agents/` 目录
3. [ ] 日志包含完整执行过程