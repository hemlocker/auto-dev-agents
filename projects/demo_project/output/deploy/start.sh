#!/bin/bash

# 设备管理系统 - 部署启动脚本
# 版本：V1.2 (支持 Excel 导入导出、标签打印、统计报表)

set -e

echo "🚀 开始部署设备管理系统..."
echo "📦 版本：V1.2"
echo "✨ 新功能：Excel 导入导出 | 设备标签打印 | 统计报表"
echo ""

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

# 清理旧镜像 (可选，释放空间)
echo "🧹 清理旧镜像..."
docker image prune -f || true

# 构建并启动
echo "🔨 构建镜像..."
echo "   - 后端镜像 (包含 xlsx, qrcode, pdfkit 依赖)..."
echo "   - 前端镜像 (包含 echarts 图表库)..."
docker-compose build

echo "🎯 启动服务..."
docker-compose up -d

# 等待服务启动
echo ""
echo "⏳ 等待服务启动..."
sleep 5

# 检查容器状态
echo "📊 检查容器状态..."
docker-compose ps

echo ""
echo "✅ 部署完成！"
echo "📱 访问地址：http://localhost"
echo ""
echo "📋 功能模块:"
echo "   - 设备管理 (CRUD)"
echo "   - Excel 导入导出"
echo "   - 设备标签打印 (含二维码)"
echo "   - 统计报表 (ECharts 图表)"
echo ""
echo "🔍 查看日志：docker-compose logs -f"
echo "🛑 停止服务：docker-compose down"
echo "🔄 重启服务：docker-compose restart"
