# -*- coding: utf-8 -*-
"""
统一状态门面 (State Facade)
Unified State Facade

整合 WorkflowState、StateManager、DistributedStateManager 为单一入口，
解决三套状态管理系统并存的问题。

使用方式：
  from scripts.workflow.state_facade import WorkflowFacade

  facade = WorkflowFacade(project_dir=Path("projects/my-project"))

  # 工作流控制（来自 WorkflowState）
  facade.load_state()           # 读取状态
  facade.save_state(state)     # 写入状态
  facade.pause()           # 暂停
  facade.resume()          # 恢复
  facade.reset()           # 重置
  facade.update_stage()    # 更新阶段
  facade.get_status()     # 获取状态摘要

  # 阶段/子任务状态（来自 DistributedStateManager）
  facade.update_stage_status()     # 更新阶段状态
  facade.start_subtask()          # 开始子任务
  facade.complete_subtask()       # 完成子任务
  facade.fail_subtask()          # 子任务失败
  facade.get_progress()          # 获取进度
  facade.print_status()          # 打印状态

  # 统一上下文（来自 StateManager）
  facade.get_section()          # 获取状态片段
  facade.update_state()          # 更新状态字段
  facade.log_event()             # 记录事件
  facade.record_execution_log()  # 记录执行日志
  facade.record_decision()       # 记录决策
  facade.record_cycle_complete() # 记录循环完成
  facade.get_decisions()         # 获取决策

设计说明：
- WorkflowState：基础工作流状态（暂停/恢复/重置/日志）
- DistributedStateManager：阶段/子任务粒度的断点续传
- StateManager：智能体状态、决策记录、事件日志、反馈追踪

使用门面模式，将三个管理器的职责统一到一个类中，
避免调用方在多个状态管理器之间切换。
"""

import json
import logging
import re
import hashlib
import threading
import warnings
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any, Set, Tuple
from dataclasses import dataclass, asdict, field


logger = logging.getLogger(__name__)


# ==================== 内部数据类 ====================

# 导入版本化管理模块
from .csv_parser import CSVInputParser, Requirement
from .manifest import ManifestManager
from .revision_history import RevisionHistoryManager


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
    input_hash: Optional[str] = None


@dataclass
class StageStatus:
    """阶段状态"""
    name: str
    status: str  # pending, in_progress, completed, failed
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: Optional[int] = None
    subtasks: Dict[str, SubtaskStatus] = field(default_factory=dict)
    input_hash: Optional[str] = None


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


# ==================== 统一状态门面 ====================

class WorkflowFacade:
    """
    统一状态门面 - 整合三套状态管理系统的单一入口

    职责：
    1. 基础工作流状态（来自 WorkflowState）
       - cycle, current_phase, current_stage, paused, history
    2. 阶段/子任务状态（来自 DistributedStateManager）
       - stage_status.json, subtask status files, project.json, input_state.json
    3. 统一上下文（来自 StateManager）
       - agents, context/decisions, events, feedback, quality

    设计说明：
    - 替代 WorkflowState、DistributedStateManager、StateManager 三个独立管理器
    - 提供统一的 API 入口，消除调用方的选择困难
    - 保持向后兼容，支持渐进式迁移
    """

    # 阶段列表（按执行顺序）
    ALL_STAGES = ["requirement", "design", "development", "testing",
                  "deployment", "operations", "monitor", "optimizer"]

    # 阶段依赖关系
    STAGE_DEPS = {
        "design": ["requirement"],
        "development": ["design"],
        "testing": ["development"],
        "deployment": ["testing"],
        "operations": ["deployment"],
        "monitor": ["operations"],
        "optimizer": ["monitor"]
    }

    # PDCA 阶段映射
    PHASE_MAP = {
        "plan": ["requirement", "design"],
        "do": ["development", "testing", "deployment"],
        "check": ["operations", "monitor"],
        "act": ["optimizer"]
    }

    # 智能体列表
    AGENTS = ["coordinator", "requirement", "design", "development",
              "testing", "deployment", "operations", "monitor", "optimizer"]

    def __init__(self, project_dir: Path, base_dir: Path = None):
        self.project_dir = Path(project_dir)
        self.base_dir = Path(base_dir) if base_dir else self.project_dir.parent.parent
        self._lock = threading.Lock()

        # 加载配置文件（从 base_dir 读取）
        self._config = self._load_config()
        self.config = self._config  # 暴露给外部模块

        # 从配置中读取输入输出目录（stage 级别配置优先）
        self._stage_configs = self._build_stage_configs()

        # 输入输出基础路径（来自配置或默认值）
        self.input_dir = self.project_dir / self._config.get("input_dir", "input")
        self.output_dir = self.project_dir / self._config.get("output_dir", "output")

        # 状态文件路径
        self._state_file = self.project_dir / "workflow_state.json"
        self._log_file = self.project_dir / "logs" / "workflow.jsonl"
        self._project_meta_file = self.project_dir / "project.json"
        self._input_state_file = self.project_dir / "input_state.json"
        self._stage_status_file = self.output_dir / ".stage_status.json"
        self._unified_state_file = self.project_dir / "state" / "state.json"
        self._events_file = self.project_dir / "state" / "events.jsonl"
        self._history_dir = self.project_dir / "state" / "history"

        # 确保目录存在
        self._log_file.parent.mkdir(parents=True, exist_ok=True)
        self._unified_state_file.parent.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 版本化管理器
        self.csv_parser = CSVInputParser(self.input_dir)
        self.manifest_manager = ManifestManager(self.project_dir)
        self.revision_manager = RevisionHistoryManager(self.output_dir)

    # ========== 配置加载（读取 config.yaml）==========

    def _load_config(self) -> dict:
        """从 base_dir/config.yaml 加载配置（config.yaml 为唯一真相源）"""
        config_path = self.base_dir / "config.yaml"
        # 与 config.yaml 相同的默认值；config.yaml 存在时以其为准
        default_config = {
            "input_dir": "input",
            "output_dir": "output",
            "stages": {},
            "pdca": {"max_cycles": 0, "cycle_interval_seconds": 60},
            "execution": {
                "mode": "auto",
                "stage_delay_seconds": 30,
                "timeout_seconds": 1800,
                "subtask": {"enabled": True, "delay_seconds": 5, "continue_on_failure": True},
                "context": {
                    "max_input_tokens": 150000,
                    "max_file_size_kb": 150,
                    "max_file_count": 50,
                    "batch_size": 15,
                    "output_reserve_tokens": 16384,
                },
            },
            "input_monitor": {"check_interval_seconds": 30, "default_timeout_seconds": 1800, "monitor_sleep_seconds": 10},
            "token_estimation": {
                "ratio_cjk": 1.8, "ratio_latin": 4.0, "ratio_code": 3.5, "ratio_mixed": 2.5,
                "max_sample_mb": 2, "cjk_ratio_threshold": 0.15, "mixed_ratio_threshold": 0.02,
            },
            "engine": {
                "http_timeout_seconds": 30, "http_timeout_short": 10, "subtask_timeout_add": 5,
                "wait_active_max_seconds": 300, "wait_active_first_seconds": 60,
                "stage_timeout_default": 1800, "stage_timeout_max": 3600,
                "subtask_in_progress_threshold": 1800, "status_print_interval_seconds": 30,
            },
        }
        if not config_path.exists():
            return default_config
        try:
            import yaml
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                if not config:
                    return default_config
                # 深度合并：default_config 填充 config 中的缺失字段
                return self._deep_merge(default_config, config)
        except (ImportError, Exception):
            return self._load_config_fallback(config_path, default_config)

    def _deep_merge(self, defaults: dict, overrides: dict) -> dict:
        """深度合并：defaults 为基础，overrides 的值覆盖（保留嵌套结构）"""
        result = defaults.copy()
        for key, value in overrides.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def _load_config_fallback(self, config_path: Path, default_config: dict) -> dict:
        """无法解析 YAML 时，从纯文本提取关键配置"""
        try:
            content = config_path.read_text(encoding="utf-8")
            config = default_config.copy()
            for key, default in [("input_dir", "input"), ("output_dir", "output")]:
                m = re.search(rf"^{key}:\s*(.+?)$", content, re.MULTILINE)
                if m:
                    config[key] = m.group(1).strip().strip('"\'')
            return config
        except (OSError, IOError):
            return default_config

    def _build_stage_configs(self) -> Dict[str, dict]:
        """从配置构建各阶段的输入输出映射"""
        stage_map = {}
        # 优先从 workflow.stages 读取（与 run.py 保持一致）
        stages_cfg = self._config.get("workflow", {}).get("stages", [])
        if not stages_cfg:
            stages_cfg = self._config.get("stages", {})
        if not stages_cfg:
            # config.yaml 中无 stages，使用默认值
            defaults = {
                "requirement": ("input/", "output/requirements/"),
                "design": ("output/requirements/", "output/design/"),
                "development": ("output/design/", "output/src/"),
                "testing": ("output/src/", "output/tests/"),
                "deployment": ("output/tests/", "output/deploy/"),
                "operations": ("output/deploy/", "output/operations/"),
                "monitor": ("output/", "output/monitor/"),
                "optimizer": ("output/monitor/", "output/optimizer/"),
            }
            for name, (inp, out) in defaults.items():
                stage_map[name] = {"input": inp, "output": out}
        elif isinstance(stages_cfg, list):
            # stages 是 list: [{name, input, output}, ...]
            for cfg in stages_cfg:
                name = cfg.get("name")
                if name:
                    stage_map[name] = {
                        "input": cfg.get("input", "input/"),
                        "output": cfg.get("output", f"output/{name}/")
                    }
        elif isinstance(stages_cfg, dict):
            # stages 是 dict: {stage_name: {input, output}}
            for name, cfg in stages_cfg.items():
                stage_map[name] = {
                    "input": cfg.get("input", f"output/{name}/") if name != "requirement" else "input/",
                    "output": cfg.get("output", f"output/{name}/")
                }
        return stage_map

    # ========== 路径工具方法 ==========

    def get_input_dir(self, stage: str = None) -> Path:
        """获取指定阶段的输入目录"""
        if stage and stage in self._stage_configs:
            stage_input = self._stage_configs[stage].get("input", "input/")
            # 相对路径基于 project_dir，绝对路径直接使用
            if stage_input.startswith("/") or stage_input.startswith("."):
                return self.project_dir / stage_input
            # 相对路径：可能是 output/xxx/ 或 input/ 开头的
            if stage_input.startswith("output/") or stage_input.startswith("input/"):
                return self.project_dir / stage_input
            return self.project_dir / stage_input
        return self.input_dir

    def get_output_dir(self, stage: str = None) -> Path:
        """获取指定阶段的输出目录"""
        if stage and stage in self._stage_configs:
            stage_output = self._stage_configs[stage].get("output", f"output/{stage}/")
            if stage_output.startswith("/") or stage_output.startswith("."):
                return self.project_dir / stage_output
            return self.project_dir / stage_output
        return self.output_dir

    # ========== 基础工作流状态（来自 WorkflowState）==========

    def load_state(self) -> dict:
        """读取基础工作流状态"""
        if not self._state_file.exists():
            return self._default_state()
        try:
            return json.loads(self._state_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return self._default_state()

    def save_state(self, state: dict):
        """写入基础工作流状态"""
        state["updated_at"] = datetime.now().isoformat()
        self._state_file.write_text(
            json.dumps(state, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def read(self) -> dict:
        """[已废弃] 使用 load_state() 替代"""
        warnings.warn("read() 已废弃，请使用 load_state()", DeprecationWarning, stacklevel=2)
        return self.load_state()

    def write(self, state: dict):
        """[已废弃] 使用 save_state() 替代"""
        warnings.warn("write() 已废弃，请使用 save_state()", DeprecationWarning, stacklevel=2)
        self.save_state(state)

    def log(self, phase: str, stage: str, spawn_config: dict):
        """[已废弃] 使用 record_execution_log() 替代"""
        warnings.warn("log() 已废弃，请使用 record_execution_log()", DeprecationWarning, stacklevel=2)
        self.record_execution_log(phase, stage, spawn_config)

    def _default_state(self) -> dict:
        return {
            "cycle": 0,
            "current_phase": None,
            "current_stage": None,
            "paused": False,
            "history": [],
            "updated_at": datetime.now().isoformat()
        }

    def pause(self):
        """暂停工作流"""
        state = self.load_state()
        state["paused"] = True
        self.save_state(state)

    def resume(self):
        """恢复工作流"""
        state = self.load_state()
        state["paused"] = False
        self.save_state(state)

    def reset(self):
        """重置状态"""
        self.save_state(self._default_state())

    def update_stage(self, phase: str, stage: str):
        """更新当前阶段"""
        state = self.load_state()
        state["current_phase"] = phase
        state["current_stage"] = stage
        self.save_state(state)

    def record_execution_log(self, phase: str, stage: str, spawn_config: dict):
        """记录执行日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "cycle": self.load_state().get("cycle", 0),
            "phase": phase,
            "stage": stage,
            "spawn_config": spawn_config
        }
        with open(self._log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    def record_cycle_complete(self):
        """记录循环完成"""
        state = self.load_state()
        state["history"].append({
            "cycle": state.get("cycle", 0),
            "completed_at": datetime.now().isoformat()
        })
        state["cycle"] = state.get("cycle", 0) + 1
        self.save_state(state)

    def get_status(self) -> dict:
        """获取状态摘要"""
        state = self.load_state()
        return {
            "cycle": state.get("cycle", 0),
            "current_phase": state.get("current_phase"),
            "current_stage": state.get("current_stage"),
            "paused": state.get("paused", False),
            "history_count": len(state.get("history", []))
        }

    # ========== 阶段/子任务状态（来自 DistributedStateManager）==========

    def _get_subtask_status_file(self, stage: str) -> Path:
        """获取子任务状态文件路径（从配置读取输出目录）"""
        stage_dir = self.get_output_dir(stage)
        stage_dir.mkdir(parents=True, exist_ok=True)
        return stage_dir / ".subtask_status.json"

    def load_stage_status(self) -> Dict[str, StageStatus]:
        """加载所有阶段状态"""
        if self._stage_status_file.exists():
            try:
                data = json.loads(self._stage_status_file.read_text(encoding="utf-8"))
                stages = {}
                for name, stage_data in data.get("stages", {}).items():
                    subtasks = {}
                    for sub_name, sub_data in stage_data.get("subtasks", {}).items():
                        subtasks[sub_name] = SubtaskStatus(**sub_data)
                    stage_data["subtasks"] = subtasks
                    stages[name] = StageStatus(**stage_data)
                return stages
            except (json.JSONDecodeError, OSError, TypeError):
                pass
        return {}

    def save_stage_status(self, stages: Dict[str, StageStatus]):
        """保存所有阶段状态"""
        with self._lock:
            data = {
                "current_phase": "",
                "current_stage": "",
                "stages": {}
            }
            for name, stage in stages.items():
                stage_dict = asdict(stage)
                stage_dict["subtasks"] = {k: asdict(v) for k, v in stage.subtasks.items()}
                data["stages"][name] = stage_dict
            self._stage_status_file.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )

    def update_stage_status(self, stage_name: str, status: str = None,
                            started_at: str = None, completed_at: str = None,
                            duration_ms: int = None) -> StageStatus:
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

    def load_subtask_status(self, stage: str) -> Dict[str, SubtaskStatus]:
        """加载子任务状态"""
        status_file = self._get_subtask_status_file(stage)
        if status_file.exists():
            try:
                data = json.loads(status_file.read_text(encoding="utf-8"))
                subtasks = {}
                for name, sub_data in data.get("subtasks", {}).items():
                    subtasks[name] = SubtaskStatus(**sub_data)
                return subtasks
            except (json.JSONDecodeError, OSError, TypeError):
                pass
        return {}

    def save_subtask_status(self, stage: str, subtasks: Dict[str, SubtaskStatus]):
        """保存子任务状态"""
        status_file = self._get_subtask_status_file(stage)
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

    def start_subtask(self, stage: str, subtask_name: str) -> SubtaskStatus:
        """标记子任务开始"""
        subtasks = self.load_subtask_status(stage)
        if subtask_name not in subtasks:
            subtasks[subtask_name] = SubtaskStatus(name=subtask_name, status="pending")
        subtask = subtasks[subtask_name]
        subtask.status = "in_progress"
        subtask.started_at = datetime.now().isoformat()
        self.save_subtask_status(stage, subtasks)
        return subtask

    def complete_subtask(self, stage: str, subtask_name: str,
                         duration_ms: int = None,
                         output_dir: str = None,
                         output_files_count: int = None) -> SubtaskStatus:
        """标记子任务完成"""
        subtasks = self.load_subtask_status(stage)
        if subtask_name not in subtasks:
            subtasks[subtask_name] = SubtaskStatus(name=subtask_name, status="pending")
        subtask = subtasks[subtask_name]
        subtask.status = "completed"
        subtask.completed_at = datetime.now().isoformat()
        if duration_ms is not None:
            subtask.duration_ms = duration_ms
        if output_dir:
            subtask.output_dir = output_dir
        if output_files_count is not None:
            subtask.output_files_count = output_files_count
        self.save_subtask_status(stage, subtasks)
        return subtask

    def fail_subtask(self, stage: str, subtask_name: str,
                     error: str = None) -> SubtaskStatus:
        """标记子任务失败"""
        subtasks = self.load_subtask_status(stage)
        if subtask_name not in subtasks:
            subtasks[subtask_name] = SubtaskStatus(name=subtask_name, status="pending")
        subtask = subtasks[subtask_name]
        subtask.status = "failed"
        subtask.completed_at = datetime.now().isoformat()
        if error:
            subtask.error = error
        self.save_subtask_status(stage, subtasks)
        return subtask

    def get_pending_subtasks(self, stage: str, all_subtasks: List[str]) -> List[str]:
        """获取待执行的子任务列表（断点续传）"""
        subtasks = self.load_subtask_status(stage)
        pending = []
        for name in all_subtasks:
            if name not in subtasks:
                pending.append(name)
            elif subtasks[name].status == "pending":
                pending.append(name)
            elif subtasks[name].status == "failed":
                pending.append(name)
            elif subtasks[name].status == "in_progress":
                started = subtasks[name].started_at
                if started:
                    try:
                        elapsed = (datetime.now() - datetime.fromisoformat(started)).total_seconds()
                        threshold = self.config.get("engine", {}).get("subtask_in_progress_threshold", 1800)
                        if elapsed > threshold:
                            pending.append(name)
                        else:
                            logger.info("⏳ 子任务 %s 正在执行中，跳过", name)
                    except (ValueError, OSError):
                        pending.append(name)
                else:
                    pending.append(name)
            else:
                logger.info("✅ 子任务 %s 已完成，跳过", name)
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

    def print_status(self, stage: str = None):
        """打印状态信息"""
        logger.info("\n%s", "=" * 60)
        logger.info("📊 项目状态")
        logger.info("%s", "=" * 60)

        # 基础工作流状态
        basic = self.load_state()
        logger.info("📅 工作流: cycle=%s, phase=%s, stage=%s",
                     basic.get('cycle', 0),
                     basic.get('current_phase', 'N/A'),
                     basic.get('current_stage', 'N/A'))

        # 项目元信息
        meta = self.load_project_meta()
        logger.info("📁 项目: %s", meta.project_name or meta.name)
        logger.info("   包名: %s", meta.package_name or '未设置')

        # 输入状态
        input_state = self._load_input_state()
        if input_state.get("last_scan"):
            logger.info("📥 输入文件: %s 个", len(input_state.get('file_hashes', {})))
            logger.info("   上次扫描: %s", input_state['last_scan'])

        # 阶段状态
        stages = self.load_stage_status()
        logger.info("📅 阶段状态:")
        emoji = {"completed": "✅", "in_progress": "🔄", "failed": "❌", "pending": "⏳"}
        for name in self.ALL_STAGES:
            s = stages.get(name)
            if s:
                logger.info("   %s %s: %s", emoji.get(s.status, '❓'), name, s.status)
            else:
                logger.info("   ⏳ %s: pending", name)

        # 子任务状态
        if stage:
            logger.info("📋 子任务状态 (%s):", stage)
            subtasks = self.load_subtask_status(stage)
            for name, sub in subtasks.items():
                duration = f" ({sub.duration_ms // 1000}s)" if sub.duration_ms else ""
                logger.info("   %s %s%s", emoji.get(sub.status, '❓'), name, duration)

        logger.info("\n%s", "=" * 60)

    # ========== 项目元信息 ==========

    def load_project_meta(self) -> ProjectMeta:
        """加载项目元信息"""
        if self._project_meta_file.exists():
            try:
                data = json.loads(self._project_meta_file.read_text(encoding="utf-8"))
                valid_fields = {"name", "project_name", "package_name", "package_path",
                              "backend_language", "frontend_framework", "created_at", "updated_at"}
                filtered = {k: v for k, v in data.items() if k in valid_fields}
                return ProjectMeta(**filtered)
            except (json.JSONDecodeError, OSError, TypeError):
                pass
        return ProjectMeta(name=self.project_dir.name)

    def save_project_meta(self, meta: ProjectMeta):
        """保存项目元信息"""
        with self._lock:
            meta.updated_at = datetime.now().isoformat()
            if not meta.created_at:
                meta.created_at = meta.updated_at
            self._project_meta_file.write_text(
                json.dumps(asdict(meta), indent=2, ensure_ascii=False),
                encoding="utf-8"
            )

    def update_project_meta(self, **kwargs) -> ProjectMeta:
        """更新项目元信息"""
        meta = self.load_project_meta()
        for key, value in kwargs.items():
            if hasattr(meta, key):
                setattr(meta, key, value)
        self.save_project_meta(meta)
        return meta

    # ========== 输入变化检测 ==========

    INPUT_TO_STAGE = {
        "feedback": "requirement",
        "meetings": "requirement",
        "emails": "requirement",
        "tickets": "optimizer"
    }

    def _load_input_state(self) -> Dict:
        """加载输入文件状态"""
        if self._input_state_file.exists():
            try:
                return json.loads(self._input_state_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        return {"file_hashes": {}, "last_scan": None}

    def _save_input_state(self, state: Dict):
        """保存输入文件状态"""
        with self._lock:
            state["last_scan"] = datetime.now().isoformat()
            self._input_state_file.write_text(
                json.dumps(state, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )

    def _file_hash(self, path: Path) -> str:
        """计算文件 MD5 哈希"""
        if not path.exists():
            return ""
        try:
            return hashlib.md5(path.read_bytes()).hexdigest()
        except OSError:
            return ""

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
                        rel = str(f.relative_to(self.input_dir))
                        hashes[rel] = self._file_hash(f)
        return hashes

    def check_input_changes(self) -> Dict[str, Any]:
        """检测输入文件变化"""
        old_state = self._load_input_state()
        old_hashes = old_state.get("file_hashes", {})
        current_hashes = self.scan_input_files()
        changes = []
        for path, new_hash in current_hashes.items():
            if path not in old_hashes:
                changes.append({"path": path, "change_type": "new", "new_hash": new_hash})
            elif old_hashes[path] != new_hash:
                changes.append({"path": path, "change_type": "modified",
                               "old_hash": old_hashes[path], "new_hash": new_hash})
        for path, old_hash in old_hashes.items():
            if path not in current_hashes:
                changes.append({"path": path, "change_type": "deleted", "old_hash": old_hash})
        affected: Set[str] = set()
        for change in changes:
            subdir = change["path"].split("/")[0]
            stage = self.INPUT_TO_STAGE.get(subdir)
            if stage:
                affected.add(stage)
        for s in self.ALL_STAGES:
            deps = self.STAGE_DEPS.get(s, [])
            if any(d in affected for d in deps):
                affected.add(s)
        self._save_input_state({"file_hashes": current_hashes})
        return {
            "has_changes": bool(changes),
            "changes": changes,
            "affected_stages": [s for s in self.ALL_STAGES if s in affected],
            "stats": {
                "total_files": len(current_hashes),
                "new": sum(1 for c in changes if c["change_type"] == "new"),
                "modified": sum(1 for c in changes if c["change_type"] == "modified"),
                "deleted": sum(1 for c in changes if c["change_type"] == "deleted")
            }
        }

    # ========== 统一上下文（来自 StateManager）==========

    def get(self) -> dict:
        """获取完整统一状态（兼容 StateManager.get() 接口）"""
        return self._load_unified_state()

    def update_state(self, path: str, value: Any, by: str = "system") -> bool:
        """
        更新状态（兼容 StateManager.update() 接口）

        Args:
            path: 状态路径，如 "workflow.current_stage"
            value: 新值
            by: 更新者
        """
        return self.batch_update({path: value}, by=by)

    def update(self, path: str, value: Any, by: str = "system") -> bool:
        """[已废弃] 使用 update_state() 替代"""
        warnings.warn("update() 已废弃，请使用 update_state()", DeprecationWarning, stacklevel=2)
        return self.update_state(path, value, by)

    def get_section(self, path: str, default=None) -> Any:
        """获取统一状态中的某个字段（兼容 StateManager 接口）"""
        state = self._load_unified_state()
        keys = path.split(".")
        result = state
        for key in keys:
            if isinstance(result, dict) and key in result:
                result = result[key]
            else:
                return default
        return result

    def batch_update(self, updates: Dict[str, Any], by: str = "system"):
        """
        批量更新统一状态

        Args:
            updates: {path: value} 格式的更新字典
            by: 更新者
        """
        state = self._load_unified_state()
        self._save_history(state)
        for path, value in updates.items():
            keys = path.split(".")
            target = state
            for key in keys[:-1]:
                if key not in target:
                    target[key] = {}
                target = target[key]
            target[keys[-1]] = value
        state["meta"]["updated_at"] = datetime.now().isoformat()
        state["meta"]["updated_by"] = by
        self._save_unified_state(state)

    def init_agents(self):
        """初始化所有智能体状态"""
        state = self._load_unified_state()
        for agent in self.AGENTS:
            state["agents"][agent] = {
                "status": "idle",
                "last_run": None,
                "last_result": None,
                "output_summary": None,
                "error": None
            }
        self._save_unified_state(state)

    def set_agent_status(self, agent: str, status: str, error: str = None):
        """
        设置智能体状态

        Args:
            agent: 智能体名称
            status: 状态 (idle/running/completed/failed)
            error: 错误信息
        """
        if agent not in self.AGENTS:
            return
        state = self._load_unified_state()
        if agent not in state["agents"]:
            state["agents"][agent] = {
                "status": "idle", "last_run": None,
                "last_result": None, "output_summary": None, "error": None
            }
        state["agents"][agent]["status"] = status
        state["agents"][agent]["last_run"] = datetime.now().isoformat()
        if error:
            state["agents"][agent]["error"] = error
        state["meta"]["updated_at"] = datetime.now().isoformat()
        state["meta"]["updated_by"] = agent
        self._save_unified_state(state)

    def get_agent_status(self, agent: str) -> Optional[dict]:
        """获取智能体状态"""
        state = self._load_unified_state()
        return state["agents"].get(agent)

    # ========== 工作流生命周期 ==========

    def start_workflow(self):
        """启动工作流"""
        self.batch_update({
            "workflow.started_at": datetime.now().isoformat(),
            "workflow.cycle": 1,
            "workflow.current_phase": "plan",
            "workflow.current_stage": "requirement",
            "workflow.paused": False,
            "project.status": "running"
        }, by="workflow")

    def advance_stage(self) -> Optional[str]:
        """
        推进到下一阶段

        Returns:
            下一阶段名称，如果循环结束返回 None
        """
        state = self.load_state()
        current_stage = state.get("current_stage")
        current_phase = state.get("current_phase")

        next_phase, next_stage = self._get_next_stage(current_phase, current_stage)
        if next_stage is None:
            return None

        state["current_phase"] = next_phase
        state["current_stage"] = next_stage
        self.save_state(state)
        return next_stage

    def _get_next_stage(self, current_phase: str, current_stage: str) -> Tuple[Optional[str], Optional[str]]:
        """获取下一阶段"""
        if current_phase is None:
            return "plan", "requirement"

        phase_order = ["plan", "do", "check", "act"]
        phase_idx = phase_order.index(current_phase)
        stages = self.PHASE_MAP[current_phase]
        stage_idx = stages.index(current_stage)

        if stage_idx + 1 < len(stages):
            return current_phase, stages[stage_idx + 1]
        elif phase_idx + 1 < len(phase_order):
            next_phase = phase_order[phase_idx + 1]
            return next_phase, self.PHASE_MAP[next_phase][0]
        else:
            return None, None

    def complete_stage(self, stage: str, result: dict = None):
        """完成一个阶段"""
        state = self._load_unified_state()
        if stage not in state["workflow"]["completed_stages"]:
            state["workflow"]["completed_stages"].append(stage)
        if stage in state["agents"]:
            state["agents"][stage]["status"] = "completed"
            state["agents"][stage]["last_run"] = datetime.now().isoformat()
            if result:
                state["agents"][stage]["last_result"] = result.get("status")
                state["agents"][stage]["output_summary"] = result.get("summary")
        self._save_unified_state(state)

    def complete_workflow(self, success: bool = True):
        """完成工作流"""
        status = "completed" if success else "failed"
        self.batch_update({
            "project.status": status,
            "workflow.current_phase": None,
            "workflow.current_stage": None
        }, by="workflow")

    # ========== 上下文管理 ==========

    def add_constraint(self, key: str, value: Any, by: str = "system"):
        """添加约束条件"""
        state = self._load_unified_state()
        state["context"]["constraints"][key] = {
            "value": value,
            "added_by": by,
            "added_at": datetime.now().isoformat()
        }
        self._save_unified_state(state)

    def get_context_for_stage(self, stage: str) -> dict:
        """获取特定阶段的上下文"""
        state = self._load_unified_state()
        decision_types = self._get_relevant_decision_types(stage)
        context = {
            "project": state["project"],
            "decisions": [d for d in state["context"]["decisions"] if d["type"] in decision_types],
            "constraints": state["context"]["constraints"],
            "completed_stages": state["workflow"]["completed_stages"],
            "quality_scores": state["quality"]["stage_scores"]
        }
        return context

    def _get_relevant_decision_types(self, stage: str) -> list:
        """获取与阶段相关的决策类型"""
        type_map = {
            "requirement": ["需求决策", "优先级决策"],
            "design": ["技术选型", "架构决策", "接口设计"],
            "development": ["技术选型", "实现决策", "代码规范"],
            "testing": ["测试策略", "覆盖决策"],
            "deployment": ["部署决策", "环境配置"],
            "operations": ["运维决策", "监控策略"],
            "monitor": ["监控策略", "告警规则"],
            "optimizer": ["优化决策", "性能策略"]
        }
        return type_map.get(stage, [])

    # ========== 事件日志 ==========

    def get_events(self, agent: str = None, action: str = None, limit: int = 50) -> list:
        """
        获取事件日志

        Args:
            agent: 按智能体过滤
            action: 按动作类型过滤
            limit: 限制数量
        """
        state = self._load_unified_state()
        events = state["events"]
        if agent:
            events = [e for e in events if e["agent"] == agent]
        if action:
            events = [e for e in events if e["action"] == action]
        return events[-limit:]

    # ========== 反馈系统 ==========

    def send_feedback(self, from_agent: str, to_agent: str,
                      feedback_type: str, content: dict):
        """发送反馈"""
        state = self._load_unified_state()
        feedback = {
            "id": f"FB-{len(state['feedback']['pending']) + 1:03d}",
            "from": from_agent,
            "to": to_agent,
            "type": feedback_type,
            "content": content,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        state["feedback"]["pending"].append(feedback)
        self._save_unified_state(state)
        self.log_event(
            agent=from_agent,
            action="feedback",
            result=f"发送反馈给 {to_agent}",
            details=feedback
        )

    def get_pending_feedback(self, agent: str = None) -> list:
        """获取待处理的反馈"""
        state = self._load_unified_state()
        pending = state["feedback"]["pending"]
        if agent:
            pending = [f for f in pending if f["to"] == agent]
        return pending

    def resolve_feedback(self, feedback_id: str, resolution: str, by: str = "system"):
        """解决反馈"""
        state = self._load_unified_state()
        for i, feedback in enumerate(state["feedback"]["pending"]):
            if feedback["id"] == feedback_id:
                feedback["status"] = "resolved"
                feedback["resolved_at"] = datetime.now().isoformat()
                feedback["resolved_by"] = by
                feedback["resolution"] = resolution
                state["feedback"]["resolved"].append(feedback)
                state["feedback"]["pending"].pop(i)
                self._save_unified_state(state)
                return True
        return False

    # ========== 质量追踪 ==========

    def record_quality_score(self, stage: str, score: float, issues: list = None):
        """记录质量分数"""
        state = self._load_unified_state()
        state["quality"]["stage_scores"][stage] = score
        if issues:
            state["quality"]["issues"].extend(issues)
        scores = list(state["quality"]["stage_scores"].values())
        state["quality"]["avg_score"] = sum(scores) / len(scores)
        self._save_unified_state(state)

    # ========== 状态重置工具 ==========

    def _save_history(self, state: dict):
        """保存历史版本"""
        self._history_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        history_file = self._history_dir / f"state_{timestamp}.json"
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        history_files = sorted(self._history_dir.glob("state_*.json"))
        if len(history_files) > 50:
            for old_file in history_files[:-50]:
                old_file.unlink()

    def get_summary(self) -> dict:
        """获取状态摘要"""
        basic = self.load_state()
        state = self._load_unified_state()
        return {
            "project": {
                "name": state["project"]["name"],
                "status": state["project"]["status"]
            },
            "workflow": {
                "cycle": basic.get("cycle", 0),
                "current_phase": basic.get("current_phase"),
                "current_stage": basic.get("current_stage"),
                "paused": basic.get("paused", False),
                "completed_count": len(state["workflow"]["completed_stages"])
            },
            "agents_summary": {
                agent: info["status"]
                for agent, info in state["agents"].items()
            },
            "quality": {
                "avg_score": state["quality"]["avg_score"],
                "issues_count": len(state["quality"]["issues"])
            },
            "feedback": {
                "pending": len(state["feedback"]["pending"]),
                "resolved": len(state["feedback"]["resolved"])
            }
        }

    def reset(self, keep_project: bool = True):
        """
        重置统一状态

        Args:
            keep_project: 是否保留项目信息
        """
        new_state = self._default_unified_state()
        if keep_project:
            old_state = self._load_unified_state()
            new_state["project"] = old_state.get("project", new_state["project"])
        self._save_unified_state(new_state)
        self.save_state(self._default_state())

    # ========== 版本化管理（来自 DistributedStateManager）==========

    def get_versioned_incremental_plan(self, stages_to_run: List[str] = None) -> Dict[str, Any]:
        """获取版本化增量执行计划"""
        all_versions = self.csv_parser.get_all_versions()
        if not all_versions:
            return {
                "mode": "none", "reason": "无版本数据",
                "stages_to_run": [], "pending_versions": [],
                "new_requirements": [], "stats": {}
            }
        processed = self.manifest_manager.get_processed_versions()
        pending_versions = [v for v in all_versions if v not in processed]
        if not pending_versions:
            return {
                "mode": "none", "reason": "所有版本已处理",
                "stages_to_run": [], "pending_versions": [],
                "new_requirements": [], "stats": {}
            }
        new_requirements = []
        for version in pending_versions:
            reqs = self.csv_parser.parse_requirements(version)
            new_requirements.extend(reqs)
        by_priority = {}
        for req in new_requirements:
            p = req.priority or "Unknown"
            by_priority[p] = by_priority.get(p, 0) + 1
        stats = {"new_requirements": len(new_requirements), "by_priority": by_priority}
        mode = "full" if not processed else "incremental"
        reason = "首次运行" if not processed else f"检测到 {len(pending_versions)} 个新版本"
        affected_stages = stages_to_run if stages_to_run else self.ALL_STAGES
        return {
            "mode": mode, "reason": reason,
            "stages_to_run": affected_stages,
            "pending_versions": pending_versions,
            "new_requirements": new_requirements, "stats": stats
        }

    def record_version_processed(self, version: str, requirements_added: int = 0):
        """记录版本已处理"""
        self.manifest_manager.record_version_processed(
            version=version,
            input_files=[f.name for f in self.input_dir.glob("feedback/*.csv")] if self.input_dir.exists() else [],
            requirements_added=requirements_added
        )

    def reset_version_state(self):
        """重置版本状态"""
        self.manifest_manager.reset()

    def print_version_status(self):
        """打印版本状态"""
        all_versions = self.csv_parser.get_all_versions()
        processed = self.manifest_manager.get_processed_versions()
        pending = [v for v in all_versions if v not in processed]
        logger.info("\n📋 所有版本: %s", all_versions)
        logger.info("✅ 已处理: %s", processed)
        logger.info("⏳ 待处理: %s", pending)
        if pending:
            logger.info("📊 待处理需求统计:")
            for version in pending:
                reqs = self.csv_parser.parse_requirements(version)
                by_priority = {}
                for req in reqs:
                    p = req.priority or "Unknown"
                    by_priority[p] = by_priority.get(p, 0) + 1
                logger.info("   %s: %s 项需求", version, len(reqs))
                if by_priority:
                    logger.info("      优先级: %s", by_priority)
        stats = self.manifest_manager.get_stats()
        if stats.get("total_versions_processed", 0) > 0:
            logger.info("📈 累计统计:")
            logger.info("   已处理版本: %s", stats['total_versions_processed'])
            logger.info("   总需求: %s", stats['total_requirements_added'])
        logger.info("\n%s", "=" * 60)

    def mark_version_processed(self, versions: List[str], requirements_count: Dict[str, int] = None):
        """标记多个版本为已处理"""
        requirements_count = requirements_count or {}
        for version in versions:
            self.manifest_manager.record_version_processed(
                version=version,
                input_files=[],
                requirements_added=requirements_count.get(version, 0)
            )

    def reset_incremental_state(self):
        """重置增量状态"""
        if self._input_state_file.exists():
            self._input_state_file.unlink()
        logger.info("✅ 增量状态已重置")

    def _load_unified_state(self) -> dict:
        """加载统一状态"""
        if self._unified_state_file.exists():
            try:
                return json.loads(self._unified_state_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        return self._default_unified_state()

    def _default_unified_state(self) -> dict:
        return {
            "meta": {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "updated_by": None
            },
            "project": {
                "name": self.project_dir.name,
                "goal": None,
                "description": None,
                "tech_stack": [],
                "constraints": {},
                "status": "created"
            },
            "agents": {
                name: {"status": "idle", "last_run": None,
                       "last_result": None, "output_summary": None, "error": None}
                for name in ["coordinator", "requirement", "design", "development",
                            "testing", "deployment", "operations", "monitor", "optimizer"]
            },
            "context": {"decisions": [], "constraints": {}, "assumptions": []},
            "events": [],
            "feedback": {"pending": [], "resolved": []},
            "quality": {"stage_scores": {}, "avg_score": 0, "issues": []}
        }

    def log_event(self, agent: str, action: str, result: str, details: dict = None):
        """记录事件"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "action": action,
            "result": result,
            "details": details or {}
        }
        # 追加到事件文件
        with open(self._events_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        # 也更新到状态中
        state = self._load_unified_state()
        state["events"].append(event)
        if len(state["events"]) > 100:
            state["events"] = state["events"][-100:]
        self._save_unified_state(state)

    def record_decision(self, decision_id: str, decision_type: str,
                        content: str, by: str, rationale: str = None):
        """记录重要决策"""
        state = self._load_unified_state()
        decision = {
            "id": decision_id,
            "type": decision_type,
            "content": content,
            "by": by,
            "at": datetime.now().isoformat(),
            "rationale": rationale
        }
        state["context"]["decisions"].append(decision)
        self._save_unified_state(state)
        self.log_event(agent=by, action="decision",
                      result=f"做出决策: {decision_id}", details=decision)

    def get_decisions(self, decision_type: str = None) -> list:
        """获取决策列表"""
        state = self._load_unified_state()
        decisions = state["context"]["decisions"]
        if decision_type:
            return [d for d in decisions if d.get("type") == decision_type]
        return decisions

    def _save_unified_state(self, state: dict):
        """保存统一状态"""
        self._unified_state_file.parent.mkdir(parents=True, exist_ok=True)
        state["meta"]["updated_at"] = datetime.now().isoformat()
        self._unified_state_file.write_text(
            json.dumps(state, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    # ========== 状态重置工具 ==========

    def reset_for_incremental_update(self, stages: List[str] = None):
        """统一重置增量更新所需的状态"""
        if stages is None:
            stages = ["requirement", "design"]
        logger.info("🔄 重置增量更新状态...")
        # 重置输入状态
        if self._input_state_file.exists():
            self._input_state_file.unlink()
            logger.info("   ✅ 已重置输入状态")
        # 重置阶段子任务状态
        for stage in stages:
            status_file = self._get_subtask_status_file(stage)
            if status_file.exists():
                try:
                    data = json.loads(status_file.read_text(encoding="utf-8"))
                    for sub_name in data.get("subtasks", {}):
                        data["subtasks"][sub_name]["status"] = "pending"
                        data["subtasks"][sub_name]["started_at"] = None
                        data["subtasks"][sub_name]["completed_at"] = None
                        data["subtasks"][sub_name]["duration_ms"] = None
                    status_file.write_text(
                        json.dumps(data, indent=2, ensure_ascii=False),
                        encoding="utf-8"
                    )
                    logger.info("   ✅ 已重置阶段 %s 的子任务状态", stage)
                except (json.JSONDecodeError, OSError):
                    pass
        logger.info("✅ 增量更新状态重置完成")
