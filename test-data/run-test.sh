#!/bin/bash
# 标准测试运行脚本
# 用法: ./run-test.sh <stage> [project_name]

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECTS_DIR="$(dirname "$SCRIPT_DIR")/projects"

# 默认项目名
PROJECT_NAME="${2:-test-device-management}"

# 显示帮助
show_help() {
    echo "标准测试运行脚本"
    echo ""
    echo "用法: $0 <stage> [project_name]"
    echo ""
    echo "阶段:"
    echo "  1  - 阶段1：初始需求（完整工作流）"
    echo "  2  - 阶段2：功能扩展（增量开发）"
    echo "  3  - 阶段3：问题反馈（优化修复）"
    echo "  all - 运行所有阶段"
    echo ""
    echo "示例:"
    echo "  $0 1                    # 运行阶段1测试"
    echo "  $0 2 my-project         # 运行阶段2测试"
    echo "  $0 all                  # 运行所有阶段测试"
}

# 阶段1：初始需求
run_stage1() {
    echo "=========================================="
    echo "阶段1：初始需求测试"
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
    echo "启动完整工作流..."
    cd "$(dirname "$SCRIPT_DIR")"
    python3 scripts/workflow.py -p "$PROJECT_NAME" --start
}

# 阶段2：功能扩展
run_stage2() {
    echo "=========================================="
    echo "阶段2：功能扩展测试"
    echo "=========================================="
    
    if [ ! -d "$PROJECTS_DIR/$PROJECT_NAME" ]; then
        echo "❌ 项目不存在，请先运行阶段1"
        exit 1
    fi
    
    echo "添加新功能需求..."
    cp -r "$SCRIPT_DIR/stage-2-features/input/"* "$PROJECTS_DIR/$PROJECT_NAME/input/"
    
    echo ""
    echo "启动增量开发工作流..."
    cd "$(dirname "$SCRIPT_DIR")"
    python3 scripts/workflow.py -p "$PROJECT_NAME" --stages development,testing
}

# 阶段3：问题反馈
run_stage3() {
    echo "=========================================="
    echo "阶段3：问题反馈测试"
    echo "=========================================="
    
    if [ ! -d "$PROJECTS_DIR/$PROJECT_NAME" ]; then
        echo "❌ 项目不存在，请先运行阶段1"
        exit 1
    fi
    
    echo "添加问题工单..."
    cp -r "$SCRIPT_DIR/stage-3-issues/input/"* "$PROJECTS_DIR/$PROJECT_NAME/input/"
    
    echo ""
    echo "启动优化工作流..."
    cd "$(dirname "$SCRIPT_DIR")"
    python3 scripts/workflow.py -p "$PROJECT_NAME" --stages monitor,optimizer
}

# 主逻辑
case "${1:-}" in
    1) run_stage1 ;;
    2) run_stage2 ;;
    3) run_stage3 ;;
    all)
        run_stage1
        sleep 10
        run_stage2
        sleep 10
        run_stage3
        echo ""
        echo "所有阶段测试完成！"
        ;;
    -h|--help|help) show_help ;;
    *)
        echo "❌ 未知阶段: $1"
        show_help
        exit 1
        ;;
esac
