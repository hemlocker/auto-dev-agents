#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
输入监控触发器
Input Monitor & Trigger

监控项目 input 目录，发现新内容自动触发 PDCA 流程

工作原理：
1. 监控 projects/{project}/input/ 目录变化
2. 检测到新文件 → 触发需求分析
3. 自动执行完整 PDCA 循环
4. 循环完成后继续监控，等待新输入
"""

import argparse
import json
import hashlib
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Set


class InputMonitor:
    """输入目录监控器"""
    
    def __init__(self, project_name: str, base_dir: str = None):
        self.project_name = project_name
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent
        self.project_dir = self.base_dir / "projects" / project_name
        self.input_dir = self.project_dir / "input"
        self.state_file = self.project_dir / "monitor_state.json"
        self.running = True
        self.watch_dirs = ["feedback", "meetings", "emails", "tickets"]
    
    def _load_state(self) -> dict:
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {"file_hashes": {}, "last_check": None, "trigger_count": 0, "last_trigger": None}
    
    def _save_state(self, state: dict):
        state["last_check"] = datetime.now().isoformat()
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    
    def _compute_file_hash(self, file_path: Path) -> str:
        try:
            with open(file_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return ""
    
    def _scan_input_files(self) -> Dict[str, str]:
        files = {}
        for subdir in self.watch_dirs:
            dir_path = self.input_dir / subdir
            if dir_path.exists():
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file():
                        relative_path = str(file_path.relative_to(self.input_dir))
                        files[relative_path] = self._compute_file_hash(file_path)
        return files
    
    def check_for_changes(self) -> dict:
        state = self._load_state()
        old_hashes = state.get("file_hashes", {})
        current_files = self._scan_input_files()
        
        changes = {"new_files": [], "modified_files": [], "deleted_files": [], "has_changes": False, "trigger_needed": False}
        
        for file_path, file_hash in current_files.items():
            if file_path not in old_hashes:
                changes["new_files"].append(file_path)
                changes["has_changes"] = True
            elif old_hashes[file_path] != file_hash:
                changes["modified_files"].append(file_path)
                changes["has_changes"] = True
        
        for file_path in old_hashes:
            if file_path not in current_files:
                changes["deleted_files"].append(file_path)
                changes["has_changes"] = True
        
        if changes["new_files"] or changes["modified_files"]:
            changes["trigger_needed"] = True
        
        state["file_hashes"] = current_files
        self._save_state(state)
        return changes
    
    def generate_trigger_task(self, changes: dict) -> dict:
        state = self._load_state()
        state["trigger_count"] = state.get("trigger_count", 0) + 1
        state["last_trigger"] = datetime.now().isoformat()
        self._save_state(state)
        
        pdca_state = {
            "cycle": 0, "current_phase": None, "current_stage": None,
            "history": [], "paused": False,
            "triggered_by": "input_change",
            "trigger_files": changes["new_files"] + changes["modified_files"],
            "trigger_time": datetime.now().isoformat()
        }
        pdca_file = self.project_dir / "pdca_state.json"
        with open(pdca_file, "w", encoding="utf-8") as f:
            json.dump(pdca_state, f, indent=2, ensure_ascii=False)
        
        task = f"""# 项目: {self.project_name} | 自动触发: 需求分析

## 触发原因
检测到输入目录变化：
- 新增文件: {len(changes['new_files'])} 个
- 修改文件: {len(changes['modified_files'])} 个

## 变化文件
{chr(10).join('- ' + f for f in (changes['new_files'] + changes['modified_files'])[:10])}

## 任务
1. 扫描 projects/{self.project_name}/input/ 目录
2. 分析新的用户反馈、工单、邮件、会议记录
3. 更新需求文档到 output/requirements/
4. 触发后续设计、开发、测试、部署流程

## 输入目录
{self.input_dir}

## 输出目录
{self.project_dir}/output/requirements/
"""
        
        return {
            "action": "sessions_spawn",
            "params": {
                "runtime": "subagent",
                "mode": "run",
                "task": task,
                "cwd": str(self.base_dir),
                "timeoutSeconds": 1800,
                "label": f"{self.project_name}_auto_requirement"
            },
            "trigger_info": {
                "new_files": changes["new_files"],
                "modified_files": changes["modified_files"],
                "trigger_count": state["trigger_count"]
            }
        }
    
    def run_continuous(self, check_interval: int = 30):
        print(f"\n{'='*60}")
        print(f"👁️ 输入监控器启动")
        print(f"📁 项目: {self.project_name}")
        print(f"📂 监控目录: {self.input_dir}")
        print(f"⏱️ 检查间隔: {check_interval}秒")
        print(f"{'='*60}\n")
        
        while self.running:
            try:
                changes = self.check_for_changes()
                
                if changes["trigger_needed"]:
                    print(f"\n🔔 [{datetime.now().strftime('%H:%M:%S')}] 检测到输入变化!")
                    print(f"   新增: {len(changes['new_files'])} 文件")
                    print(f"   修改: {len(changes['modified_files'])} 文件")
                    trigger = self.generate_trigger_task(changes)
                    print(f"\n📤 自动触发 PDCA 流程:\n{json.dumps(trigger['params'], indent=2, ensure_ascii=False)}")
                    return trigger
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 无变化，继续监控...")
                
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                self.running = False
                break
            except Exception as e:
                print(f"❌ 错误: {e}")
                time.sleep(10)
        
        print("\n👋 监控器已停止")
    
    def status(self) -> dict:
        state = self._load_state()
        current_files = self._scan_input_files()
        return {
            "project": self.project_name,
            "input_dir": str(self.input_dir),
            "watched_dirs": self.watch_dirs,
            "total_files": len(current_files),
            "trigger_count": state.get("trigger_count", 0),
            "last_check": state.get("last_check"),
            "last_trigger": state.get("last_trigger")
        }


def main():
    parser = argparse.ArgumentParser(description="输入监控触发器")
    parser.add_argument("--project", "-p", required=True, help="项目名称")
    parser.add_argument("--start", action="store_true", help="启动持续监控")
    parser.add_argument("--check", "-c", action="store_true", help="检查一次变化")
    parser.add_argument("--status", "-s", action="store_true", help="查看状态")
    parser.add_argument("--interval", "-i", type=int, default=30, help="检查间隔（秒）")
    
    args = parser.parse_args()
    monitor = InputMonitor(project_name=args.project)
    
    if args.status:
        print(json.dumps(monitor.status(), indent=2, ensure_ascii=False))
    elif args.check:
        changes = monitor.check_for_changes()
        print(json.dumps(changes, indent=2, ensure_ascii=False))
        if changes["trigger_needed"]:
            trigger = monitor.generate_trigger_task(changes)
            print(f"\n触发任务:\n{json.dumps(trigger, indent=2, ensure_ascii=False)}")
    elif args.start:
        monitor.run_continuous(check_interval=args.interval)
    else:
        print(json.dumps(monitor.status(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    exit(main())