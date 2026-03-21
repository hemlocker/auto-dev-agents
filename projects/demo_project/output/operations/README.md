# 设备管理系统 - 运维文档

## 目录

本目录包含设备管理系统的完整运维文档和配置：

```
operations/
├── README.md              # 本文件 - 文档说明
├── 运维检查清单.md         # 日常运维检查清单
├── 日志配置说明.md         # 日志配置和管理说明
├── 监控配置.md            # 监控和告警配置
├── health_check.sh        # 健康检查脚本
└── tickets/               # 问题跟踪 (位于 input/tickets/)
```

## 快速开始

### 1. 日常健康检查
```bash
cd /root/.openclaw/workspace/projects/auto-dev-agents/projects/demo_project/output/operations
./health_check.sh
```

### 2. 查看运维检查清单
参考：[运维检查清单.md](./运维检查清单.md)

### 3. 配置监控
参考：[监控配置.md](./监控配置.md)

### 4. 日志管理
参考：[日志配置说明.md](./日志配置说明.md)

## 文档说明

### 运维检查清单 (运维检查清单.md)
包含每日、每周、每月的运维检查项目，确保系统稳定运行。

**适用场景**:
- 每日系统巡检
- 定期维护检查
- 故障排查参考

**主要内容**:
- 服务状态检查
- 日志检查
- 资源监控
- 安全更新
- 备份验证
- 应急预案

### 日志配置说明 (日志配置说明.md)
详细说明系统日志的配置、收集、分析和保留策略。

**适用场景**:
- 日志系统配置
- 日志收集方案选型
- 日志分析排查

**主要内容**:
- Nginx 日志配置
- Node.js 日志配置
- Docker 日志配置
- 日志收集方案 (ELK/Loki)
- 日志分析命令
- 告警规则

### 监控配置 (监控配置.md)
提供完整的监控和告警配置方案，包括 Prometheus、Grafana、Alertmanager。

**适用场景**:
- 部署监控系统
- 配置告警规则
- 创建监控仪表板

**主要内容**:
- Prometheus 配置
- Alertmanager 配置
- 告警规则定义
- Grafana 仪表板
- Docker Compose 监控栈
- 黑盒监控配置

### 健康检查脚本 (health_check.sh)
自动化健康检查脚本，支持 Cron 定时执行。

**功能**:
- ✓ Docker 服务状态检查
- ✓ HTTP 端点可用性检查
- ✓ 系统资源监控 (CPU/内存/磁盘)
- ✓ 容器日志错误检测
- ✓ 数据库状态检查
- ✓ 网络连接检查
- ✓ 自动生成检查报告
- ✓ 告警通知支持

**使用方法**:
```bash
# 手动执行
./health_check.sh

# 配置 Cron (每 5 分钟执行一次)
crontab -e
*/5 * * * * /path/to/health_check.sh

# 设置告警邮箱
export ALERT_EMAIL="ops@example.com"
./health_check.sh
```

**输出**:
- 控制台实时输出检查结果
- 日志文件：`health_check.log`
- JSON 报告：`health_report_YYYYMMDD_HHMMSS.json`

## 问题跟踪

检查发现的问题会记录在 `input/tickets/` 目录：

```bash
ls -la /root/.openclaw/workspace/projects/auto-dev-agents/projects/demo_project/input/tickets/
```

**最新检查报告**: [ops-check-20260321.md](../input/tickets/ops-check-20260321.md)

## 部署监控系统

### 前置条件
- Docker 和 Docker Compose 已安装
- 系统有空闲端口：9090, 9093, 3000, 9100, 8080, 9115

### 部署步骤

1. **准备配置文件**
```bash
cd /root/.openclaw/workspace/projects/auto-dev-agents/projects/demo_project/output/operations

# 创建 Prometheus 配置
cat > prometheus.yml << 'EOF'
# (参考 监控配置.md 中的内容)
EOF

# 创建 Alertmanager 配置
cat > alertmanager.yml << 'EOF'
# (参考 监控配置.md 中的内容)
EOF

# 创建告警规则
cat > alerts.yml << 'EOF'
# (参考 监控配置.md 中的内容)
EOF
```

2. **启动监控栈**
```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

3. **访问监控界面**
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)
- Alertmanager: http://localhost:9093

4. **导入 Grafana 仪表板**
- 访问 Grafana
- 导入 监控配置.md 中提供的仪表板 JSON

## 维护计划

### 每日
- [ ] 执行健康检查脚本
- [ ] 查看告警通知
- [ ] 检查错误日志

### 每周
- [ ] 审查运维检查清单
- [ ] 分析性能趋势
- [ ] 更新监控规则

### 每月
- [ ] 审查和更新文档
- [ ] 测试备份恢复
- [ ] 评估容量规划

## 应急联系

| 角色 | 联系人 | 联系方式 |
|------|--------|----------|
| 运维负责人 | TBD | TBD |
| 开发负责人 | TBD | TBD |

## 相关文档

- [部署配置](../deploy/README.md)
- [问题跟踪](../input/tickets/)

## 版本历史

| 版本 | 日期 | 更新内容 | 作者 |
|------|------|---------|------|
| 1.0 | 2026-03-21 | 初始版本 | operations 智能体 |

---

**最后更新**: 2026-03-21  
**维护团队**: DevOps  
**文档状态**: 有效
