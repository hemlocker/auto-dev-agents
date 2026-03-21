#!/bin/bash

# 设备管理系统 - 停止脚本

set -e

echo "🛑 停止服务..."

cd "$(dirname "$0")"

docker-compose down

echo "✅ 服务已停止"
