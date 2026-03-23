# 部署知识库

## 部署方式对比

| 方式 | 适用场景 | 优点 | 缺点 |
|------|----------|------|------|
| **直接运行** | 开发/测试 | 简单快速 | 环境不一致 |
| **Docker** | 生产环境 | 隔离性好 | 需要容器知识 |
| **Docker Compose** | 小型生产 | 易于编排 | 单机部署 |
| **Kubernetes** | 大型生产 | 高可用、可扩展 | 复杂度高 |

---

## Docker 部署

### Dockerfile 模板

```dockerfile
# 后端 Dockerfile
FROM openjdk:17-jdk-slim

WORKDIR /app

COPY target/*.jar app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]
```

```dockerfile
# 前端 Dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8080:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=prod
      - DB_HOST=mysql
      - REDIS_HOST=redis
    depends_on:
      - mysql
      - redis
    networks:
      - app-network

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    networks:
      - app-network

  mysql:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=root123
      - MYSQL_DATABASE=device_management
    volumes:
      - mysql-data:/var/lib/mysql
    networks:
      - app-network

  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data
    networks:
      - app-network

networks:
  app-network:
    driver: bridge

volumes:
  mysql-data:
  redis-data:
```

---

## Nginx 配置

```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    # 日志格式
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    # Gzip 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    # 后端代理
    upstream backend {
        server backend:8080;
    }

    server {
        listen 80;
        server_name localhost;

        # 前端静态资源
        location / {
            root /usr/share/nginx/html;
            index index.html;
            try_files $uri $uri/ /index.html;
        }

        # API 代理
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }
}
```

---

## CI/CD 配置

### GitHub Actions

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up JDK 17
      uses: actions/setup-java@v3
      with:
        java-version: '17'
        distribution: 'temurin'
    
    - name: Build with Maven
      run: mvn clean package -DskipTests
    
    - name: Run tests
      run: mvn test
    
    - name: Build Docker image
      run: docker build -t myapp:latest .
    
    - name: Push to registry
      run: |
        docker tag myapp:latest registry.example.com/myapp:latest
        docker push registry.example.com/myapp:latest
```

---

## 部署检查清单

### 发布前检查

- [ ] 所有测试通过
- [ ] 代码已合并到主分支
- [ ] 版本号已更新
- [ ] 数据库迁移脚本准备就绪
- [ ] 配置文件已更新
- [ ] 回滚方案已准备

### 发布后验证

- [ ] 服务正常启动
- [ ] 健康检查通过
- [ ] 核心功能可用
- [ ] 日志正常输出
- [ ] 监控告警正常

---

## 回滚方案

```bash
# 1. 回滚到上一版本
kubectl rollout undo deployment/myapp

# 2. 回滚到指定版本
kubectl rollout undo deployment/myapp --to-revision=2

# 3. 查看回滚历史
kubectl rollout history deployment/myapp
```

---

## 监控配置

### Prometheus + Grafana

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'spring-boot'
    metrics_path: '/actuator/prometheus'
    static_configs:
      - targets: ['backend:8080']
```

### 告警规则

```yaml
groups:
  - name: app-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_server_requests_seconds_count{status="500"}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
```