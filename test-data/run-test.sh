#!/bin/bash
# 标准测试运行脚本
# 用法: ./run-test.sh [project_name]
# 默认执行完整 PDCA 循环

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECTS_DIR="$(dirname "$SCRIPT_DIR")/projects"

# 获取当前分支版本号
get_version() {
    cd "$(dirname "$SCRIPT_DIR")"
    git branch --show-current 2>/dev/null || echo "dev"
}

# 默认项目名（短格式：tdm-{版本号}）
DEFAULT_VERSION=$(get_version)
DEFAULT_NAME="tdm-${DEFAULT_VERSION}"
PROJECT_NAME="${1:-$DEFAULT_NAME}"

# 显示帮助
show_help() {
    echo "标准测试运行脚本"
    echo ""
    echo "用法: $0 [project_name]"
    echo ""
    echo "默认执行完整 PDCA 循环（需求→设计→开发→测试→部署→运维→监控→优化）"
    echo ""
    echo "默认项目名: $DEFAULT_NAME"
    echo ""
    echo "示例:"
    echo "  $0                      # 运行完整 PDCA 循环 (项目: $DEFAULT_NAME)"
    echo "  $0 my-project           # 运行完整 PDCA 循环 (项目: my-project)"
    echo "  $0 --help               # 显示帮助"
}

# 运行完整 PDCA 循环
run_full_cycle() {
    echo "=========================================="
    echo "完整 PDCA 循环测试"
    echo "项目名: $PROJECT_NAME"
    echo "=========================================="
    
    # 清理旧项目
    if [ -d "$PROJECTS_DIR/$PROJECT_NAME" ]; then
        echo "清理旧项目..."
        rm -rf "$PROJECTS_DIR/$PROJECT_NAME"
    fi
    
    # 复制测试数据
    echo "复制测试数据..."
    mkdir -p "$PROJECTS_DIR/$PROJECT_NAME"
    cp -r "$SCRIPT_DIR/stage-1-initial/"* "$PROJECTS_DIR/$PROJECT_NAME/"
    
    echo ""
    echo "启动完整 PDCA 循环..."
    echo "  PLAN: requirement, design"
    echo "  DO: development, testing, deployment"
    echo "  CHECK: operations, monitor"
    echo "  ACT: optimizer"
    echo ""
    
    cd "$(dirname "$SCRIPT_DIR")"
    python3 scripts/run.py -p "$PROJECT_NAME" --full-cycle --execute
}

# 主逻辑
case "${1:-}" in
    -h|--help|help) show_help ;;
    *) run_full_cycle ;;
esac
