#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDCA 工作流调度器
PDCA Workflow Scheduler

基于 OpenClaw 平台的 PDCA 循环自动化
"""

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional


class PDCAWorkflow:
    """PDCA 工作流调度器"""
    
    def __init__(self, project_name: str, base_dir: str = None):
        self.project_name = project_name
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent
        self.config = self._load_config()
        self.project_dir = self.base_dir / "projects" / project_name
        
    def _load_config(self) -> dict:
        """加载配置"""
        config_path = self.base_dir / "config.yaml"
        if not config_path.exists():
            return {"pdca": {"max_cycles": 0}}
        
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        config = {"pdca": {"max_cycles": 0}}
        match = re.search(r"max_cycles:\s*(\d+)", content)
        if match:
            config["pdca"]["max_cycles"] = int(match.group(1))
        return config
    
    def _load_prompt(self, prompt_path: str) -> str:
        """加载提示词"""
        full_path = self.base_dir / prompt_path
        if full_path.exists():
            with open(full_path, "r", encoding="utf-8") as f:
                return f.read()
        return ""
    
    def _read_project_state(self) -> dict:
        """读取项目状态"""
        state_file = self.project_dir / "pdca_state.json"
        if state_file.exists():
            with open(state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"cycle": 0, "current_phase": None, "current_stage": None, "history": []}
    
    def _save_project_state(self, state: dict):
        """保存项目状态"""
        state_file = self.project_dir / "pdca_state.json"
        state["updated_at"] = datetime.now().isoformat()
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    
    def _generate_spawn_task(self, stage_name: str, phase: str) -> dict:
        """生成 sessions_spawn 任务配置"""
        prompt = self._load_prompt(f"prompts/{stage_name}/system.md")
        input_map = {
            "requirement": "input/", "design": "output/requirements/",
            "development": "output/design/", "testing": "output/src/",
            "deployment": "output/tests/", "operations": "output/deploy/",
            "monitor": "output/", "optimizer": "output/monitor/"
        }
        output_map = {
            "requirement": "output/requirements/", "design": "output/design/",
            "development": "output/src/", "testing": "output/tests/",
            "deployment": "output/deploy/", "operations": "output/operations/",
            "monitor": "output/monitor/", "optimizer": "output/optimizer/"
        }
        
        task = f"""# 项目: {self.project_name} | PDCA 阶段: {phase.upper()} | 智能体: {stage_name}

## 系统提示词
{prompt}

## 输入: {self.project_dir / input_map.get(stage_name, 'input/')}
## 输出: {self.project_dir / output_map.get(stage_name, 'output/')}

请根据输入完成 {stage_name} 阶段工作，结果写入输出目录。"""
        
        return {
            "action": "sessions_spawn",
            "params": {
                "runtime": "subagent", "mode": "run", "task": task,
                "cwd": str(self.base_dir), "timeoutSeconds": 1800,
                "label": f"{self.project_name}_{phase}_{stage_name}"
            },
            "stage": stage_name, "phase": phase
        }
    
    def get_next_stage(self) -> Optional[dict]:
        """获取下一阶段任务"""
        state = self._read_project_state()
        pdca_config = self.config.get("pdca", {})
        
        phase_order = ["plan", "do", "check", "act"]
        stage_order = {
            "plan": ["requirement", "design"],
            "do": ["development", "testing", "deployment"],
            "check": ["operations", "monitor"],
            "act": ["optimizer"]
        }
        
        current_phase = state.get("current_phase")
        current_stage = state.get("current_stage")
        
        if current_phase is None:
            next_phase, next_stage = "plan", "requirement"
            state["cycle"] = state.get("cycle", 0) + 1
        else:
            phase_idx = phase_order.index(current_phase)
            stage_idx = stage_order[current_phase].index(current_stage)
            
            if stage_idx + 1 < len(stage_order[current_phase]):
                next_phase, next_stage = current_phase, stage_order[current_phase][stage_idx + 1]
            elif phase_idx + 1 < len(phase_order):
                next_phase, next_stage = phase_order[phase_idx + 1], stage_order[phase_order[phase_idx + 1]][0]
            else:
                state["history"].append({"cycle": state["cycle"], "completed_at": datetime.now().isoformat()})
                max_cycles = pdca_config.get("max_cycles", 0)
                if max_cycles == 0 or state["cycle"] < max_cycles:
                    next_phase, next_stage = "plan", "requirement"
                    state["cycle"] += 1
                else:
                    self._save_project_state(state)
                    return None
        
        state["current_phase"], state["current_stage"] = next_phase, next_stage
        self._save_project_state(state)
        return self._generate_spawn_task(next_stage, next_phase)
    
    def run_full_cycle(self) -> list:
        """运行完整 PDCA 循环"""
        self._save_project_state({"cycle": 0, "current_phase": None, "current_stage": None, "history": []})
        tasks = []
        while (task := self.get_next_stage()) is not None:
            tasks.append(task)
        return tasks
    
    def get_status(self) -> dict:
        """获取当前状态"""
        state = self._read_project_state()
        return {
            "project": self.project_name, "cycle": state.get("cycle", 0),
            "current_phase": state.get("current_phase"), "current_stage": state.get("current_stage"),
            "history_count": len(state.get("history", [])), "project_dir": str(self.project_dir)
        }


def main():
    parser = argparse.ArgumentParser(description="PDCA 工作流调度器")
    parser.add_argument("--project", "-p", required=True, help="项目名称")
    parser.add_argument("--next", "-n", action="store_true", help="获取下一阶段任务")
    parser.add_argument("--full-cycle", "-f", action="store_true", help="运行完整 PDCA 循环")
    parser.add_argument("--status", "-s", action="store_true", help="查看当前状态")
    args = parser.parse_args()
    
    workflow = PDCAWorkflow(project_name=args.project)
    
    if args.status:
        print(json.dumps(workflow.get_status(), indent=2, ensure_ascii=False))
    elif args.full_cycle:
        tasks = workflow.run_full_cycle()
        print(f"\n📋 PDCA 循环任务列表 (共 {len(tasks)} 个阶段):")
        for i, task in enumerate(tasks, 1):
            print(f"  {i}. [{task['phase'].upper()}] {task['stage']}")
    elif args.next:
        task = workflow.get_next_stage()
        if task is None:
            print("✅ PDCA 循环已完成")
        else:
            print(f"\n📌 下一阶段: [{task['phase'].upper()}] {task['stage']}")
            print(f"\n💡 sessions_spawn 参数:\n{json.dumps(task['params'], indent=2, ensure_ascii=False)}")
    else:
        print(json.dumps(workflow.get_status(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    exit(main())