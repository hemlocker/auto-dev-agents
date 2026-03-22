#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增量更新管理器
Incremental Update Manager

支持增量模式，只处理新增/变更的输入

使用方式：
  python3 scripts/incremental_update.py --project demo_project --analyze
"""

import argparse
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set


class IncrementalUpdateManager:
    """增量更新管理器"""
    
    def __init__(self, project_name: str, base_dir: str = None):
        self.project_name = project_name
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent
        self.project_dir = self.base_dir / "projects" / project_name
        self.input_dir = self.project_dir / "input"
        self.output_dir = self.project_dir / "output"
        self.state_file = self.project_dir / "incremental_state.json"
        
        # 输入目录映射到阶段
        self.input_to_stage = {
            "feedback": "requirement",
            "meetings": "requirement",
            "emails": "requirement",
            "tickets": "optimizer"
        }
        
        # 阶段依赖关系
        self.stage_deps = {
            "design": ["requirement"],
            "development": ["design"],
            "testing": ["development"],
            "deployment": ["testing"],
            "operations": ["deployment"],
            "monitor": ["operations"],
            "optimizer": ["monitor"]
        }
    
    def _file_hash(self, path: Path) -> str:
        if not path.exists():
            return ""
        try:
            return hashlib.md5(path.read_bytes()).hexdigest()
        except:
            return ""
    
    def _load_state(self) -> Dict:
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except:
                pass
        return {"input_hashes": {}, "completed_stages": [], "last_run": None}
    
    def _save_state(self, state: Dict):
        state["last_run"] = datetime.now().isoformat()
        self.state_file.write_text(json.dumps(state, indent=2, ensure_ascii=False))
    
    def scan_inputs(self) -> Dict[str, str]:
        """扫描输入文件"""
        hashes = {}
        for subdir in ["feedback", "meetings", "emails", "tickets"]:
            dir_path = self.input_dir / subdir
            if dir_path.exists():
                for f in dir_path.rglob("*"):
                    if f.is_file():
                        hashes[f"{subdir}/{f.name}"] = self._file_hash(f)
        return hashes
    
    def detect_changes(self) -> Dict:
        """检测输入变化"""
        state = self._load_state()
        old = state.get("input_hashes", {})
        current = self.scan_inputs()
        
        changes = {
            "new": [f for f in current if f not in old],
            "modified": [f for f in current if f in old and old[f] != current[f]],
            "deleted": [f for f in old if f not in current]
        }
        changes["has_changes"] = bool(changes["new"] or changes["modified"] or changes["deleted"])
        
        state["input_hashes"] = current
        self._save_state(state)
        return changes
    
    def analyze_impact(self, changes: Dict) -> List[str]:
        """分析受影响的阶段"""
        affected = set()
        
        for file_path in changes["new"] + changes["modified"] + changes["deleted"]:
            subdir = file_path.split("/")[0]
            stage = self.input_to_stage.get(subdir)
            if stage:
                affected.add(stage)
        
        # 传播到下游
        all_stages = ["requirement", "design", "development", "testing", 
                      "deployment", "operations", "monitor", "optimizer"]
        expanded = set(affected)
        for stage in all_stages:
            deps = self.stage_deps.get(stage, [])
            if any(d in expanded for d in deps):
                expanded.add(stage)
        
        return [s for s in all_stages if s in expanded]
    
    def get_plan(self) -> Dict:
        """获取增量更新计划"""
        state = self._load_state()
        
        # 首次运行 - 保存当前状态
        if not state.get("last_run"):
            current = self.scan_inputs()
            state["input_hashes"] = current
            state["last_run"] = datetime.now().isoformat()
            self._save_state(state)
            return {
                "mode": "full",
                "reason": "首次运行",
                "stages": ["requirement", "design", "development", "testing",
                           "deployment", "operations", "monitor", "optimizer"]
            }
        
        changes = self.detect_changes()
        if not changes["has_changes"]:
            return {"mode": "none", "reason": "无变化", "stages": []}
        
        stages = self.analyze_impact(changes)
        return {
            "mode": "incremental",
            "reason": "检测到输入变化",
            "changes": changes,
            "stages": stages
        }
    
    def mark_complete(self, stage: str):
        """标记阶段完成"""
        state = self._load_state()
        if stage not in state.get("completed_stages", []):
            state.setdefault("completed_stages", []).append(stage)
        self._save_state(state)
    
    def reset(self):
        """重置状态"""
        if self.state_file.exists():
            self.state_file.unlink()


def main():
    parser = argparse.ArgumentParser(description="增量更新管理器")
    parser.add_argument("--project", "-p", required=True)
    parser.add_argument("--analyze", "-a", action="store_true")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--complete", help="标记阶段完成")
    
    args = parser.parse_args()
    manager = IncrementalUpdateManager(project_name=args.project)
    
    if args.reset:
        manager.reset()
        print(json.dumps({"status": "reset"}))
    elif args.complete:
        manager.mark_complete(args.complete)
        print(json.dumps({"completed": args.complete}))
    else:
        result = manager.get_plan()
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    exit(main())