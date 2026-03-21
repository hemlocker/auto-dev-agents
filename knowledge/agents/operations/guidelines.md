# Operations 智能体知识库

## 角色定位

Operations（运维专家）负责：
- 系统监控检查
- 健康检查脚本
- 运维文档编写
- 问题发现和反馈

---

## 健康检查项

### 服务状态检查
- Docker 容器运行状态
- 服务端口可用性
- 进程存活检查

### 资源检查
- CPU 使用率 (< 80%)
- 内存使用率 (< 80%)
- 磁盘使用率 (< 80%)

### 应用检查
- API 响应时间 (< 1s)
- 数据库连接
- 错误日志检测

---

## 健康检查脚本模板

```bash
#!/bin/bash

# 健康检查报告
REPORT_FILE="health_report_$(date +%Y%m%d_%H%M%S).json"

# 检查服务状态
check_service() {
  local service=$1
  if systemctl is-active --quiet $service; then
    echo "✅ $service: 运行中"
  else
    echo "❌ $service: 未运行"
  fi
}

# 检查端口
check_port() {
  local port=$1
  if netstat -tuln | grep -q ":$port "; then
    echo "✅ 端口 $port: 开放"
  else
    echo "❌ 端口 $port: 未开放"
  fi
}

# 检查资源
check_resources() {
  # CPU
  CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}')
  echo "CPU使用率: $CPU_USAGE%"
  
  # 内存
  MEM_USAGE=$(free | grep Mem | awk '{print ($3/$2) * 100}')
  echo "内存使用率: $MEM_USAGE%"
  
  # 磁盘
  DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}')
  echo "磁盘使用率: $DISK_USAGE"
}

# 执行检查
echo "=== 健康检查报告 ==="
check_service docker
check_port 3000
check_resources
```

---

## 运维文档模板

```markdown
# 运维文档

## 1. 系统概述
- 架构说明
- 组件列表
- 依赖关系

## 2. 部署说明
- 环境要求
- 部署步骤
- 配置说明

## 3. 监控配置
- 监控指标
- 告警规则
- 日志位置

## 4. 运维操作
- 启动/停止
- 备份/恢复
- 故障排查

## 5. 常见问题
- 问题1: xxx
  - 原因: xxx
  - 解决: xxx
```

---

## 问题反馈

发现问题时，写入 `input/tickets/`:

```markdown
# 问题工单

**发现时间**: {timestamp}
**优先级**: P0/P1/P2
**类型**: 运维问题

## 问题描述
{详细描述}

## 影响
{影响范围}

## 建议
{解决方案}
```

---

## 检查清单

- [ ] 服务状态正常
- [ ] 资源使用正常
- [ ] API 可访问
- [ ] 运维文档完整
- [ ] 问题已反馈

---

**相关文件**
- 提示词：`prompts/operations/system.md`
- 检查清单：`knowledge/checklists/operations-checklist.md`