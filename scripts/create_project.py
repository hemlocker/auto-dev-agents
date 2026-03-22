#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建项目脚本
Create Project Script

基于 OpenClaw 平台创建新的开发项目
"""

import argparse
import json
from datetime import datetime
from pathlib import Path


def create_project(name: str, goal: str, base_dir: str = None) -> dict:
    """
    创建新项目
    
    Args:
        name: 项目名称
        goal: 项目目标
        base_dir: 项目根目录
        
    Returns:
        项目配置信息
    """
    if base_dir is None:
        base_dir = Path(__file__).parent.parent / "projects"
    else:
        base_dir = Path(base_dir)
    
    project_dir = base_dir / name
    
    # 检查项目是否已存在
    if project_dir.exists():
        print(f"❌ 项目 '{name}' 已存在")
        return {"success": False, "error": "项目已存在"}
    
    # 创建目录结构
    dirs = [
        "input/feedback",
        "input/meetings",
        "input/emails",
        "input/tickets",
        "output/requirements",
        "output/design",
        "output/src",
        "output/tests",
        "output/deploy",
        "output/operations",
        "output/monitor",
        "output/optimizer",
        "logs/agents",
        "logs/workflows",
    ]
    
    for d in dirs:
        (project_dir / d).mkdir(parents=True, exist_ok=True)
    
    # 创建项目配置
    project_config = {
        "name": name,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "status": "created",
        "goal": goal,
        "workflow_results": []
    }
    
    with open(project_dir / "project.json", "w", encoding="utf-8") as f:
        json.dump(project_config, f, indent=2, ensure_ascii=False)
    
    # 创建默认的项目目标文件
    goal_file = project_dir / "input" / "feedback" / "project_goal.md"
    with open(goal_file, "w", encoding="utf-8") as f:
        f.write(f"""# 项目目标

## 项目名称
{goal}

## 描述
请补充项目详细描述...

## 核心功能
1. 功能1
2. 功能2
3. 功能3

## 技术栈
- 后端：
- 数据库：
- 前端：
""")
    
    print(f"✅ 项目 '{name}' 创建成功")
    print(f"📁 项目目录: {project_dir}")
    print(f"📝 项目目标: {goal}")
    print(f"\n下一步:")
    print(f"  1. 编辑 {project_dir}/input/feedback/project_goal.md")
    print(f"  2. 运行 python scripts/run_workflow.py --project {name}")
    
    return {
        "success": True,
        "project_dir": str(project_dir),
        "config": project_config
    }


def main():
    parser = argparse.ArgumentParser(description="创建新的开发项目")
    parser.add_argument("--name", "-n", required=True, help="项目名称")
    parser.add_argument("--goal", "-g", required=True, help="项目目标")
    parser.add_argument("--base-dir", "-b", help="项目根目录（默认: projects/）")
    
    args = parser.parse_args()
    
    result = create_project(
        name=args.name,
        goal=args.goal,
        base_dir=args.base_dir
    )
    
    return 0 if result["success"] else 1


if __name__ == "__main__":
    exit(main())