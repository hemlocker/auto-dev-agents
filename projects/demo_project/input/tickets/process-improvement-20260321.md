# 流程改进工单

**项目**: demo_project  
**创建日期**: 2026-03-21 18:33  
**创建智能体**: optimizer  
**PDCA 阶段**: ACT  
**工单类型**: 流程改进  

---

## 1. 改进背景

在本次质量检查中，发现以下流程性问题需要系统性改进：

1. **代码生成流程缺陷**: 模板变量未正确替换，导致异常目录产生
2. **PDCA 流程不完整**: 优化器阶段输出缺失
3. **质量门禁缺失**: 缺少自动化质量检查机制

---

## 2. 改进目标

| 改进项 | 当前状态 | 目标状态 | 完成时间 |
|-------|---------|---------|---------|
| 代码生成验证 | 无 | 自动生成后验证 | 2026-03-28 |
| PDCA 流程完整性 | 部分缺失 | 完整执行 4 阶段 | 2026-03-28 |
| 质量门禁 | 无 | CI/CD 集成 | 2026-04-11 |

---

## 3. 改进方案

### 3.1 代码生成流程改进

#### 问题描述
代码生成智能体在使用模板变量时，未正确替换所有变量，导致生成异常目录名 `{backend`。

#### 改进措施

**步骤 1: 添加模板变量验证**

在代码生成智能体的工作流程中添加验证步骤：

```yaml
# 智能体配置示例
steps:
  - name: generate_code
    action: generate
    template: project-template
    
  - name: validate_output
    action: validate
    checks:
      - no_unreplaced_variables: true
      - directory_structure_valid: true
      - no_special_characters: true
      
  - name: report_issues
    action: notify
    on_failure: true
```

**步骤 2: 验证脚本**

```bash
#!/bin/bash
# validate-output.sh - 验证代码生成输出

PROJECT_DIR="$1"
ERRORS=0

# 检查未替换的模板变量
if find "$PROJECT_DIR" -type d -name "*{{*}}" -o -name "*}}*" -o -name "*{*" -o -name "*}*"; then
    echo "❌ 发现未替换的模板变量或特殊字符目录"
    find "$PROJECT_DIR" -type d -name "*{{*}" -o -name "*}}*" -o -name "*{*" -o -name "*}*"
    ERRORS=$((ERRORS + 1))
fi

# 检查目录结构
if [ ! -d "$PROJECT_DIR/src/backend" ]; then
    echo "❌ 缺少必需的 backend 目录"
    ERRORS=$((ERRORS + 1))
fi

if [ ! -d "$PROJECT_DIR/src/frontend" ]; then
    echo "❌ 缺少必需的 frontend 目录"
    ERRORS=$((ERRORS + 1))
fi

# 输出结果
if [ $ERRORS -eq 0 ]; then
    echo "✅ 代码生成验证通过"
    exit 0
else
    echo "❌ 代码生成验证失败，发现 $ERRORS 个问题"
    exit 1
fi
```

**步骤 3: 集成到智能体流程**

在代码生成智能体配置中添加验证步骤，验证失败时自动回滚并通知。

#### 验收标准
- [ ] 验证脚本可检测未替换的模板变量
- [ ] 验证脚本可检测目录结构问题
- [ ] 智能体流程集成验证步骤
- [ ] 验证失败时自动回滚

---

### 3.2 PDCA 流程完整性改进

#### 问题描述
optimizer/ 目录为空，表明 PDCA 流程中的 OPTIMIZE 阶段未正确执行。

#### 改进措施

**步骤 1: 检查 PDCA 流程配置**

```json
// project-config.json
{
  "pdca": {
    "enabled": true,
    "stages": {
      "PLAN": {
        "agent": "planner",
        "required": true
      },
      "DO": {
        "agent": "developer",
        "required": true
      },
      "CHECK": {
        "agent": "monitor",
        "required": true
      },
      "ACT": {
        "agent": "optimizer",
        "required": true
      }
    },
    "validation": {
      "check_output_directory": true,
      "min_files_per_stage": 1
    }
  }
}
```

**步骤 2: 添加流程验证**

在 PDCA 流程执行完成后，验证每个阶段的输出：

```bash
#!/bin/bash
# validate-pdca.sh - 验证 PDCA 流程完整性

PROJECT_DIR="$1"

echo "验证 PDCA 流程完整性..."

# 检查各阶段输出
STAGES=("requirements" "design" "src" "tests" "deploy" "operations" "optimizer" "monitor")

for stage in "${STAGES[@]}"; do
    STAGE_DIR="$PROJECT_DIR/output/$stage"
    if [ ! -d "$STAGE_DIR" ]; then
        echo "❌ 缺少阶段目录：$stage"
        continue
    fi
    
    FILE_COUNT=$(find "$STAGE_DIR" -type f | wc -l)
    if [ $FILE_COUNT -eq 0 ]; then
        echo "⚠️  阶段目录为空：$stage"
    else
        echo "✅ 阶段 $stage: $FILE_COUNT 个文件"
    fi
done
```

**步骤 3: 配置智能体触发链**

确保 PDCA 各阶段智能体按顺序触发：

```yaml
# 智能体触发配置
agent_chain:
  - name: planner
    trigger: manual
    next: developer
    
  - name: developer
    trigger: planner_complete
    next: monitor
    
  - name: monitor
    trigger: developer_complete
    next: optimizer
    
  - name: optimizer
    trigger: monitor_complete
    next: null
```

#### 验收标准
- [ ] PDCA 配置包含所有 4 个阶段
- [ ] 各阶段智能体正确触发
- [ ] 流程验证脚本可检测缺失阶段
- [ ] optimizer/ 目录有输出文件

---

### 3.3 质量门禁建设

#### 问题描述
项目缺少自动化质量检查机制，依赖人工检查容易遗漏问题。

#### 改进措施

**步骤 1: 定义质量门禁指标**

```yaml
# quality-gates.yml
gates:
  code_quality:
    - eslint: pass
    - no_critical_issues: true
    
  test_coverage:
    - unit_tests: ">=80%"
    - e2e_tests: ">=50%"
    
  documentation:
    - readme: required
    - api_docs: required
    
  security:
    - no_high_vulnerabilities: true
    - https_enabled: true
    
  operations:
    - backup_configured: true
    - monitoring_configured: true
    - logging_configured: true
```

**步骤 2: 创建质量检查脚本**

```bash
#!/bin/bash
# quality-gate-check.sh - 质量门禁检查

set -e

PROJECT_DIR="$1"
FAILED=0

echo "🚪 执行质量门禁检查..."

# 代码质量检查
echo "📝 代码质量检查..."
if ! npm run lint; then
    echo "❌ ESLint 检查失败"
    FAILED=$((FAILED + 1))
fi

# 测试覆盖率检查
echo "🧪 测试覆盖率检查..."
COVERAGE=$(npm run test:coverage -- --reporter=text-summary | grep "All files" | awk '{print $4}' | sed 's/%//')
if (( $(echo "$COVERAGE < 80" | bc -l) )); then
    echo "❌ 测试覆盖率不足：${COVERAGE}% < 80%"
    FAILED=$((FAILED + 1))
fi

# 文档检查
echo "📚 文档检查..."
if [ ! -f "$PROJECT_DIR/README.md" ]; then
    echo "❌ 缺少 README.md"
    FAILED=$((FAILED + 1))
fi

# 安全检查
echo "🔒 安全检查..."
if npm audit --audit-level=high 2>&1 | grep -q "found.*high"; then
    echo "❌ 发现高危安全漏洞"
    FAILED=$((FAILED + 1))
fi

# 运维检查
echo "🔧 运维检查..."
if ! grep -q "logging:" "$PROJECT_DIR/deploy/docker-compose.yml"; then
    echo "❌ 未配置日志轮转"
    FAILED=$((FAILED + 1))
fi

if ! grep -q "restart:" "$PROJECT_DIR/deploy/docker-compose.yml"; then
    echo "❌ 未配置重启策略"
    FAILED=$((FAILED + 1))
fi

# 输出结果
echo ""
if [ $FAILED -eq 0 ]; then
    echo "✅ 质量门禁检查通过"
    exit 0
else
    echo "❌ 质量门禁检查失败，$FAILED 项未通过"
    exit 1
fi
```

**步骤 3: 集成到 CI/CD**

```yaml
# .github/workflows/quality-gate.yml
name: Quality Gate

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  quality-gate:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          
      - name: Install dependencies
        run: npm ci
        
      - name: Run quality gate
        run: ./quality-gate-check.sh
        
      - name: Upload quality report
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: quality-report
          path: output/monitor/
```

#### 验收标准
- [ ] 质量门禁指标已定义
- [ ] 质量检查脚本可执行
- [ ] CI/CD 集成质量门禁
- [ ] 质量不达标时阻止合并

---

## 4. 实施计划

| 改进项 | 开始日期 | 结束日期 | 负责人 | 状态 |
|-------|---------|---------|--------|------|
| 代码生成验证 | 2026-03-22 | 2026-03-25 | 开发负责人 | 待执行 |
| PDCA 流程完整性 | 2026-03-22 | 2026-03-28 | 系统管理员 | 待执行 |
| 质量门禁建设 | 2026-04-01 | 2026-04-11 | 技术负责人 | 待执行 |

---

## 5. 预期效果

| 指标 | 改进前 | 改进后 | 提升 |
|-----|-------|-------|------|
| 代码生成错误率 | 5% | <1% | 80%↓ |
| PDCA 流程完整性 | 75% | 100% | 33%↑ |
| 质量问题发现时间 | 周级 | 分钟级 | 1000x↑ |
| 综合质量评分 | 88.3 | 95+ | 7.5%↑ |

---

## 6. 相关文件

- **优化方案**: `output/optimizer/optimization-plan-20260321.md`
- **实施工单**: `input/tickets/optimizer-implementation-20260321.md`
- **验证脚本**: `scripts/validate-output.sh` (待创建)
- **质量门禁**: `scripts/quality-gate-check.sh` (待创建)

---

## 7. 审批流程

| 角色 | 姓名 | 审批状态 | 日期 |
|-----|------|---------|------|
| 项目经理 | 待分配 | 待审批 | - |
| 技术负责人 | 待分配 | 待审批 | - |
| 质量负责人 | 待分配 | 待审批 | - |

---

**工单状态**: 新建  
**优先级**: 中  
**预计工时**: 16 小时  
**实际工时**: 待填写

---

*本工单触发流程改进的 PDCA 循环*
