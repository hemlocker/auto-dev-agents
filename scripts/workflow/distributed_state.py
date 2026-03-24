"""
分布式状态管理 - 支持断点续传和版本化增量更新

状态文件分布：
- project.json                    # 项目元信息
- input_state.json                # 输入文件状态（哈希）
- output/manifest.json            # 版本清单
- output/revision_history.json    # 修订历史
- output/.stage_status.json       # 阶段执行状态
- output/{stage}/.subtask_status.json  # 子任务状态
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any, Set
from dataclasses import dataclass, asdict, field
import threading

# 导入版本化模块
from .csv_parser import CSVInputParser, Requirement
from .manifest import ManifestManager
from .revision_history import RevisionHistoryManager, ChangeType


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
    input_hash: Optional[str] = None  # 新增：执行时的输入哈希


@dataclass 
class StageStatus:
    """阶段状态"""
    name: str
    status: str  # pending, in_progress, completed, failed
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: Optional[int] = None
    subtasks: Dict[str, SubtaskStatus] = field(default_factory=dict)
    input_hash: Optional[str] = None  # 新增：执行时的输入哈希


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


@dataclass
class InputChange:
    """输入变化"""
    path: str
    change_type: str  # new, modified, deleted
    old_hash: Optional[str] = None
    new_hash: Optional[str] = None


class DistributedStateManager:
    """分布式状态管理器 - 支持断点续传和版本化增量更新"""
    
    # 输入目录到阶段的映射
    INPUT_TO_STAGE = {
        "feedback": "requirement",
        "meetings": "requirement",
        "emails": "requirement",
        "tickets": "optimizer"
    }
    
    # 阶段依赖关系（下游依赖上游）
    STAGE_DEPS = {
        "design": ["requirement"],
        "development": ["design"],
        "testing": ["development"],
        "deployment": ["testing"],
        "operations": ["deployment"],
        "monitor": ["operations"],
        "optimizer": ["monitor"]
    }
    
    # 所有阶段（按执行顺序）
    ALL_STAGES = ["requirement", "design", "development", "testing", 
                  "deployment", "operations", "monitor", "optimizer"]
    
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.input_dir = self.project_dir / "input"
        self.output_dir = self.project_dir / "output"
        
        # 状态文件路径
        self.project_meta_file = self.project_dir / "project.json"
        self.input_state_file = self.project_dir / "input_state.json"
        self.stage_status_file = self.output_dir / ".stage_status.json"
        
        # 锁，防止并发写入
        self._lock = threading.Lock()
        
        # 确保目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 版本化管理器
        self.csv_parser = CSVInputParser(self.input_dir)
        self.manifest_manager = ManifestManager(self.project_dir)
        self.revision_manager = RevisionHistoryManager(self.output_dir)
    
    # ========== 项目元信息 ==========
    
    def load_project_meta(self) -> ProjectMeta:
        """加载项目元信息"""
        if self.project_meta_file.exists():
            try:
                data = json.loads(self.project_meta_file.read_text(encoding="utf-8"))
                # 只提取 ProjectMeta 定义的字段
                valid_fields = {"name", "project_name", "package_name", "package_path", 
                               "backend_language", "frontend_framework", "created_at", "updated_at"}
                filtered_data = {k: v for k, v in data.items() if k in valid_fields}
                return ProjectMeta(**filtered_data)
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
        # 根据 stage 确定目录（stage 名称 -> 输出目录名）
        stage_output_map = {
            "requirement": "requirements",   # 单数 stage 名映射到复数目录
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
    
    # ========== 增量更新功能 ==========
    
    def _file_hash(self, path: Path) -> str:
        """计算文件 MD5 哈希"""
        if not path.exists():
            return ""
        try:
            return hashlib.md5(path.read_bytes()).hexdigest()
        except Exception:
            return ""
    
    def _load_input_state(self) -> Dict:
        """加载输入文件状态"""
        if self.input_state_file.exists():
            try:
                return json.loads(self.input_state_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"file_hashes": {}, "last_scan": None}
    
    def _save_input_state(self, state: Dict):
        """保存输入文件状态"""
        with self._lock:
            state["last_scan"] = datetime.now().isoformat()
            self.input_state_file.write_text(
                json.dumps(state, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
    
    def scan_input_files(self) -> Dict[str, str]:
        """扫描所有输入文件并计算哈希"""
        hashes = {}
        
        if not self.input_dir.exists():
            return hashes
        
        for subdir in self.INPUT_TO_STAGE.keys():
            dir_path = self.input_dir / subdir
            if dir_path.exists():
                for f in dir_path.rglob("*"):
                    if f.is_file() and not f.name.startswith("."):
                        relative_path = f.relative_to(self.input_dir)
                        hashes[str(relative_path)] = self._file_hash(f)
        
        return hashes
    
    def detect_input_changes(self) -> Dict[str, Any]:
        """检测输入文件变化
        
        Returns:
            {
                "has_changes": bool,
                "changes": [InputChange, ...],
                "affected_stages": [str, ...],
                "affected_subtasks": {stage: [subtask, ...], ...}
            }
        """
        old_state = self._load_input_state()
        old_hashes = old_state.get("file_hashes", {})
        current_hashes = self.scan_input_files()
        
        # 检测变化
        changes = []
        for path, new_hash in current_hashes.items():
            if path not in old_hashes:
                changes.append(InputChange(path=path, change_type="new", new_hash=new_hash))
            elif old_hashes[path] != new_hash:
                changes.append(InputChange(
                    path=path, 
                    change_type="modified",
                    old_hash=old_hashes[path],
                    new_hash=new_hash
                ))
        
        for path, old_hash in old_hashes.items():
            if path not in current_hashes:
                changes.append(InputChange(path=path, change_type="deleted", old_hash=old_hash))
        
        # 分析受影响的阶段
        affected_stages = self._analyze_affected_stages(changes)
        
        # 分析受影响的子任务（更细粒度）
        affected_subtasks = self._analyze_affected_subtasks(changes, affected_stages)
        
        # 保存新状态
        self._save_input_state({"file_hashes": current_hashes})
        
        return {
            "has_changes": bool(changes),
            "changes": [asdict(c) for c in changes],
            "affected_stages": affected_stages,
            "affected_subtasks": affected_subtasks,
            "stats": {
                "total_files": len(current_hashes),
                "new": sum(1 for c in changes if c.change_type == "new"),
                "modified": sum(1 for c in changes if c.change_type == "modified"),
                "deleted": sum(1 for c in changes if c.change_type == "deleted")
            }
        }
    
    def _analyze_affected_stages(self, changes: List[InputChange]) -> List[str]:
        """分析受影响的阶段（包含依赖传播）"""
        directly_affected: Set[str] = set()
        
        for change in changes:
            subdir = change.path.split("/")[0]
            stage = self.INPUT_TO_STAGE.get(subdir)
            if stage:
                directly_affected.add(stage)
        
        # 传播到下游阶段
        all_affected = set(directly_affected)
        for stage in self.ALL_STAGES:
            deps = self.STAGE_DEPS.get(stage, [])
            if any(d in all_affected for d in deps):
                all_affected.add(stage)
        
        # 按执行顺序返回
        return [s for s in self.ALL_STAGES if s in all_affected]
    
    def _analyze_affected_subtasks(self, changes: List[InputChange], 
                                    affected_stages: List[str]) -> Dict[str, List[str]]:
        """分析受影响的子任务（细粒度增量）
        
        策略：
        1. requirement 阶段：所有子任务都要重跑（输入是整个需求）
        2. design/development 阶段：可以根据变化的模块推断受影响的子任务
        """
        affected_subtasks = {}
        
        for stage in affected_stages:
            # 获取该阶段的所有子任务
            subtask_status = self.load_subtask_status(stage)
            
            if not subtask_status:
                # 没有历史状态，需要执行所有子任务
                continue
            
            # 根据阶段和变化类型决定哪些子任务需要重跑
            if stage == "requirement":
                # 需求阶段：所有子任务都要重跑
                affected_subtasks[stage] = list(subtask_status.keys())
            
            elif stage == "design":
                # 设计阶段：依赖需求阶段的输出
                # 如果 requirement 有变化，所有设计子任务都要重跑
                if "requirement" in affected_stages:
                    affected_subtasks[stage] = list(subtask_status.keys())
            
            elif stage == "development":
                # 开发阶段：可以根据模块推断
                # 简化处理：如果上游有变化，所有开发子任务都要重跑
                if "design" in affected_stages or "requirement" in affected_stages:
                    affected_subtasks[stage] = list(subtask_status.keys())
            
            else:
                # 其他阶段：上游有变化则全部重跑
                deps = self.STAGE_DEPS.get(stage, [])
                if any(d in affected_stages for d in deps):
                    affected_subtasks[stage] = list(subtask_status.keys())
        
        return affected_subtasks
    
    def get_incremental_plan(self, stages_to_run: List[str] = None) -> Dict[str, Any]:
        """获取增量执行计划
        
        Args:
            stages_to_run: 指定要运行阶段（None 表示检测所有阶段）
        
        Returns:
            {
                "mode": "full" | "incremental" | "none",
                "reason": str,
                "stages_to_run": [str, ...],
                "subtasks_to_run": {stage: [subtask, ...], ...},
                "changes": {...}
            }
        """
        # 检测输入变化
        change_result = self.detect_input_changes()
        
        # 首次运行检测
        old_state = self._load_input_state()
        if not old_state.get("last_scan"):
            # 首次运行，全量执行
            return {
                "mode": "full",
                "reason": "首次运行",
                "stages_to_run": stages_to_run or self.ALL_STAGES,
                "subtasks_to_run": {},
                "changes": {}
            }
        
        # 无变化
        if not change_result["has_changes"]:
            return {
                "mode": "none",
                "reason": "输入无变化",
                "stages_to_run": [],
                "subtasks_to_run": {},
                "changes": {}
            }
        
        # 有变化，增量执行
        affected_stages = change_result["affected_stages"]
        
        # 如果指定了阶段，取交集
        if stages_to_run:
            affected_stages = [s for s in affected_stages if s in stages_to_run]
        
        # 🔧 关键改进：输入变化时，重置受影响阶段的所有子任务状态
        # 这样断点续传会重新执行这些子任务
        for stage in affected_stages:
            self._reset_stage_subtasks(stage)
        
        # 获取需要执行的子任务（现在会返回全部子任务）
        subtasks_to_run = {}
        for stage in affected_stages:
            all_subtasks = self._get_stage_subtasks(stage)
            subtasks_to_run[stage] = all_subtasks  # 输入变化时执行所有子任务
        
        return {
            "mode": "incremental",
            "reason": f"检测到 {len(change_result['changes'])} 个文件变化",
            "stages_to_run": affected_stages,
            "subtasks_to_run": subtasks_to_run,
            "changes": change_result
        }
    
    def _reset_stage_subtasks(self, stage: str):
        """重置阶段的所有子任务状态（用于增量更新）
        
        当输入变化时，需要重新执行该阶段的所有子任务
        """
        status_file = self.get_subtask_status_file(stage)
        
        if status_file.exists():
            try:
                data = json.loads(status_file.read_text(encoding="utf-8"))
                # 将所有子任务状态重置为 pending
                for subtask_name, subtask_data in data.get("subtasks", {}).items():
                    subtask_data["status"] = "pending"
                    subtask_data["started_at"] = None
                    subtask_data["completed_at"] = None
                    subtask_data["duration_ms"] = None
                
                status_file.write_text(
                    json.dumps(data, indent=2, ensure_ascii=False),
                    encoding="utf-8"
                )
                print(f"   🔄 已重置阶段 {stage} 的子任务状态")
            except Exception as e:
                print(f"   ⚠️ 重置阶段 {stage} 子任务状态失败: {e}")
    
    def _get_stage_subtasks(self, stage: str) -> List[str]:
        """获取阶段的所有子任务名称"""
        from workflow.models import STAGE_SUBTASKS
        subtasks = STAGE_SUBTASKS.get(stage, [])
        return [s.get("name", s) if isinstance(s, dict) else s for s in subtasks]
    
    def reset_incremental_state(self):
        """重置增量状态"""
        if self.input_state_file.exists():
            self.input_state_file.unlink()
        print("✅ 增量状态已重置")
    
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
        
        # 输入状态
        input_state = self._load_input_state()
        if input_state.get("last_scan"):
            print(f"\n📥 输入文件: {len(input_state.get('file_hashes', {}))} 个")
            print(f"   上次扫描: {input_state['last_scan']}")
        
        # 阶段状态
        stages = self.load_stage_status()
        print(f"\n📅 阶段状态:")
        for name in self.ALL_STAGES:
            stage = stages.get(name)
            if stage:
                status_emoji = {"completed": "✅", "in_progress": "🔄", "failed": "❌", "pending": "⏳"}
                print(f"   {status_emoji.get(stage.status, '❓')} {name}: {stage.status}")
            else:
                print(f"   ⏳ {name}: pending")
        
        # 子任务状态
        if stage:
            print(f"\n📋 子任务状态 ({stage}):")
            subtasks = self.load_subtask_status(stage)
            for name, sub in subtasks.items():
                status_emoji = {"completed": "✅", "in_progress": "🔄", "failed": "❌", "pending": "⏳"}
                duration = f" ({sub.duration_ms // 1000}s)" if sub.duration_ms else ""
                print(f"   {status_emoji.get(sub.status, '❓')} {name}{duration}")
        
        print("\n" + "=" * 60)
    
    # ========== 版本化管理 ==========
    
    def get_versioned_incremental_plan(self, stages_to_run: List[str] = None) -> Dict[str, Any]:
        """获取版本化增量执行计划
        
        Args:
            stages_to_run: 指定要运行阶段（None 表示检测所有阶段）
        
        Returns:
            {
                "mode": "full" | "incremental" | "none",
                "reason": str,
                "stages_to_run": [str, ...],
                "pending_versions": [str, ...],
                "new_requirements": [Requirement, ...],
                "stats": {...}
            }
        """
        # 获取所有版本
        all_versions = self.csv_parser.get_all_versions()
        
        if not all_versions:
            return {
                "mode": "none",
                "reason": "无版本数据",
                "stages_to_run": [],
                "pending_versions": [],
                "new_requirements": [],
                "stats": {}
            }
        
        # 获取已处理的版本
        processed = self.manifest_manager.get_processed_versions()
        
        # 找出待处理版本
        pending_versions = [v for v in all_versions if v not in processed]
        
        if not pending_versions:
            return {
                "mode": "none",
                "reason": "所有版本已处理",
                "stages_to_run": [],
                "pending_versions": [],
                "new_requirements": [],
                "stats": {}
            }
        
        # 获取待处理版本的需求
        new_requirements = []
        for version in pending_versions:
            reqs = self.csv_parser.parse_requirements(version)
            new_requirements.extend(reqs)
        
        # 统计
        by_priority = {}
        for req in new_requirements:
            p = req.priority or "Unknown"
            by_priority[p] = by_priority.get(p, 0) + 1
        
        stats = {
            "new_requirements": len(new_requirements),
            "by_priority": by_priority
        }
        
        # 确定执行模式
        if not processed:
            # 首次运行，全量执行
            mode = "full"
            reason = "首次运行"
        else:
            # 增量执行
            mode = "incremental"
            reason = f"检测到 {len(pending_versions)} 个新版本"
        
        # 确定要运行的阶段
        if stages_to_run:
            affected_stages = stages_to_run
        else:
            affected_stages = self.ALL_STAGES
        
        return {
            "mode": mode,
            "reason": reason,
            "stages_to_run": affected_stages,
            "pending_versions": pending_versions,
            "new_requirements": new_requirements,
            "stats": stats
        }
    
    def record_version_processed(self, version: str, requirements_added: int = 0):
        """记录版本已处理
        
        Args:
            version: 版本号
            requirements_added: 新增需求数量
        """
        self.manifest_manager.record_version_processed(
            version=version,
            input_files=[f.name for f in self.input_dir.glob("feedback/*.csv")],
            requirements_added=requirements_added
        )
    
    def reset_version_state(self):
        """重置版本状态"""
        self.manifest_manager.reset()
        print("✅ 版本状态已重置")
    
    def print_version_status(self):
        """打印版本状态"""
        all_versions = self.csv_parser.get_all_versions()
        processed = self.manifest_manager.get_processed_versions()
        pending = [v for v in all_versions if v not in processed]
        
        print(f"\n📋 所有版本: {all_versions}")
        print(f"✅ 已处理: {processed}")
        print(f"⏳ 待处理: {pending}")
        
        if pending:
            print(f"\n📊 待处理需求统计:")
            for version in pending:
                reqs = self.csv_parser.parse_requirements(version)
                by_priority = {}
                for req in reqs:
                    p = req.priority or "Unknown"
                    by_priority[p] = by_priority.get(p, 0) + 1
                print(f"   {version}: {len(reqs)} 项需求")
                if by_priority:
                    print(f"      优先级: {by_priority}")
        
        # 显示清单统计
        stats = self.manifest_manager.get_stats()
        if stats.get("total_versions", 0) > 0:
            print(f"\n📈 累计统计:")
            print(f"   已处理版本: {stats['total_versions']}")
            print(f"   总需求: {stats['total_requirements']}")
        
        print("\n" + "=" * 60)