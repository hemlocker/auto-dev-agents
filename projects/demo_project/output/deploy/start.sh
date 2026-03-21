#!/bin/bash

# 设备管理系统 - 部署启动脚本

set -e

echo "🚀 开始部署设备管理系统..."

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检查 docker-compose 是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose 未安装，请先安装"
    exit 1
fi

# 进入部署目录
cd "$(dirname "$0")"

# 停止旧容器
echo "📦 停止旧容器..."
docker-compose down || true

# 构建并启动
echo "🔨 构建镜像..."
docker-compose build

echo "🎯 启动服务..."
docker-compose up -d

echo ""
echo "✅ 部署完成！"
echo "📱 访问地址：http://localhost"
echo ""
echo "查看日志：docker-compose logs -f"
echo "停止服务：docker-compose down"
