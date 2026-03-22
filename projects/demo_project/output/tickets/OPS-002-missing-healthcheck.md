# Ticket: OPS-002 - 缺少健康检查配置

## 问题描述
docker-compose.yml 中未配置健康检查（healthcheck），无法自动检测服务健康状态。

## 问题详情

### 当前配置
```yaml
services:
  backend:
    build:
      context: ../src
      dockerfile: ../deploy/Dockerfile.backend
    expose:
      - "3000"
    volumes:
      - db-data:/app/data
    environment:
      - NODE_ENV=production
      - PORT=3000
    networks:
      - app-network
    restart: unless-stopped
    # ❌ 缺少 healthcheck 配置
```

### 建议配置
```yaml
services:
  backend:
    # ... 其他配置 ...
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:3000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
  
  frontend:
    # ... 其他配置 ...
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

### 需要后端支持
同时需要在后端 API 中添加健康检查端点：
```javascript
// backend/src/app.js
app.get('/api/health', (req, res) => {
  res.json({ 
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: '1.2.0'
  });
});
```

## 影响范围
- 无法自动检测服务是否正常运行
- 容器崩溃后可能无法自动重启
- 运维监控缺少关键指标
- 依赖检查（depends_on）无法等待服务真正就绪

## 优先级
🟡 **中** - 影响运维质量

## 解决方案
1. 在后端添加 `/api/health` 健康检查端点
2. 在 docker-compose.yml 中添加 healthcheck 配置
3. 安装 wget 到后端镜像中（或使用 curl）
4. 测试健康检查：`docker-compose ps` 应显示健康状态

## 发现时间
2026-03-22 00:12

## 发现智能体
operations (PDCA: CHECK)

## 状态
📋 待修复
