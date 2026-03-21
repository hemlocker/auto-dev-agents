#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDCA 自动执行器
PDCA Auto Executor

真正的全自动执行：无需人工对话，后台自动循环运行

启动方式：
  python3 scripts/auto_executor.py --project demo_project --start
"""

import argparse
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional


class PDCAAutoExecutor:
    """PDCA 自动执行器"""
    
    def __init__(self, project_name: str, base_dir: str = None):
        self.project_name = project_name
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent
        self.config = self._load_config()
        self.project_dir = self.base_dir / "projects" / project_name
        self.running = True
        
    def _load_config(self) -> dict:
        config_path = self.base_dir / "config.yaml"
        if not config_path.exists():
            return {"pdca": {"cycle_interval_seconds": 300, "max_cycles": 0}, "execution": {"stage_delay_seconds": 60}}
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
        config = {"pdca": {"cycle_interval_seconds": 300, "max_cycles": 0}, "execution": {"stage_delay_seconds": 60}}
        for key in ["cycle_interval_seconds", "max_cycles"]:
            match = re.search(rf"{key}:\s*(\d+)", content)
            if match:
                config["pdca"][key] = int(match.group(1))
        for key in ["stage_delay_seconds"]:
            match = re.search(rf"{key}:\s*(\d+)", content)
            if match:
                config["execution"][key] = int(match.group(1))
        return config
    
    def _load_prompt(self, stage: str) -> str:
        prompt_path = self.base_dir / "prompts" / stage / "system.md"
        if prompt_path.exists():
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        return f"你是 {stage} 智能体，请完成你的任务。"
    
    def _read_state(self) -> dict:
        state_file = self.project_dir / "pdca_state.json"
        if state_file.exists():
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {"cycle": 0, "current_phase": None, "current_stage": None, "history": [], "paused": False}
    
    def _save_state(self, state: dict):
        state_file = self.project_dir / "pdca_state.json"
        state["updated_at"] = datetime.now().isoformat()
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    
    def _get_next_stage(self, state: dict) -> tuple:
        phase_order = ["plan", "do", "check", "act"]
        stage_map = {"plan": ["requirement", "design"], "do": ["development", "testing", "deployment"], "check": ["operations", "monitor"], "act": ["optimizer"]}
        current_phase = state.get("current_phase")
        current_stage = state.get("current_stage")
        if current_phase is None:
            state["cycle"] = state.get("cycle", 0) + 1
            return "plan", "requirement"
        phase_idx = phase_order.index(current_phase)
        stages = stage_map[current_phase]
        stage_idx = stages.index(current_stage)
        if stage_idx + 1 < len(stages):
            return current_phase, stages[stage_idx + 1]
        elif phase_idx + 1 < len(phase_order):
            return phase_order[phase_idx + 1], stage_map[phase_order[phase_idx + 1]][0]
        else:
            state["history"].append({"cycle": state["cycle"], "completed_at": datetime.now().isoformat()})
            max_cycles = self.config["pdca"].get("max_cycles", 0)
            if max_cycles == 0 or state["cycle"] < max_cycles:
                state["cycle"] += 1
                return "plan", "requirement"
            return None, None
    
    def _get_input_output(self, stage: str) -> tuple:
        input_map = {"requirement": "input/", "design": "output/requirements/", "development": "output/design/", "testing": "output/src/", "deployment": "output/tests/", "operations": "output/deploy/", "monitor": "output/", "optimizer": "output/monitor/"}
        output_map = {"requirement": "output/requirements/", "design": "output/design/", "development": "output/src/", "testing": "output/tests/", "deployment": "output/deploy/", "operations": "output/operations/", "monitor": "output/monitor/", "optimizer": "output/optimizer/"}
        return str(self.project_dir / input_map.get(stage, "input/")), str(self.project_dir / output_map.get(stage, "output/"))
    
    def _execute_stage(self, phase: str, stage: str) -> bool:
        """执行单个阶段 - 输出 sessions_spawn 配置"""
        prompt = self._load_prompt(stage)
        input_dir, output_dir = self._get_input_output(stage)
        
        print(f"\n{'='*50}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 执行: [{phase.upper()}] {stage}")
        print(f"{'='*50}")
        
        # 生成 sessions_spawn 配置
        task = f"""# 项目: {self.project_name} | PDCA: {phase.upper()} | 智能体: {stage}

## 提示词
{prompt}

## 输入: {input_dir}
## 输出: {output_dir}

完成 {stage} 阶段工作，结果写入输出目录。"""
        
        spawn_config = {
            "action": "sessions_spawn",
            "params": {
                "runtime": "subagent",
                "mode": "run",
                "task": task,
                "cwd": str(self.base_dir),
                "timeoutSeconds": 1800,
                "label": f"{self.project_name}_{phase}_{stage}"
            }
        }
        
        # 记录执行
        log_file = self.project_dir / "logs" / "execution.jsonl"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps({"timestamp": datetime.now().isoformat(), "phase": phase, "stage": stage, "spawn_config": spawn_config}, ensure_ascii=False) + "\n")
        
        print(f"📤 sessions_spawn 配置已生成")
        print(json.dumps(spawn_config, indent=2, ensure_ascii=False))
        
        return True
    
    def run_cycle(self):
        """运行一个阶段"""
        state = self._read_state()
        if state.get("paused"):
            print("⏸️ 已暂停")
            return False
        phase, stage = self._get_next_stage(state)
        if phase is None:
            print("✅ 已达最大循环次数")
            return False
        state["current_phase"], state["current_stage"] = phase, stage
        self._save_state(state)
        return self._execute_stage(phase, stage)
    
    def run_continuous(self):
        """持续运行"""
        print(f"\n{'='*60}")
        print(f"🚀 PDCA 自动执行器启动")
        print(f"📁 项目: {self.project_name}")
        print(f"{'='*60}\n")
        
        stage_delay = self.config["execution"].get("stage_delay_seconds", 60)
        
        while self.running:
            try:
                if not self.run_cycle():
                    break
                print(f"\n⏳ 等待 {stage_delay} 秒...")
                time.sleep(stage_delay)
                state = self._read_state()
                while state.get("paused") and self.running:
                    time.sleep(10)
                    state = self._read_state()
            except KeyboardInterrupt:
                self.running = False
                break
            except Exception as e:
                print(f"❌ 错误: {e}")
                time.sleep(60)
        
        print("\n👋 执行器已停止")
    
    def pause(self):
        state = self._read_state()
        state["paused"] = True
        self._save_state(state)
        print("⏸️ 已暂停")
    
    def resume(self):
        state = self._read_state()
        state["paused"] = False
        self._save_state(state)
        print("▶️ 已恢复")
    
    def status(self) -> dict:
        state = self._read_state()
        return {"project": self.project_name, "cycle": state.get("cycle", 0), "current_phase": state.get("current_phase"), "current_stage": state.get("current_stage"), "paused": state.get("paused", False)}


def main():
    parser = argparse.ArgumentParser(description="PDCA 自动执行器")
    parser.add_argument("--project", "-p", required=True, help="项目名称")
    parser.add_argument("--start", action="store_true", help="启动自动执行")
    parser.add_argument("--pause", action="store_true", help="暂停")
    parser.add_argument("--resume", action="store_true", help="恢复")
    parser.add_argument("--status", "-s", action="store_true", help="查看状态")
    parser.add_argument("--next", "-n", action="store_true", help="执行下一阶段")
    args = parser.parse_args()
    
    executor = PDCAAutoExecutor(project_name=args.project)
    
    if args.pause:
        executor.pause()
    elif args.resume:
        executor.resume()
    elif args.status:
        print(json.dumps(executor.status(), indent=2, ensure_ascii=False))
    elif args.next:
        executor.run_cycle()
    elif args.start:
        executor.run_continuous()
    else:
        print(json.dumps(executor.status(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    exit(main())