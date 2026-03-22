# 新工单：运维配置完善

**项目**: demo_project  
**创建时间**: 2026-03-22  
**创建智能体**: optimizer  
**PDCA 阶段**: PLAN  
**工单类型**: 运维改进  
**优先级**: P2

---

## 1. 工单概述

基于运维检查发现的配置缺失问题，完善 Docker 和系统配置，提升系统可靠性、可维护性和安全性。

**当前状态**: 基础运维配置缺失  
**目标状态**: 符合生产环境最佳实践  
**截止时间**: 2026-04-04

---

## 2. 问题背景

### 2.1 运维检查发现的问题

| 问题 | 严重程度 | 工单 |
|-----|---------|------|
| Dockerfile 路径错误 | 高 | OPS-001 |
| 缺少健康检查配置 | 中 | OPS-002 |
| 日志配置不完善 | 中 | OPS-003 |
| 缺少资源限制 | 中 | MON-009 |
| 安全配置不足 | 中 | MON-010 |
| 缺少重启策略 | 低 | MON-011 |
| 环境变量管理不当 | 低 | MON-012 |

---

## 3. 改进任务

### 任务 1: 修复 Dockerfile 路径

**描述**: 修复 docker-compose.yml 中错误的 Dockerfile 路径

**当前配置**:
```yaml
services:
  frontend:
    build:
      context: ../src
      dockerfile: ../../deploy/Dockerfile.frontend  # ❌ 错误
```

**修改为**:
```yaml
services:
  frontend:
    build:
      context: ../src
      dockerfile: ../deploy/Dockerfile.frontend  # ✅ 正确
  
  backend:
    build:
      context: ../src
      dockerfile: ../deploy/Dockerfile.backend
```

**验收**:
- [ ] docker-compose build 成功
- [ ] 镜像可正常构建

**负责人**: 运维负责人  
**工时**: 1 小时

---

### 任务 2: 添加健康检查端点

**描述**: 在后端添加健康检查 API 端点

**新增文件**: `src/backend/src/routes/health.js`

**代码**:
```javascript
const express = require('express');
const router = express.Router();
const sequelize = require('../config/database');

/**
 * 健康检查端点
 * 返回服务运行状态和数据库连接状态
 */
router.get('/health', async (req, res) => {
  try {
    // 检查数据库连接
    await sequelize.authenticate();
    
    res.json({
      code: 200,
      message: 'healthy',
      data: {
        status: 'up',
        database: 'connected',
        version: process.env.npm_package_version || '1.0.0',
        timestamp: new Date().toISOString(),
        uptime: process.uptime()
      }
    });
  } catch (error) {
    res.status(500).json({
      code: 500,
      message: 'unhealthy',
      data: {
        status: 'down',
        database: 'disconnected',
        error: error.message,
        timestamp: new Date().toISOString()
      }
    });
  }
});

/**
 * 就绪检查端点
 * 检查服务是否准备好接收流量
 */
router.get('/ready', async (req, res) => {
  try {
    // 检查所有依赖是否就绪
    await sequelize.authenticate();
    
    res.json({
      code: 200,
      message: 'ready',
      data: {
        ready: true,
        checks: {
          database: 'ok'
        }
      }
    });
  } catch (error) {
    res.status(503).json({
      code: 503,
      message: 'not ready',
      data: {
        ready: false,
        checks: {
          database: 'error'
        },
        error: error.message
      }
    });
  }
});

module.exports = router;
```

**注册路由**: 在 `src/backend/src/app.js` 中添加:
```javascript
const healthRoutes = require('./routes/health');
app.use('/api', healthRoutes);
```

**验收**:
- [ ] /api/health 端点可访问
- [ ] 返回正确的健康状态
- [ ] 数据库连接检查正常

**负责人**: 后端开发  
**工时**: 2 小时

---

### 任务 3: 配置 Docker 健康检查

**描述**: 在 docker-compose.yml 中添加健康检查配置

**修改文件**: `deploy/docker-compose.yml`

**添加配置**:
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

**验收**:
- [ ] docker-compose ps 显示健康状态
- [ ] 服务异常时自动检测

**负责人**: 运维负责人  
**工时**: 1 小时

---

### 任务 4: 配置日志轮转

**描述**: 在 docker-compose.yml 中添加日志轮转配置

**修改文件**: `deploy/docker-compose.yml`

**添加配置**:
```yaml
services:
  backend:
    # ... 其他配置 ...
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "5"
  
  frontend:
    # ... 其他配置 ...
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "5"
```

**验收**:
- [ ] 日志文件有大小限制
- [ ] 日志文件有数量限制
- [ ] 旧日志自动清理

**负责人**: 运维负责人  
**工时**: 1 小时

---

### 任务 5: 配置资源限制

**描述**: 在 docker-compose.yml 中添加容器资源限制

**修改文件**: `deploy/docker-compose.yml`

**添加配置**:
```yaml
services:
  backend:
    # ... 其他配置 ...
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 128M
  
  frontend:
    # ... 其他配置 ...
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.1'
          memory: 64M
```

**验收**:
- [ ] 容器 CPU 使用有限制
- [ ] 容器内存使用有限制

**负责人**: 运维负责人  
**工时**: 1 小时

---

### 任务 6: 配置重启策略

**描述**: 在 docker-compose.yml 中添加重启策略

**修改文件**: `deploy/docker-compose.yml`

**添加配置**:
```yaml
services:
  backend:
    # ... 其他配置 ...
    restart: unless-stopped
  
  frontend:
    # ... 其他配置 ...
    restart: unless-stopped
```

**验收**:
- [ ] 容器异常退出后自动重启
- [ ] 手动停止后不自动重启

**负责人**: 运维负责人  
**工时**: 1 小时

---

### 任务 7: 改进环境变量管理

**描述**: 使用 .env 文件管理敏感信息

**新增文件**: `deploy/.env.example`

**内容**:
```bash
# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=demo_project
DB_USER=app_user
DB_PASSWORD=change_me_in_production

# 应用配置
NODE_ENV=production
PORT=3000
API_SECRET_KEY=change_me_in_production

# 日志配置
LOG_LEVEL=info
```

**修改文件**: `deploy/.gitignore`

**添加**:
```
.env
.env.local
.env.*.local
```

**修改文件**: `deploy/docker-compose.yml`

**使用环境变量**:
```yaml
services:
  backend:
    # ... 其他配置 ...
    env_file:
      - .env
    environment:
      - NODE_ENV=${NODE_ENV:-production}
      - PORT=${PORT:-3000}
      - DB_PASSWORD=${DB_PASSWORD}
```

**验收**:
- [ ] .env 文件已加入 .gitignore
- [ ] 敏感信息不再硬编码
- [ ] .env.example 提供配置模板

**负责人**: 运维负责人  
**工时**: 2 小时

---

### 任务 8: 增强安全配置

**描述**: 配置 HTTPS 和 CORS 策略

**修改文件**: `deploy/nginx.conf`

**添加 CORS 配置**:
```nginx
server {
    listen 80;
    server_name localhost;
    
    # CORS 配置
    add_header Access-Control-Allow-Origin "https://your-domain.com" always;
    add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
    add_header Access-Control-Allow-Headers "Origin, X-Requested-With, Content-Type, Accept, Authorization" always;
    add_header Access-Control-Allow-Credentials "true" always;
    
    # 预检请求处理
    if ($request_method = OPTIONS) {
        add_header Access-Control-Allow-Origin "https://your-domain.com";
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Origin, X-Requested-With, Content-Type, Accept, Authorization";
        add_header Access-Control-Allow-Credentials "true";
        add_header Content-Type 'text/plain; charset=utf-8';
        add_header Content-Length 0;
        return 204;
    }
    
    # ... 其他配置 ...
}
```

**验收**:
- [ ] CORS 策略已配置
- [ ] 生产环境配置 HTTPS

**负责人**: 运维负责人  
**工时**: 2 小时

---

## 4. 实施计划

| 任务 | 开始日期 | 结束日期 | 负责人 | 状态 |
|-----|---------|---------|--------|------|
| 任务 1: 修复 Dockerfile 路径 | 2026-04-04 | 2026-04-04 | 运维负责人 | 待开始 |
| 任务 2: 添加健康检查端点 | 2026-04-04 | 2026-04-04 | 后端开发 | 待开始 |
| 任务 3: 配置 Docker 健康检查 | 2026-04-04 | 2026-04-04 | 运维负责人 | 待开始 |
| 任务 4: 配置日志轮转 | 2026-04-04 | 2026-04-04 | 运维负责人 | 待开始 |
| 任务 5: 配置资源限制 | 2026-04-04 | 2026-04-04 | 运维负责人 | 待开始 |
| 任务 6: 配置重启策略 | 2026-04-04 | 2026-04-04 | 运维负责人 | 待开始 |
| 任务 7: 改进环境变量管理 | 2026-04-04 | 2026-04-04 | 运维负责人 | 待开始 |
| 任务 8: 增强安全配置 | 2026-04-04 | 2026-04-04 | 运维负责人 | 待开始 |

---

## 5. 验收标准

### 5.1 功能验收
- [ ] docker-compose build 成功
- [ ] docker-compose up -d 成功
- [ ] 健康检查正常工作
- [ ] 日志轮转正常

### 5.2 安全验收
- [ ] 敏感信息已加密
- [ ] CORS 策略已配置
- [ ] 无高危安全漏洞

### 5.3 文档验收
- [ ] 运维文档已更新
- [ ] .env.example 已创建

---

## 6. 预期效果

| 指标 | 改进前 | 改进后 | 提升 |
|-----|-------|-------|------|
| 服务可用性 | 未知 | 可监控 | 100%↑ |
| 日志管理 | 无限制 | 50MB 上限 | 安全 |
| 资源使用 | 无限制 | 有限制 | 安全 |
| 配置安全 | 硬编码 | 环境变量 | 安全 |

---

## 7. 关联工单

- **来源**: OPS-001, OPS-002, OPS-003
- **关联**: MON-009, MON-010, MON-011, MON-012
- **依赖**: 无

---

## 8. 状态跟踪

| 日期 | 状态 | 备注 |
|-----|------|------|
| 2026-03-22 | 新建 | 工单创建 |

---

**工单状态**: 新建  
**优先级**: P2  
**预计工时**: 11 小时  
**实际工时**: 待填写

---

*本工单由 optimizer 智能体基于优化分析报告自动生成*
