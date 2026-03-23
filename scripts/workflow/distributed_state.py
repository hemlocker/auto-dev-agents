"""
分布式状态管理 - 支持断点续传

状态文件分布：
- project.json                    # 项目根目录：项目元信息
- output/.stage_status.json       # 阶段执行状态
- output/{stage}/.subtask_status.json  # 子任务状态（与输出目录同级）
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict, field
import threading


@dataclass
class SubtaskStatus:
    """子任务状态"""
    name: str
    status: str  # pending, in_progress, completed, failed
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: Optional[int] = None
    output_dir: Optional[str] = None
    output_files_count: Optional[int] = None
    error: Optional[str] = None


@dataclass 
class StageStatus:
    """阶段状态"""
    name: str
    status: str  # pending, in_progress, completed, failed
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: Optional[int] = None
    subtasks: Dict[str, SubtaskStatus] = field(default_factory=dict)


@dataclass
class ProjectMeta:
    """项目元信息"""
    name: str
    project_name: Optional[str] = None
    package_name: Optional[str] = None
    package_path: Optional[str] = None
    backend_language: str = "java"
    frontend_framework: str = "vue"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class DistributedStateManager:
    """分布式状态管理器"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.output_dir = self.project_dir / "output"
        
        # 状态文件路径
        self.project_meta_file = self.project_dir / "project.json"
        self.stage_status_file = self.output_dir / ".stage_status.json"
        
        # 锁，防止并发写入
        self._lock = threading.Lock()
        
        # 确保目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    # ========== 项目元信息 ==========
    
    def load_project_meta(self) -> ProjectMeta:
        """加载项目元信息"""
        if self.project_meta_file.exists():
            try:
                data = json.loads(self.project_meta_file.read_text(encoding="utf-8"))
                return ProjectMeta(**data)
            except Exception as e:
                print(f"⚠️ 加载项目元信息失败: {e}")
        
        # 返回默认值
        return ProjectMeta(name=self.project_dir.name)
    
    def save_project_meta(self, meta: ProjectMeta):
        """保存项目元信息"""
        with self._lock:
            meta.updated_at = datetime.now().isoformat()
            if not meta.created_at:
                meta.created_at = meta.updated_at
            
            self.project_meta_file.write_text(
                json.dumps(asdict(meta), indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
    
    def update_project_meta(self, **kwargs):
        """更新项目元信息"""
        meta = self.load_project_meta()
        for key, value in kwargs.items():
            if hasattr(meta, key):
                setattr(meta, key, value)
        self.save_project_meta(meta)
        return meta
    
    # ========== 阶段状态 ==========
    
    def load_stage_status(self) -> Dict[str, StageStatus]:
        """加载所有阶段状态"""
        if self.stage_status_file.exists():
            try:
                data = json.loads(self.stage_status_file.read_text(encoding="utf-8"))
                stages = {}
                for name, stage_data in data.get("stages", {}).items():
                    subtasks = {}
                    for sub_name, sub_data in stage_data.get("subtasks", {}).items():
                        subtasks[sub_name] = SubtaskStatus(**sub_data)
                    stage_data["subtasks"] = subtasks
                    stages[name] = StageStatus(**stage_data)
                return stages
            except Exception as e:
                print(f"⚠️ 加载阶段状态失败: {e}")
        return {}
    
    def save_stage_status(self, stages: Dict[str, StageStatus]):
        """保存所有阶段状态"""
        with self._lock:
            data = {
                "current_phase": "",  # 由外部设置
                "current_stage": "",
                "stages": {}
            }
            
            for name, stage in stages.items():
                stage_dict = asdict(stage)
                stage_dict["subtasks"] = {
                    k: asdict(v) for k, v in stage.subtasks.items()
                }
                data["stages"][name] = stage_dict
            
            self.stage_status_file.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
    
    def get_stage(self, stage_name: str) -> StageStatus:
        """获取阶段状态"""
        stages = self.load_stage_status()
        if stage_name not in stages:
            stages[stage_name] = StageStatus(name=stage_name, status="pending")
        return stages[stage_name]
    
    def update_stage(self, stage_name: str, status: str = None, 
                     started_at: str = None, completed_at: str = None,
                     duration_ms: int = None):
        """更新阶段状态"""
        stages = self.load_stage_status()
        
        if stage_name not in stages:
            stages[stage_name] = StageStatus(name=stage_name, status="pending")
        
        stage = stages[stage_name]
        if status:
            stage.status = status
        if started_at:
            stage.started_at = started_at
        if completed_at:
            stage.completed_at = completed_at
        if duration_ms:
            stage.duration_ms = duration_ms
        
        self.save_stage_status(stages)
        return stage
    
    # ========== 子任务状态 ==========
    
    def get_subtask_status_file(self, stage: str) -> Path:
        """获取子任务状态文件路径"""
        # 根据 stage 确定目录
        stage_output_map = {
            "requirements": "requirements",
            "design": "design",
            "development": "src",
            "testing": "tests",
            "deployment": "deploy"
        }
        
        dir_name = stage_output_map.get(stage, stage)
        stage_dir = self.output_dir / dir_name
        stage_dir.mkdir(parents=True, exist_ok=True)
        
        return stage_dir / ".subtask_status.json"
    
    def load_subtask_status(self, stage: str) -> Dict[str, SubtaskStatus]:
        """加载子任务状态"""
        status_file = self.get_subtask_status_file(stage)
        
        if status_file.exists():
            try:
                data = json.loads(status_file.read_text(encoding="utf-8"))
                subtasks = {}
                for name, sub_data in data.get("subtasks", {}).items():
                    subtasks[name] = SubtaskStatus(**sub_data)
                return subtasks
            except Exception as e:
                print(f"⚠️ 加载子任务状态失败: {e}")
        return {}
    
    def save_subtask_status(self, stage: str, subtasks: Dict[str, SubtaskStatus]):
        """保存子任务状态"""
        status_file = self.get_subtask_status_file(stage)
        
        with self._lock:
            data = {
                "stage": stage,
                "updated_at": datetime.now().isoformat(),
                "subtasks": {k: asdict(v) for k, v in subtasks.items()}
            }
            
            status_file.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
    
    def get_subtask(self, stage: str, subtask_name: str) -> SubtaskStatus:
        """获取子任务状态"""
        subtasks = self.load_subtask_status(stage)
        if subtask_name not in subtasks:
            subtasks[subtask_name] = SubtaskStatus(name=subtask_name, status="pending")
        return subtasks[subtask_name]
    
    def update_subtask(self, stage: str, subtask_name: str, 
                       status: str = None,
                       started_at: str = None,
                       completed_at: str = None,
                       duration_ms: int = None,
                       output_dir: str = None,
                       output_files_count: int = None,
                       error: str = None):
        """更新子任务状态"""
        subtasks = self.load_subtask_status(stage)
        
        if subtask_name not in subtasks:
            subtasks[subtask_name] = SubtaskStatus(name=subtask_name, status="pending")
        
        subtask = subtasks[subtask_name]
        if status:
            subtask.status = status
        if started_at:
            subtask.started_at = started_at
        if completed_at:
            subtask.completed_at = completed_at
        if duration_ms is not None:
            subtask.duration_ms = duration_ms
        if output_dir:
            subtask.output_dir = output_dir
        if output_files_count is not None:
            subtask.output_files_count = output_files_count
        if error:
            subtask.error = error
        
        self.save_subtask_status(stage, subtasks)
        return subtask
    
    def start_subtask(self, stage: str, subtask_name: str) -> SubtaskStatus:
        """标记子任务开始"""
        return self.update_subtask(
            stage, subtask_name,
            status="in_progress",
            started_at=datetime.now().isoformat()
        )
    
    def complete_subtask(self, stage: str, subtask_name: str, 
                         duration_ms: int = None,
                         output_dir: str = None,
                         output_files_count: int = None) -> SubtaskStatus:
        """标记子任务完成"""
        return self.update_subtask(
            stage, subtask_name,
            status="completed",
            completed_at=datetime.now().isoformat(),
            duration_ms=duration_ms,
            output_dir=output_dir,
            output_files_count=output_files_count
        )
    
    def fail_subtask(self, stage: str, subtask_name: str, 
                     error: str = None) -> SubtaskStatus:
        """标记子任务失败"""
        return self.update_subtask(
            stage, subtask_name,
            status="failed",
            completed_at=datetime.now().isoformat(),
            error=error
        )
    
    # ========== 断点续传查询 ==========
    
    def get_pending_subtasks(self, stage: str, all_subtasks: List[str]) -> List[str]:
        """获取待执行的子任务列表"""
        subtasks = self.load_subtask_status(stage)
        
        pending = []
        for name in all_subtasks:
            if name not in subtasks:
                pending.append(name)
            elif subtasks[name].status == "pending":
                pending.append(name)
            elif subtasks[name].status == "failed":
                # 失败的任务可以重试
                pending.append(name)
            elif subtasks[name].status == "in_progress":
                # 检查是否超时（超过 30 分钟视为需要重试）
                started = subtasks[name].started_at
                if started:
                    started_time = datetime.fromisoformat(started)
                    elapsed = (datetime.now() - started_time).total_seconds()
                    if elapsed > 1800:  # 30 分钟
                        print(f"⚠️ 子任务 {name} 超时，将重试")
                        pending.append(name)
                    else:
                        print(f"⏳ 子任务 {name} 正在执行中，跳过")
                else:
                    pending.append(name)
            else:
                print(f"✅ 子任务 {name} 已完成，跳过")
        
        return pending
    
    def get_completed_subtasks(self, stage: str) -> List[str]:
        """获取已完成的子任务列表"""
        subtasks = self.load_subtask_status(stage)
        return [name for name, sub in subtasks.items() if sub.status == "completed"]
    
    def get_progress(self, stage: str, all_subtasks: List[str]) -> Dict[str, Any]:
        """获取执行进度"""
        subtasks = self.load_subtask_status(stage)
        
        completed = sum(1 for s in subtasks.values() if s.status == "completed")
        failed = sum(1 for s in subtasks.values() if s.status == "failed")
        in_progress = sum(1 for s in subtasks.values() if s.status == "in_progress")
        pending = len(all_subtasks) - completed - failed - in_progress
        
        return {
            "total": len(all_subtasks),
            "completed": completed,
            "failed": failed,
            "in_progress": in_progress,
            "pending": pending,
            "progress_percent": round(completed / len(all_subtasks) * 100, 1) if all_subtasks else 0
        }
    
    # ========== 调试工具 ==========
    
    def print_status(self, stage: str = None):
        """打印状态信息"""
        print("\n" + "=" * 60)
        print("📊 项目状态")
        print("=" * 60)
        
        # 项目元信息
        meta = self.load_project_meta()
        print(f"\n📁 项目: {meta.project_name or meta.name}")
        print(f"   包名: {meta.package_name or '未设置'}")
        
        # 阶段状态
        stages = self.load_stage_status()
        print(f"\n📅 阶段状态:")
        for name, stage in stages.items():
            status_emoji = {"completed": "✅", "in_progress": "🔄", "failed": "❌", "pending": "⏳"}
            print(f"   {status_emoji.get(stage.status, '❓')} {name}: {stage.status}")
        
        # 子任务状态
        if stage:
            print(f"\n📋 子任务状态 ({stage}):")
            subtasks = self.load_subtask_status(stage)
            for name, sub in subtasks.items():
                status_emoji = {"completed": "✅", "in_progress": "🔄", "failed": "❌", "pending": "⏳"}
                duration = f" ({sub.duration_ms // 1000}s)" if sub.duration_ms else ""
                print(f"   {status_emoji.get(sub.status, '❓')} {name}{duration}")
        
        print("\n" + "=" * 60)