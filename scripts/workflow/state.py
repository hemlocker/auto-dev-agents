# -*- coding: utf-8 -*-
"""
工作流状态管理
简化版状态管理，专注于 WorkflowExecutor 需要的功能
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List


class WorkflowState:
    """工作流状态管理器"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.state_file = project_dir / "workflow_state.json"
        self.log_file = project_dir / "logs" / "workflow.jsonl"
        
        # 确保目录存在
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def read(self) -> dict:
        """读取状态"""
        if not self.state_file.exists():
            return {
                "cycle": 0,
                "current_phase": None,
                "current_stage": None,
                "paused": False,
                "history": []
            }
        try:
            return json.loads(self.state_file.read_text(encoding="utf-8"))
        except:
            return {
                "cycle": 0,
                "current_phase": None,
                "current_stage": None,
                "paused": False,
                "history": []
            }
    
    def write(self, state: dict):
        """写入状态"""
        state["updated_at"] = datetime.now().isoformat()
        self.state_file.write_text(
            json.dumps(state, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
    
    def log(self, phase: str, stage: str, spawn_config: dict):
        """记录执行日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "cycle": self.read().get("cycle", 0),
            "phase": phase,
            "stage": stage,
            "spawn_config": spawn_config
        }
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    def get_status(self) -> dict:
        """获取状态摘要"""
        state = self.read()
        return {
            "cycle": state.get("cycle", 0),
            "current_phase": state.get("current_phase"),
            "current_stage": state.get("current_stage"),
            "paused": state.get("paused", False),
            "history_count": len(state.get("history", []))
        }
    
    def pause(self):
        """暂停工作流"""
        state = self.read()
        state["paused"] = True
        self.write(state)
    
    def resume(self):
        """恢复工作流"""
        state = self.read()
        state["paused"] = False
        self.write(state)
    
    def reset(self):
        """重置状态"""
        self.write({
            "cycle": 0,
            "current_phase": None,
            "current_stage": None,
            "paused": False,
            "history": []
        })
    
    def update_stage(self, phase: str, stage: str):
        """更新当前阶段"""
        state = self.read()
        state["current_phase"] = phase
        state["current_stage"] = stage
        self.write(state)
    
    def record_cycle_complete(self):
        """记录循环完成"""
        state = self.read()
        state["history"].append({
            "cycle": state["cycle"],
            "completed_at": datetime.now().isoformat()
        })
        state["cycle"] = state.get("cycle", 0) + 1
        self.write(state)