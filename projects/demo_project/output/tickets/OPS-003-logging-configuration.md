# Ticket: OPS-003 - 日志配置不完善

## 问题描述
Docker 容器未配置日志轮转，可能导致磁盘空间耗尽。

## 问题详情

### 当前配置
docker-compose.yml 中未指定日志驱动和日志大小限制，使用 Docker 默认配置（无限制）。

### 风险
- 日志文件可能无限增长
- 磁盘空间耗尽风险
- 日志查询性能下降
- 重要日志被淹没

### 建议配置
```yaml
services:
  backend:
    # ... 其他配置 ...
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
  
  frontend:
    # ... 其他配置 ...
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 全局配置（可选）
在 `/etc/docker/daemon.json` 中配置默认日志策略：
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

## 影响范围
- 长期运行可能导致磁盘空间问题
- 日志管理不便
- 不符合生产环境最佳实践

## 优先级
🟡 **中** - 长期运行风险

## 解决方案
1. 在 docker-compose.yml 中添加 logging 配置
2. 重启服务应用新配置：`docker-compose up -d`
3. 验证日志轮转：`docker inspect --format='{{.HostConfig.LogConfig}}' <container>`
4. 考虑集中日志方案（ELK/Loki）用于生产环境

## 发现时间
2026-03-22 00:12

## 发现智能体
operations (PDCA: CHECK)

## 状态
📋 待修复
