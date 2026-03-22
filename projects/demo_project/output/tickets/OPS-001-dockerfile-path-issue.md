# Ticket: OPS-001 - Dockerfile 路径配置错误

## 问题描述
docker-compose.yml 中引用的 Dockerfile 路径不正确，导致构建失败。

## 问题详情

### 当前配置
```yaml
# docker-compose.yml
services:
  frontend:
    build:
      context: ../src
      dockerfile: ../../deploy/Dockerfile.frontend
  
  backend:
    build:
      context: ../src
      dockerfile: ../../deploy/Dockerfile.backend
```

### 问题分析
- `context: ../src` 指向 `/root/.openclaw/workspace/projects/auto-dev-agents/projects/demo_project/output/src/`
- `dockerfile: ../../deploy/Dockerfile.frontend` 会解析为 `/root/.openclaw/workspace/projects/auto-dev-agents/projects/demo_project/deploy/Dockerfile.frontend`
- 但实际 Dockerfile 位于 `/root/.openclaw/workspace/projects/auto-dev-agents/projects/demo_project/output/deploy/Dockerfile.frontend`
- 路径差一级目录，导致构建时找不到 Dockerfile

### 正确路径
应该使用以下任一方案：

**方案 1: 调整 dockerfile 路径**
```yaml
services:
  frontend:
    build:
      context: ../src
      dockerfile: ../deploy/Dockerfile.frontend  # 修改为 ../deploy/
  
  backend:
    build:
      context: ../src
      dockerfile: ../deploy/Dockerfile.backend   # 修改为 ../deploy/
```

**方案 2: 调整 context 路径**
```yaml
services:
  frontend:
    build:
      context: .
      dockerfile: deploy/Dockerfile.frontend
  
  backend:
    build:
      context: .
      dockerfile: deploy/Dockerfile.backend
```

## 影响范围
- 无法通过 docker-compose build 构建镜像
- 部署脚本 start.sh 执行失败
- 新功能无法上线

## 优先级
🔴 **高** - 阻塞部署

## 解决方案
1. 修改 docker-compose.yml 中的 dockerfile 路径
2. 在本地测试构建：`docker-compose build`
3. 验证容器启动：`docker-compose up -d`
4. 更新部署文档

## 发现时间
2026-03-22 00:12

## 发现智能体
operations (PDCA: CHECK)

## 状态
📋 待修复
