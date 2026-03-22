# Deployment 智能体知识库

## 角色定位

Deployment（部署工程师）负责：
- 创建部署配置
- 容器化配置
- 编写部署脚本
- 环境配置管理

---

## 部署方式

| 方式 | 适用场景 | 复杂度 |
|------|----------|--------|
| 直接运行 | 开发/测试 | 低 |
| Docker | 生产环境 | 中 |
| Docker Compose | 小型生产 | 中 |
| Kubernetes | 大型生产 | 高 |

---

## Docker 配置模板

### 后端 Dockerfile
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --production
COPY . .
EXPOSE 3000
CMD ["node", "src/app.js"]
```

### 前端 Dockerfile
```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### docker-compose.yml
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
    volumes:
      - ./data:/app/data

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
```

---

## Nginx 配置模板

```nginx
server {
    listen 80;
    
    # 前端静态文件
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }
    
    # API 反向代理
    location /api {
        proxy_pass http://backend:3000;
        proxy_set_header Host $host;
    }
}
```

---

## 部署脚本模板

### start.sh
```bash
#!/bin/bash
echo "Starting services..."
docker-compose up -d
echo "Services started!"
```

### stop.sh
```bash
#!/bin/bash
echo "Stopping services..."
docker-compose down
echo "Services stopped!"
```

---

## 环境变量管理

### .env.example
```
NODE_ENV=production
PORT=3000
DB_PATH=./data/database.sqlite
```

---

## 检查清单

- [ ] Dockerfile 已创建
- [ ] docker-compose.yml 已创建
- [ ] Nginx 配置正确
- [ ] 启动脚本可用
- [ ] 环境变量已配置

---

**相关文件**
- 提示词：`prompts/deployment/system.md`
- 检查清单：`knowledge/checklists/deployment-checklist.md`