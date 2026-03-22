# Ticket: MON-004 - 数据库备份缺失

## 问题描述
项目无数据库备份机制，`output/database/` 目录为空，存在数据丢失风险。

## 问题详情

### 当前状态
- **数据库文件位置**: `output/src/database/device.db` (32KB)
- **备份目录**: `output/database/` (空目录)
- **备份脚本**: 不存在
- **备份策略**: 无

### 风险评估
| 风险场景 | 可能性 | 影响 | 风险等级 |
|---------|--------|------|---------|
| 服务器故障 | 中 | 数据永久丢失 | 🔴 高 |
| 误操作删除 | 中 | 数据永久丢失 | 🔴 高 |
| 数据损坏 | 低 | 部分数据丢失 | 🟡 中 |
| 恶意攻击 | 低 | 数据泄露/丢失 | 🟡 中 |

### 最佳实践对比
| 项目 | 最佳实践 | 当前状态 | 差距 |
|-----|---------|---------|------|
| 备份频率 | 每日至少 1 次 | 无备份 | ❌ |
| 备份保留 | 至少 7 天 | 无备份 | ❌ |
| 异地备份 | 至少 1 份异地 | 无备份 | ❌ |
| 恢复测试 | 定期测试 | 无测试 | ❌ |
| 备份监控 | 监控备份状态 | 无监控 | ❌ |

## 影响范围
- 生产数据无保护
- 无法应对数据丢失场景
- 不符合运维最佳实践
- 可能被审计发现问题

## 优先级
🔴 **P0 - 严重**

## 解决方案

### 方案一：简单备份脚本（推荐）

创建备份脚本 `deploy/backup.sh`:
```bash
#!/bin/bash
# 数据库备份脚本

BACKUP_DIR="/root/.openclaw/workspace/projects/auto-dev-agents/projects/demo_project/backups"
DB_FILE="/root/.openclaw/workspace/projects/auto-dev-agents/projects/demo_project/output/src/database/device.db"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/device_$DATE.db"

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 复制数据库文件
cp "$DB_FILE" "$BACKUP_FILE"

# 压缩备份
gzip "$BACKUP_FILE"

# 删除 7 天前的备份
find "$BACKUP_DIR" -name "device_*.db.gz" -mtime +7 -delete

echo "备份完成：$BACKUP_FILE.gz"
```

配置定时任务 (crontab):
```bash
# 每日凌晨 2 点执行备份
0 2 * * * /root/.openclaw/workspace/projects/auto-dev-agents/projects/demo_project/deploy/backup.sh
```

### 方案二：Docker Volume 备份

如果使用 Docker，配置 volume 备份:
```yaml
# docker-compose.yml
services:
  backup:
    image: alpine
    volumes:
      - db-data:/data:ro
      - ./backups:/backup
    command: >
      sh -c "cp /data/device.db /backup/device_$$(date +%Y%m%d_%H%M%S).db &&
             gzip /backup/device_*.db &&
             find /backup -name '*.gz' -mtime +7 -delete"
```

### 方案三：SQLite WAL 模式 + 定期导出

```bash
# 启用 WAL 模式
sqlite3 device.db "PRAGMA journal_mode=WAL;"

# 定期导出 SQL
sqlite3 device.db ".dump" > backup_$(date +%Y%m%d).sql
```

## 验收标准
- [ ] 备份脚本已创建并测试
- [ ] 定时任务已配置
- [ ] 至少保留 7 份历史备份
- [ ] 执行恢复测试并记录
- [ ] 备份监控已配置

## 实施步骤
1. 创建 `deploy/backup.sh` 脚本
2. 执行首次手动备份
3. 配置 crontab 定时任务
4. 验证备份文件完整性
5. 执行恢复测试
6. 更新运维文档

## 发现时间
2026-03-22 00:15

## 发现智能体
monitor (PDCA: CHECK)

## 状态
📋 待修复

## 关联工单
- OPS-003: 日志配置不完善
- OPS-002: 缺少健康检查配置
