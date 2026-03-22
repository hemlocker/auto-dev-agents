# 新工单：质量门禁建设

**项目**: demo_project  
**创建时间**: 2026-03-22  
**创建智能体**: optimizer  
**PDCA 阶段**: PLAN  
**工单类型**: 质量建设  
**优先级**: P1

---

## 1. 工单概述

基于优化分析发现的质量管理缺失问题，建立自动化质量门禁机制，确保代码质量、测试覆盖率、文档完整性等指标达标后方可进入下一阶段。

**当前状态**: 无质量门禁，依赖人工检查  
**目标状态**: 自动化质量检查，不达标自动阻断  
**截止时间**: 2026-04-18

---

## 2. 问题背景

### 2.1 当前质量问题

1. **测试通过率低**: 56.2%，未达到 80% 目标
2. **代码质量未知**: 无 ESLint 强制检查
3. **文档不完整**: 需求追踪矩阵未同步
4. **运维配置缺失**: 健康检查、日志轮转等未配置

### 2.2 缺少质量门禁的后果

- 低质量代码可进入生产
- 测试覆盖率无保障
- 文档与实际脱节
- 运维问题发现滞后

---

## 3. 建设任务

### 任务 1: 定义质量门禁指标

**描述**: 定义各阶段的质量门禁指标

**产出文件**: `config/quality-gates.yml`

**内容示例**:
```yaml
gates:
  # 代码质量门禁
  code_quality:
    eslint:
      enabled: true
      max_warnings: 10
      max_errors: 0
    
    complexity:
      max_cyclomatic: 10
      max_function_length: 50
  
  # 测试质量门禁
  test_quality:
    unit_tests:
      enabled: true
      min_pass_rate: 80%
    
    coverage:
      enabled: true
      min_lines: 80%
      min_branches: 70%
      min_functions: 80%
    
    e2e_tests:
      enabled: true
      min_pass_rate: 90%
  
  # 文档质量门禁
  documentation:
    readme:
      required: true
      min_length: 500
    
    api_docs:
      required: true
    
    requirement_trace:
      required: true
      min_sync_rate: 90%
  
  # 安全门禁
  security:
    npm_audit:
      enabled: true
      max_low: 10
      max_moderate: 5
      max_high: 0
      max_critical: 0
    
    secrets_scan:
      enabled: true
  
  # 运维门禁
  operations:
    healthcheck:
      required: true
    
    logging:
      required: true
      max_size: 10m
      max_files: 5
    
    backup:
      required: true
      frequency: daily
    
    restart_policy:
      required: true
```

**验收**:
- [ ] 质量门禁指标已定义
- [ ] 指标合理可测量
- [ ] 获得团队认可

**负责人**: 技术负责人  
**工时**: 4 小时

---

### 任务 2: 创建质量检查脚本

**描述**: 创建可执行的质量检查脚本

**产出文件**: `scripts/quality-gate-check.sh`

**脚本功能**:
1. 执行 ESLint 检查
2. 运行测试并检查通过率
3. 检查测试覆盖率
4. 检查文档完整性
5. 执行安全扫描
6. 检查运维配置
7. 生成质量报告

**脚本示例**:
```bash
#!/bin/bash
set -e

PROJECT_DIR="$1"
REPORT_DIR="$PROJECT_DIR/output/monitor"
FAILED=0
WARNINGS=0

echo "🚪 执行质量门禁检查..."
echo "================================"

# 1. 代码质量检查
echo "📝 代码质量检查..."
if ! npm run lint 2>&1 | tee "$REPORT_DIR/lint-report.txt"; then
    echo "❌ ESLint 检查失败"
    FAILED=$((FAILED + 1))
else
    echo "✅ ESLint 检查通过"
fi

# 2. 测试通过率检查
echo "🧪 测试通过率检查..."
TEST_OUTPUT=$(npm test 2>&1 | tee "$REPORT_DIR/test-report.txt")
PASS_RATE=$(echo "$TEST_OUTPUT" | grep "Passing" | awk '{print $2}' | sed 's/(//')
if (( $(echo "$PASS_RATE < 80" | bc -l) )); then
    echo "❌ 测试通过率不足：${PASS_RATE}% < 80%"
    FAILED=$((FAILED + 1))
else
    echo "✅ 测试通过率达标：${PASS_RATE}%"
fi

# 3. 测试覆盖率检查
echo "📊 测试覆盖率检查..."
COVERAGE_OUTPUT=$(npm run test:coverage 2>&1 | tee "$REPORT_DIR/coverage-report.txt")
LINE_COVERAGE=$(echo "$COVERAGE_OUTPUT" | grep "All files" | awk '{print $4}' | sed 's/%//')
if (( $(echo "$LINE_COVERAGE < 80" | bc -l) )); then
    echo "❌ 代码覆盖率不足：${LINE_COVERAGE}% < 80%"
    FAILED=$((FAILED + 1))
else
    echo "✅ 代码覆盖率达标：${LINE_COVERAGE}%"
fi

# 4. 文档检查
echo "📚 文档检查..."
if [ ! -f "$PROJECT_DIR/README.md" ]; then
    echo "❌ 缺少 README.md"
    FAILED=$((FAILED + 1))
else
    WORD_COUNT=$(wc -w < "$PROJECT_DIR/README.md")
    if [ $WORD_COUNT -lt 500 ]; then
        echo "❌ README.md 内容不足 ($WORD_COUNT < 500 词)"
        FAILED=$((FAILED + 1))
    else
        echo "✅ README.md 检查通过 ($WORD_COUNT 词)"
    fi
fi

# 5. 安全检查
echo "🔒 安全检查..."
if npm audit --audit-level=high 2>&1 | grep -q "found.*high"; then
    echo "❌ 发现高危安全漏洞"
    FAILED=$((FAILED + 1))
else
    echo "✅ 安全检查通过"
fi

# 6. 运维配置检查
echo "🔧 运维配置检查..."
if ! grep -q "healthcheck:" "$PROJECT_DIR/deploy/docker-compose.yml"; then
    echo "❌ 未配置健康检查"
    FAILED=$((FAILED + 1))
else
    echo "✅ 健康检查已配置"
fi

if ! grep -q "logging:" "$PROJECT_DIR/deploy/docker-compose.yml"; then
    echo "❌ 未配置日志轮转"
    FAILED=$((FAILED + 1))
else
    echo "✅ 日志轮转已配置"
fi

# 输出总结
echo ""
echo "================================"
echo "质量门禁检查结果:"
echo "  失败项：$FAILED"
echo "  警告项：$WARNINGS"
echo "================================"

if [ $FAILED -eq 0 ]; then
    echo "✅ 质量门禁检查通过"
    exit 0
else
    echo "❌ 质量门禁检查失败，$FAILED 项未通过"
    exit 1
fi
```

**验收**:
- [ ] 脚本可执行
- [ ] 检查项完整
- [ ] 报告生成正确

**负责人**: 技术负责人  
**工时**: 8 小时

---

### 任务 3: 创建质量报告生成器

**描述**: 创建质量报告自动生成脚本

**产出文件**: `scripts/generate-quality-report.js`

**报告内容**:
- 质量评分（百分制）
- 各维度得分
- 问题清单
- 改进建议
- 历史趋势

**验收**:
- [ ] 报告自动生成
- [ ] 评分计算准确
- [ ] 报告格式规范

**负责人**: 技术负责人  
**工时**: 6 小时

---

### 任务 4: 集成到 CI/CD 流程

**描述**: 将质量门禁集成到 CI/CD 流程

**产出文件**: `.github/workflows/quality-gate.yml`

**流程设计**:
```yaml
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
        run: ./scripts/quality-gate-check.sh
        
      - name: Generate quality report
        run: node scripts/generate-quality-report.js
        
      - name: Upload quality report
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: quality-report
          path: output/monitor/
          
      - name: Notify on failure
        if: failure()
        run: |
          # 发送失败通知
          echo "质量门禁检查失败，请修复后重新提交"
```

**验收**:
- [ ] CI/CD 配置正确
- [ ] 质量不达标时构建失败
- [ ] 报告自动上传

**负责人**: 系统管理员  
**工时**: 4 小时

---

### 任务 5: 集成到 PDCA 流程

**描述**: 将质量门禁集成到 PDCA 各阶段

**集成点**:
1. **PLAN → DO**: 需求文档质量检查
2. **DO → CHECK**: 代码质量检查
3. **CHECK → ACT**: 测试质量检查
4. **ACT → PLAN**: 整体质量评分

**产出文件**: `scripts/pdca-quality-gates.sh`

**验收**:
- [ ] 各阶段转换有质量检查
- [ ] 质量不达标时阻断流转

**负责人**: 系统管理员  
**工时**: 4 小时

---

### 任务 6: 质量 Dashboard 建设

**描述**: 创建质量数据可视化 Dashboard

**展示内容**:
- 质量评分趋势
- 测试通过率趋势
- 代码覆盖率趋势
- 问题分布
- 修复进度

**实现方式**:
- 方案 1: Grafana Dashboard
- 方案 2: 静态 HTML 报告
- 方案 3: 飞书多维表格

**验收**:
- [ ] Dashboard 可访问
- [ ] 数据实时更新
- [ ] 图表清晰易懂

**负责人**: 技术负责人  
**工时**: 8 小时

---

## 4. 实施计划

| 任务 | 开始日期 | 结束日期 | 负责人 | 状态 |
|-----|---------|---------|--------|------|
| 任务 1: 定义质量指标 | 2026-04-11 | 2026-04-12 | 技术负责人 | 待开始 |
| 任务 2: 创建检查脚本 | 2026-04-12 | 2026-04-14 | 技术负责人 | 待开始 |
| 任务 3: 报告生成器 | 2026-04-14 | 2026-04-15 | 技术负责人 | 待开始 |
| 任务 4: CI/CD 集成 | 2026-04-15 | 2026-04-16 | 系统管理员 | 待开始 |
| 任务 5: PDCA 集成 | 2026-04-16 | 2026-04-17 | 系统管理员 | 待开始 |
| 任务 6: Dashboard 建设 | 2026-04-17 | 2026-04-18 | 技术负责人 | 待开始 |

---

## 5. 验收标准

### 5.1 功能验收
- [ ] 质量检查脚本可执行
- [ ] 质量报告自动生成
- [ ] CI/CD 集成成功
- [ ] Dashboard 可访问

### 5.2 质量验收
- [ ] 质量门禁指标合理
- [ ] 检查项覆盖全面
- [ ] 误报率低

### 5.3 流程验收
- [ ] 质量不达标时自动阻断
- [ ] 通知机制正常
- [ ] 修复后自动重检

---

## 6. 预期效果

| 指标 | 建设前 | 建设后 | 提升 |
|-----|-------|-------|------|
| 质量问题发现时间 | 周级 | 分钟级 | 1000x↑ |
| 质量检查覆盖率 | 人工抽样 | 100% | 100%↑ |
| 低质量代码流入 | 时有发生 | 0 | 100%↓ |
| 质量评分 | 88.3 | ≥95 | 7.5%↑ |

---

## 7. 关联工单

- **来源**: 优化分析报告 - 优化项 8
- **关联**: OPT-001 (测试质量修复)
- **依赖**: OPT-001 完成后效果更佳

---

## 8. 状态跟踪

| 日期 | 状态 | 备注 |
|-----|------|------|
| 2026-03-22 | 新建 | 工单创建 |

---

**工单状态**: 新建  
**优先级**: P1  
**预计工时**: 34 小时  
**实际工时**: 待填写

---

*本工单由 optimizer 智能体基于优化分析报告自动生成*
