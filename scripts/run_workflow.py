#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行工作流脚本
Run Workflow Script

基于 OpenClaw 平台运行开发工作流
通过 sessions_spawn 创建子会话执行各阶段任务
"""

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path


def load_config() -> dict:
    """加载配置文件"""
    config_path = Path(__file__).parent.parent / "config.yaml"
    
    if not config_path.exists():
        return {
            "projects": {"dir": "projects", "default": "demo_project"},
            "workflow": {
                "stages": [
                    {"name": "requirement", "agent": "RequirementAgent"},
                    {"name": "design", "agent": "DesignAgent"},
                    {"name": "development", "agent": "DevelopmentAgent"},
                    {"name": "testing", "agent": "TestingAgent"},
                    {"name": "deployment", "agent": "DeploymentAgent"},
                    {"name": "operations", "agent": "OperationsAgent"},
                    {"name": "monitor", "agent": "MonitorAgent"},
                    {"name": "optimizer", "agent": "OptimizerAgent"},
                ],
                "execution": {
                    "stage_delay_minutes": 5,
                    "quality_threshold": 0.85,
                    "max_iterations": 3
                }
            }
        }
    
    # 简单的 YAML 解析（避免依赖 pyyaml）
    import yaml
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_prompt(prompt_path: str) -> str:
    """加载提示词"""
    full_path = Path(__file__).parent.parent / prompt_path
    if full_path.exists():
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def get_project_info(project_name: str) -> dict:
    """获取项目信息"""
    projects_dir = Path(__file__).parent.parent / "projects"
    project_dir = projects_dir / project_name
    config_file = project_dir / "project.json"
    
    if not config_file.exists():
        return {"error": f"项目 '{project_name}' 不存在"}
    
    with open(config_file, "r", encoding="utf-8") as f:
        return json.load(f)


def run_stage_via_openclaw(
    stage: dict,
    project_name: str,
    input_context: str = ""
) -> dict:
    """
    通过 OpenClaw 运行单个阶段
    
    注意：此函数设计为被 OpenClaw 会话调用
    实际执行时，应该在 OpenClaw 会话中直接使用 sessions_spawn
    """
    prompt = load_prompt(stage.get("prompt", ""))
    
    # 构建任务描述
    task = f"""
# 项目：{project_name}
# 阶段：{stage['name']}
# 智能体：{stage['agent']}

{prompt}

---
## 上下文
{input_context}

---
## 任务
请根据上述要求和上下文，完成 {stage['name']} 阶段的工作。
输出结果到 projects/{project_name}/output/{stage['name']}/ 目录。
"""
    
    return {
        "stage": stage["name"],
        "agent": stage["agent"],
        "task": task,
        "prompt_loaded": bool(prompt)
    }


def run_workflow(project_name: str, stages: list = None) -> dict:
    """
    运行完整工作流
    
    Args:
        project_name: 项目名称
        stages: 要运行的阶段列表（None 表示全部）
        
    Returns:
        执行结果
    """
    config = load_config()
    project_info = get_project_info(project_name)
    
    if "error" in project_info:
        print(f"❌ {project_info['error']}")
        return {"success": False, "error": project_info["error"]}
    
    print(f"\n{'='*60}")
    print(f"🚀 开始执行开发工作流")
    print(f"📋 项目：{project_name}")
    print(f"🎯 目标：{project_info.get('goal', '未指定')}")
    print(f"{'='*60}\n")
    
    all_stages = config["workflow"]["stages"]
    execution_config = config["workflow"]["execution"]
    
    if stages:
        all_stages = [s for s in all_stages if s["name"] in stages]
    
    results = []
    context = ""
    
    for i, stage in enumerate(all_stages, 1):
        print(f"\n--- 阶段 {i}/{len(all_stages)}: {stage['name']} ---")
        
        # 准备阶段任务
        stage_result = run_stage_via_openclaw(
            stage=stage,
            project_name=project_name,
            input_context=context
        )
        
        print(f"📝 提示词: {'已加载' if stage_result['prompt_loaded'] else '未找到'}")
        print(f"🤖 智能体: {stage['agent']}")
        
        # 在实际运行时，这里会调用 OpenClaw 的 sessions_spawn
        # 现在打印任务信息供参考
        print(f"\n💡 任务提示:")
        print(f"   在 OpenClaw 会话中，可以使用以下方式运行:")
        print(f"   sessions_spawn(runtime='subagent', task='...')")
        
        results.append(stage_result)
        
        # 更新上下文（供下一阶段使用）
        context += f"\n### {stage['name']} 阶段已完成\n"
    
    # 更新项目状态
    project_info["status"] = "workflow_running"
    project_info["updated_at"] = datetime.now().isoformat()
    project_info["workflow_results"] = results
    
    projects_dir = Path(__file__).parent.parent / "projects"
    config_file = projects_dir / project_name / "project.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(project_info, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"✅ 工作流任务已准备完成")
    print(f"📁 结果目录: projects/{project_name}/output/")
    print(f"{'='*60}\n")
    
    return {
        "success": True,
        "project": project_name,
        "stages_run": len(results),
        "results": results
    }


def main():
    parser = argparse.ArgumentParser(description="运行开发工作流")
    parser.add_argument("--project", "-p", required=True, help="项目名称")
    parser.add_argument("--stages", "-s", help="要运行的阶段（逗号分隔，如: requirement,design）")
    
    args = parser.parse_args()
    
    stages = None
    if args.stages:
        stages = [s.strip() for s in args.stages.split(",")]
    
    result = run_workflow(project_name=args.project, stages=stages)
    
    return 0 if result["success"] else 1


if __name__ == "__main__":
    exit(main())