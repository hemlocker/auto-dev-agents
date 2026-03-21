# 设备管理系统 - 部署配置

## 目录结构

```
deploy/
├── Dockerfile.backend    # 后端 Docker 镜像
├── Dockerfile.frontend   # 前端 Docker 镜像
├── docker-compose.yml    # Docker Compose 配置
├── nginx.conf            # Nginx 配置
├── start.sh              # 启动脚本
├── stop.sh               # 停止脚本
└── README.md             # 本文件
```

## 快速开始

### 1. 启动服务

```bash
chmod +x start.sh
./start.sh
```

### 2. 访问系统

浏览器访问：http://localhost

### 3. 查看日志

```bash
docker-compose logs -f
```

### 4. 停止服务

```bash
./stop.sh
# 或
docker-compose down
```

## 技术栈

- **前端**: Vue 3 + Vite + Element Plus
- **后端**: Node.js + Express + Sequelize
- **数据库**: SQLite (数据持久化在 Docker volume)
- **Web 服务器**: Nginx

## 端口说明

- 前端：80 (HTTP)
- 后端：3000 (内部网络，不对外暴露)

## 数据持久化

数据库数据存储在 Docker volume `db-data` 中，停止容器不会丢失数据。

如需清空数据：

```bash
docker volume rm demo_project_db-data
```

## 环境变量

后端支持以下环境变量：

- `NODE_ENV`: 运行环境 (production/development)
- `PORT`: 服务端口 (默认 3000)
