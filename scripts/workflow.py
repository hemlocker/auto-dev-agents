#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流执行器
Workflow Executor

统一的开发工作流执行器，整合了：
- run_workflow.py: 指定阶段运行
- pdca_workflow.py: PDCA 循环调度
- auto_executor.py: 自动循环执行

使用方式：
  # 查看状态
  python3 scripts/workflow.py --project my_project --status

  # 单步执行下一阶段
  python3 scripts/workflow.py --project my_project --next

  # 指定阶段运行
  python3 scripts/workflow.py --project my_project --stages requirement,design

  # 运行完整 PDCA 循环
  python3 scripts/workflow.py --project my_project --full-cycle

  # 启动持续自动执行
  python3 scripts/workflow.py --project my_project --start

  # 暂停/恢复
  python3 scripts/workflow.py --project my_project --pause
  python3 scripts/workflow.py --project my_project --resume
"""

import argparse
import json
import re
import time
import subprocess
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field

# 延迟导入 requests，如果不可用则使用 subprocess + curl
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# Gateway HTTP API 配置
GATEWAY_URL = "http://127.0.0.1:18799"
GATEWAY_TOKEN = None  # 从环境变量或配置读取


# ==================== 数据类定义 ====================

@dataclass
class StageConfig:
    """阶段配置"""
    name: str
    phase: str = "custom"
    input_dir: str = None
    output_dir: str = None
    prompt: str = None
    depends_on: List[str] = field(default_factory=list)
    skip: bool = False
    timeout: int = 1800
    
    @classmethod
    def from_dict(cls, data: dict) -> 'StageConfig':
        """从字典创建"""
        return cls(
            name=data.get("name"),
            phase=data.get("phase", "custom"),
            input_dir=data.get("input"),
            output_dir=data.get("output"),
            prompt=data.get("prompt"),
            depends_on=data.get("depends_on", []),
            skip=data.get("skip", False),
            timeout=data.get("timeout", 1800)
        )


# ==================== 自定义异常 ====================

class WorkflowError(Exception):
    """工作流基础异常"""
    pass


class StageExecutionError(WorkflowError):
    """阶段执行异常"""
    def __init__(self, stage: str, message: str):
        self.stage = stage
        self.message = message
        super().__init__(f"[{stage}] {message}")


class StageTimeoutError(WorkflowError):
    """阶段超时异常"""
    def __init__(self, stage: str, timeout: int):
        self.stage = stage
        self.timeout = timeout
        super().__init__(f"[{stage}] 执行超时 ({timeout}s)")


class DependencyError(WorkflowError):
    """依赖检查异常"""
    def __init__(self, stage: str, missing_input: str):
        self.stage = stage
        self.missing_input = missing_input
        super().__init__(f"[{stage}] 缺少前置输入: {missing_input}")


# ==================== HTTP 辅助函数 ====================

def http_post(url: str, headers: dict, payload: dict, timeout: int = 30) -> dict:
    """发送 HTTP POST 请求（优先使用 requests，否则使用 curl）"""
    if HAS_REQUESTS:
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            return {"status_code": response.status_code, "text": response.text, "json": response.json() if response.text else None}
        except Exception as e:
            return {"error": str(e)}
    else:
        # 使用 curl
        import tempfile
        header_args = []
        for k, v in headers.items():
            header_args.extend(["-H", f"{k}: {v}"])
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(payload, f)
            payload_file = f.name
        
        try:
            result = subprocess.run(
                ["curl", "-s", "-X", "POST", url] + header_args + ["-d", f"@{payload_file}", "--connect-timeout", str(timeout)],
                capture_output=True, text=True, timeout=timeout + 5
            )
            response_text = result.stdout
            try:
                return {"status_code": 200, "text": response_text, "json": json.loads(response_text) if response_text else None}
            except:
                return {"status_code": 500, "text": response_text}
        except Exception as e:
            return {"error": str(e)}
        finally:
            os.unlink(payload_file)


class SubagentExecutor:
    """子智能体执行器 - 通过 OpenClaw Gateway HTTP API 执行"""

    def __init__(self, gateway_url: str = None, gateway_token: str = None):
        self.gateway_url = gateway_url or GATEWAY_URL
        self.gateway_token = gateway_token or GATEWAY_TOKEN

    def spawn(self, task: str, cwd: str, label: str, timeout_seconds: int = 1800) -> dict:
        """通过 Gateway HTTP API 启动子智能体"""
        headers = {"Content-Type": "application/json"}
        if self.gateway_token:
            headers["Authorization"] = f"Bearer {self.gateway_token}"

        payload = {
            "tool": "sessions_spawn",
            "args": {
                "runtime": "subagent",
                "mode": "run",
                "task": task,
                "cwd": cwd,
                "timeoutSeconds": timeout_seconds,
                "label": label
            }
        }

        result = http_post(
            f"{self.gateway_url}/tools/invoke",
            headers,
            payload,
            timeout=30
        )

        if "error" in result:
            return {"ok": False, "error": result["error"]}
        
        status_code = result.get("status_code", 500)
        if status_code == 200:
            return result.get("json", {"ok": True})
        elif status_code == 404:
            return {"ok": False, "error": "sessions_spawn 被 Gateway 禁用，请配置 gateway.tools.allow"}
        else:
            return {"ok": False, "error": f"HTTP {status_code}: {result.get('text', '')}"}

    def check_status(self, session_key: str) -> dict:
        """检查子智能体状态"""
        headers = {"Content-Type": "application/json"}
        if self.gateway_token:
            headers["Authorization"] = f"Bearer {self.gateway_token}"

        payload = {
            "tool": "subagents",
            "args": {"action": "list"}
        }

        result = http_post(
            f"{self.gateway_url}/tools/invoke",
            headers,
            payload,
            timeout=10
        )

        if "error" in result:
            return {"running": False, "error": result["error"]}
        
        if result.get("status_code") == 200:
            data = result.get("json", {})
            if data.get("ok") and data.get("result"):
                for sub in data["result"].get("active", []):
                    if sub.get("sessionKey") == session_key:
                        return {"running": True, "info": sub}
                for sub in data["result"].get("recent", []):
                    if sub.get("sessionKey") == session_key:
                        return {"running": False, "info": sub}
            return {"running": False, "info": None}
        return {"running": False, "error": result.get("text", "Unknown error")}


class WorkflowExecutor:
    """工作流执行器 - 统一的 PDCA 工作流管理"""

    # 默认阶段配置（配置文件不存在时使用）
    DEFAULT_STAGES = [
        StageConfig("requirement", "plan", "input/", "output/requirements/"),
        StageConfig("design", "plan", "output/requirements/", "output/design/", depends_on=["requirement"]),
        StageConfig("development", "do", "output/design/", "output/src/", depends_on=["design"]),
        StageConfig("testing", "do", "output/src/", "output/tests/", depends_on=["development"]),
        StageConfig("deployment", "do", "output/tests/", "output/deploy/", depends_on=["testing"]),
        StageConfig("operations", "check", "output/deploy/", "output/operations/", depends_on=["deployment"]),
        StageConfig("monitor", "check", "output/", "output/monitor/", depends_on=["operations"]),
        StageConfig("optimizer", "act", "output/monitor/", "output/optimizer/", depends_on=["monitor"]),
    ]

    def __init__(self, project_name: str, base_dir: str = None, execute: bool = False,
                 template: str = None, stages_override: List[str] = None):
        self.project_name = project_name
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent
        self.project_dir = self.base_dir / "projects" / project_name
        self.input_dir = self.project_dir / "input"
        self.output_dir = self.project_dir / "output"
        self.state_file = self.project_dir / "workflow_state.json"
        self.log_file = self.project_dir / "logs" / "workflow.jsonl"
        self.config = self._load_config()
        self.running = True
        self.execute = execute  # 是否实际执行子智能体
        self.subagent_executor = SubagentExecutor() if execute else None
        
        # 加载阶段配置
        self.stages = self._load_stages(template, stages_override)
        self.stage_map = {s.name: s for s in self.stages}

    # ==================== 配置与状态管理 ====================

    def _load_config(self) -> dict:
        """加载项目配置"""
        config_path = self.base_dir / "config.yaml"
        default_config = {
            "pdca": {
                "max_cycles": 0,  # 0 = 无限循环
                "cycle_interval_seconds": 300
            },
            "execution": {
                "stage_delay_seconds": 60,
                "timeout_seconds": 1800
            }
        }

        if not config_path.exists():
            return default_config

        try:
            import yaml
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                # 合并默认配置
                for key in default_config:
                    if key not in config:
                        config[key] = default_config[key]
                return config
        except:
            # 简单解析 YAML（避免依赖）
            content = config_path.read_text()
            config = default_config.copy()

            for key in ["max_cycles", "cycle_interval_seconds"]:
                match = re.search(rf"{key}:\s*(\d+)", content)
                if match:
                    config["pdca"][key] = int(match.group(1))

            for key in ["stage_delay_seconds", "timeout_seconds"]:
                match = re.search(rf"{key}:\s*(\d+)", content)
                if match:
                    config["execution"][key] = int(match.group(1))

            return config

    def _load_stages(self, template: str = None, stages_override: List[str] = None) -> List[StageConfig]:
        """加载阶段配置
        
        Args:
            template: 模板名称
            stages_override: 指定执行的阶段列表
            
        Returns:
            List[StageConfig]: 阶段配置列表
        """
        # 优先级: stages_override > template > config.yaml > DEFAULT_STAGES
        
        if stages_override:
            # 使用指定的阶段列表
            return [s for s in self.DEFAULT_STAGES if s.name in stages_override]
        
        # 尝试从配置加载
        workflow_config = self.config.get("workflow", {})
        
        if template:
            # 使用指定模板
            templates = workflow_config.get("templates", {})
            template_stages = templates.get(template, {}).get("stages", [])
            if template_stages:
                return [s for s in self.DEFAULT_STAGES if s.name in template_stages]
        
        # 使用配置文件中的阶段定义
        stages_config = workflow_config.get("stages", [])
        if stages_config:
            return [StageConfig.from_dict(s) for s in stages_config]
        
        # 使用默认配置
        return self.DEFAULT_STAGES

    def _load_project_info(self) -> dict:
        """加载项目信息"""
        project_file = self.project_dir / "project.json"
        if not project_file.exists():
            return {"error": f"项目 '{self.project_name}' 不存在"}

        with open(project_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_prompt(self, stage: str) -> str:
        """加载阶段提示词"""
        prompt_path = self.base_dir / "prompts" / stage / "system.md"
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        return f"你是 {stage} 智能体，请完成你的任务。"

    def _read_state(self) -> dict:
        """读取工作流状态"""
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text(encoding="utf-8"))
            except:
                pass
        return {
            "cycle": 0,
            "current_phase": None,
            "current_stage": None,
            "paused": False,
            "history": []
        }

    def _save_state(self, state: dict):
        """保存工作流状态"""
        state["updated_at"] = datetime.now().isoformat()
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(
            json.dumps(state, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def _log_execution(self, phase: str, stage: str, spawn_config: dict):
        """记录执行日志"""
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "cycle": self._read_state().get("cycle", 0),
            "phase": phase,
            "stage": stage,
            "spawn_config": spawn_config
        }
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    # ==================== 阶段管理 ====================

    def _get_next_stage(self, state: dict) -> Tuple[Optional[str], Optional[str]]:
        """获取下一阶段"""
        current_stage = state.get("current_stage")

        if current_stage is None:
            # 开始第一个阶段
            state["cycle"] = state.get("cycle", 0) + 1
            if self.stages:
                first_stage = self.stages[0]
                return first_stage.phase, first_stage.name
            return None, None

        # 找到当前阶段索引
        stage_names = [s.name for s in self.stages]
        if current_stage not in stage_names:
            return None, None
        
        stage_idx = stage_names.index(current_stage)
        
        # 下一阶段
        if stage_idx + 1 < len(self.stages):
            next_stage = self.stages[stage_idx + 1]
            return next_stage.phase, next_stage.name

        # 循环完成
        state["history"].append({
            "cycle": state["cycle"],
            "completed_at": datetime.now().isoformat()
        })

        max_cycles = self.config["pdca"].get("max_cycles", 0)
        if max_cycles == 0 or state["cycle"] < max_cycles:
            state["cycle"] += 1
            if self.stages:
                first_stage = self.stages[0]
                return first_stage.phase, first_stage.name

        return None, None

    def _generate_spawn_config(self, stage: str, phase: str = None) -> dict:
        """生成 sessions_spawn 配置"""
        stage_config = self.stage_map.get(stage)
        
        # 从阶段配置获取属性
        if stage_config:
            input_path = self.project_dir / stage_config.input_dir if stage_config.input_dir else self.input_dir
            output_path = self.project_dir / stage_config.output_dir if stage_config.output_dir else self.output_dir / stage
            timeout = stage_config.timeout
            phase = phase or stage_config.phase
        else:
            input_path = self.input_dir
            output_path = self.output_dir / stage
            timeout = self.config["execution"].get("timeout_seconds", 1800)
        
        prompt = self._load_prompt(stage)

        task = f"""# 项目: {self.project_name} | PDCA 阶段: {phase.upper()} | 智能体: {stage}

## 系统提示词
{prompt}

## 输入目录
{input_path}

## 输出目录
{output_path}

## 任务
请根据输入完成 {stage} 阶段的工作，结果写入输出目录。
"""

        return {
            "action": "sessions_spawn",
            "params": {
                "runtime": "subagent",
                "mode": "run",
                "task": task,
                "cwd": str(self.base_dir),
                "timeoutSeconds": timeout,
                "label": f"{self.project_name}_{phase}_{stage}"
            },
            "stage": stage,
            "phase": phase,
            "input_dir": str(input_path),
            "output_dir": str(output_path)
        }

    # ==================== 执行模式 ====================

    def _check_dependencies(self, stage: str) -> Tuple[bool, Optional[str]]:
        """检查前置阶段输出是否存在
        
        Returns:
            Tuple[bool, Optional[str]]: (是否通过, 缺失的输入路径)
        """
        stage_config = self.stage_map.get(stage)
        if not stage_config:
            return True, None
        
        input_path = stage_config.input_dir
        if not input_path:
            return True, None
        
        full_path = self.project_dir / input_path
        if not full_path.exists():
            return False, str(full_path)
        
        # 检查目录是否为空（requirement 阶段除外）
        if stage != "requirement" and full_path.is_dir():
            if not any(full_path.iterdir()):
                return False, f"{full_path} (目录为空)"
        
        return True, None

    def execute_stage(self, stage: str, phase: str = None, wait: bool = True, 
                      skip_dependency_check: bool = False) -> dict:
        """执行单个阶段

        Args:
            stage: 阶段名称
            phase: PDCA 阶段
            wait: 是否等待子智能体完成（仅当 execute=True 时有效）
            skip_dependency_check: 是否跳过依赖检查

        Returns:
            dict: 执行结果
            
        Raises:
            DependencyError: 前置阶段输出不存在
            StageExecutionError: 子智能体启动失败
            StageTimeoutError: 子智能体执行超时
        """
        # 获取阶段配置
        stage_config = self.stage_map.get(stage)
        if not stage_config:
            stage_config = StageConfig(stage, phase or "custom")
        
        if phase is None:
            phase = stage_config.phase

        # 依赖检查
        if self.execute and not skip_dependency_check:
            passed, missing = self._check_dependencies(stage)
            if not passed:
                raise DependencyError(stage, missing)

        spawn_config = self._generate_spawn_config(stage, phase)
        start_time = time.time()

        print(f"\n{'='*60}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 执行阶段")
        print(f"  PDCA: {phase.upper()}")
        print(f"  智能体: {stage}")
        print(f"  输入: {spawn_config['input_dir']}")
        print(f"  输出: {spawn_config['output_dir']}")
        print(f"{'='*60}")

        self._log_execution(phase, stage, spawn_config)

        # 实际执行子智能体
        if self.execute and self.subagent_executor:
            print(f"\n🚀 启动子智能体: {spawn_config['params']['label']}")

            result = self.subagent_executor.spawn(
                task=spawn_config["params"]["task"],
                cwd=spawn_config["params"]["cwd"],
                label=spawn_config["params"]["label"],
                timeout_seconds=spawn_config["params"]["timeoutSeconds"]
            )

            if not result.get("ok"):
                error_msg = result.get("error", "未知错误")
                print(f"❌ 启动失败: {error_msg}")
                spawn_config["spawn_result"] = result
                spawn_config["duration"] = time.time() - start_time
                spawn_config["success"] = False
                raise StageExecutionError(stage, error_msg)

            spawn_config["spawn_result"] = result

            if wait:
                # 等待子智能体完成
                session_key = result.get("result", {}).get("childSessionKey")
                if session_key:
                    print(f"⏳ 等待子智能体完成: {session_key}")
                    completed = self._wait_for_completion(session_key)
                    if not completed:
                        spawn_config["duration"] = time.time() - start_time
                        spawn_config["success"] = False
                        raise StageTimeoutError(stage, 3600)

        spawn_config["duration"] = time.time() - start_time
        spawn_config["success"] = True
        return spawn_config

    def _wait_for_completion(self, session_key: str, poll_interval: int = 10, max_wait: int = 3600):
        """等待子智能体完成

        Args:
            session_key: 子智能体会话 key
            poll_interval: 轮询间隔（秒），默认 10 秒
            max_wait: 最大等待时间（秒），默认 1 小时
        """
        waited = 0
        while waited < max_wait:
            status = self.subagent_executor.check_status(session_key)
            if not status.get("running"):
                info = status.get("info", {})
                duration = info.get("durationMs", 0) / 1000 if info else 0
                print(f"✅ 子智能体完成 (耗时 {duration:.0f}s)")
                return True
            print(f"  ⏳ 执行中... ({waited}s)")
            time.sleep(poll_interval)
            waited += poll_interval
        print(f"⏰ 等待超时: {session_key}")
        return False

    def execute_next(self) -> Optional[dict]:
        """执行下一阶段（PDCA 模式）"""
        state = self._read_state()

        if state.get("paused"):
            print("⏸️ 工作流已暂停")
            return None

        phase, stage = self._get_next_stage(state)

        if phase is None:
            print("✅ PDCA 循环已完成，已达最大循环次数")
            return None

        state["current_phase"] = phase
        state["current_stage"] = stage
        self._save_state(state)

        return self.execute_stage(stage, phase)

    def execute_stages(self, stages: List[str]) -> List[dict]:
        """执行指定阶段列表"""
        results = []
        stage_names = [s.name for s in self.stages]
        
        print(f"\n🚀 执行指定阶段: {', '.join(stages)}")

        for stage in stages:
            if stage not in stage_names:
                print(f"⚠️ 未知阶段: {stage}，跳过")
                continue

            result = self.execute_stage(stage)
            results.append(result)

        return results

    def execute_full_cycle(self) -> dict:
        """执行完整工作流
        
        Returns:
            dict: 执行结果统计，包含:
                - total: 总阶段数
                - success: 成功数
                - failed: 失败数
                - duration: 总耗时（秒）
                - stages: 各阶段结果
                - error: 失败阶段错误信息（如有）
        """
        # 重置状态
        self._save_state({
            "cycle": 1,
            "current_phase": None,
            "current_stage": None,
            "paused": False,
            "history": []
        })

        stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "duration": 0,
            "stages": [],
            "error": None
        }
        start_time = time.time()
        
        # 显示执行计划
        print(f"\n🔄 执行工作流 ({len(self.stages)} 个阶段)")
        phase_groups = {}
        for s in self.stages:
            if s.phase not in phase_groups:
                phase_groups[s.phase] = []
            phase_groups[s.phase].append(s.name)
        for phase, stages in phase_groups.items():
            print(f"   {phase.upper()}: {', '.join(stages)}")

        try:
            for stage_config in self.stages:
                stage = stage_config.name
                phase = stage_config.phase
                stats["total"] += 1
                
                # 跳过标记的阶段
                if stage_config.skip:
                    print(f"⏭️ 跳过阶段: {stage}")
                    stats["skipped"] += 1
                    continue
                    
                try:
                    result = self.execute_stage(stage, phase)
                    result["phase"] = phase
                    stats["stages"].append(result)
                    stats["success"] += 1
                    
                    # 更新状态
                    state = self._read_state()
                    state["current_phase"] = phase
                    state["current_stage"] = stage
                    self._save_state(state)
                    
                except DependencyError as e:
                    print(f"⚠️ 依赖检查失败: {e}")
                    stats["stages"].append({
                        "stage": stage,
                        "phase": phase,
                        "success": False,
                        "error": str(e),
                        "error_type": "dependency"
                    })
                    stats["failed"] += 1
                    stats["error"] = str(e)
                    raise
                    
                except StageExecutionError as e:
                    print(f"❌ 阶段执行失败: {e}")
                    stats["stages"].append({
                        "stage": stage,
                        "phase": phase,
                        "success": False,
                        "error": str(e),
                        "error_type": "execution"
                    })
                    stats["failed"] += 1
                    stats["error"] = str(e)
                    raise
                    
                except StageTimeoutError as e:
                    print(f"⏰ 阶段执行超时: {e}")
                    stats["stages"].append({
                        "stage": stage,
                        "phase": phase,
                        "success": False,
                        "error": str(e),
                        "error_type": "timeout"
                    })
                    stats["failed"] += 1
                    stats["error"] = str(e)
                    raise

        except WorkflowError:
            # 工作流错误已记录，继续返回统计
            pass

        # 标记完成
        stats["duration"] = time.time() - start_time
        
        state = self._read_state()
        if stats["failed"] == 0:
            state["history"].append({
                "cycle": state["cycle"],
                "completed_at": datetime.now().isoformat(),
                "duration": stats["duration"]
            })
            self._save_state(state)
            print(f"\n✅ PDCA 循环完成")
        else:
            state["history"].append({
                "cycle": state["cycle"],
                "failed_at": datetime.now().isoformat(),
                "error": stats["error"]
            })
            self._save_state(state)
            print(f"\n❌ PDCA 循环中断: {stats['error']}")

        print(f"   总计: {stats['total']} 阶段")
        print(f"   成功: {stats['success']}")
        print(f"   失败: {stats['failed']}")
        print(f"   耗时: {stats['duration']:.1f}s")
        
        return stats

    def run_continuous(self):
        """持续运行（自动循环执行）"""
        print(f"\n{'='*60}")
        print(f"🚀 工作流自动执行器启动")
        print(f"📁 项目: {self.project_name}")
        print(f"📂 目录: {self.project_dir}")
        print(f"{'='*60}\n")

        project_info = self._load_project_info()
        if "error" in project_info:
            print(f"❌ {project_info['error']}")
            return

        print(f"🎯 目标: {project_info.get('goal', '未指定')}")

        stage_delay = self.config["execution"].get("stage_delay_seconds", 60)

        while self.running:
            try:
                state = self._read_state()

                if state.get("paused"):
                    print("⏸️ 已暂停，等待恢复...")
                    time.sleep(10)
                    continue

                result = self.execute_next()

                if result is None:
                    print("\n👋 工作流执行完成")
                    break

                print(f"\n⏳ 等待 {stage_delay} 秒后继续...")
                time.sleep(stage_delay)

            except KeyboardInterrupt:
                print("\n⏸️ 收到中断信号，停止执行")
                self.running = False
                break
            except Exception as e:
                print(f"❌ 错误: {e}")
                time.sleep(60)

        print("\n👋 执行器已停止")

    # ==================== 控制命令 ====================

    def pause(self):
        """暂停工作流"""
        state = self._read_state()
        state["paused"] = True
        self._save_state(state)
        print("⏸️ 工作流已暂停")

    def resume(self):
        """恢复工作流"""
        state = self._read_state()
        state["paused"] = False
        self._save_state(state)
        print("▶️ 工作流已恢复")

    def reset(self):
        """重置工作流状态"""
        self._save_state({
            "cycle": 0,
            "current_phase": None,
            "current_stage": None,
            "paused": False,
            "history": []
        })
        print("🔄 工作流状态已重置")

    def status(self) -> dict:
        """获取工作流状态"""
        state = self._read_state()
        project_info = self._load_project_info()

        return {
            "project": self.project_name,
            "project_dir": str(self.project_dir),
            "goal": project_info.get("goal") if "error" not in project_info else None,
            "cycle": state.get("cycle", 0),
            "current_phase": state.get("current_phase"),
            "current_stage": state.get("current_stage"),
            "paused": state.get("paused", False),
            "history_count": len(state.get("history", [])),
            "config": {
                "max_cycles": self.config["pdca"].get("max_cycles", 0),
                "stage_delay": self.config["execution"].get("stage_delay_seconds", 60)
            }
        }


def main():
    parser = argparse.ArgumentParser(
        description="工作流执行器 - 统一的 PDCA 工作流管理",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查看状态
  python3 scripts/workflow.py -p my_project --status

  # 单步执行（仅生成配置）
  python3 scripts/workflow.py -p my_project --next

  # 单步执行（实际运行子智能体）
  python3 scripts/workflow.py -p my_project --next --execute

  # 指定阶段执行
  python3 scripts/workflow.py -p my_project --stages requirement,design --execute

  # 使用模板执行
  python3 scripts/workflow.py -p my_project --template dev-only --execute

  # 从指定阶段开始执行
  python3 scripts/workflow.py -p my_project --from development --execute

  # 执行到指定阶段
  python3 scripts/workflow.py -p my_project --until testing --execute

  # 完整循环（实际执行）
  python3 scripts/workflow.py -p my_project --full-cycle --execute

  # 持续执行
  python3 scripts/workflow.py -p my_project --start --execute

  # 暂停/恢复
  python3 scripts/workflow.py -p my_project --pause
  python3 scripts/workflow.py -p my_project --resume
        """
    )

    parser.add_argument("--project", "-p", required=True, help="项目名称")
    parser.add_argument("--status", "-s", action="store_true", help="查看状态")
    parser.add_argument("--next", "-n", action="store_true", help="执行下一阶段")
    parser.add_argument("--stages", help="执行指定阶段（逗号分隔）")
    parser.add_argument("--template", "-t", help="使用预设模板 (full-pdca/dev-only/test-only/plan-do)")
    parser.add_argument("--from", dest="from_stage", help="从指定阶段开始执行")
    parser.add_argument("--until", dest="until_stage", help="执行到指定阶段为止")
    parser.add_argument("--full-cycle", "-f", action="store_true", help="执行完整工作流")
    parser.add_argument("--start", action="store_true", help="启动持续自动执行")
    parser.add_argument("--pause", action="store_true", help="暂停工作流")
    parser.add_argument("--resume", action="store_true", help="恢复工作流")
    parser.add_argument("--reset", action="store_true", help="重置状态")
    parser.add_argument("--execute", "-e", action="store_true",
                        help="实际执行子智能体（通过 Gateway HTTP API）")
    parser.add_argument("--gateway-url", default="http://127.0.0.1:18799",
                        help="Gateway URL (默认: http://127.0.0.1:18799)")

    args = parser.parse_args()

    # 处理阶段范围
    stages_override = None
    if args.stages:
        stages_override = [s.strip() for s in args.stages.split(",")]
    elif args.from_stage or args.until_stage:
        # 获取默认阶段列表
        default_stages = [s.name for s in WorkflowExecutor.DEFAULT_STAGES]
        from_idx = 0
        until_idx = len(default_stages)
        
        if args.from_stage and args.from_stage in default_stages:
            from_idx = default_stages.index(args.from_stage)
        if args.until_stage and args.until_stage in default_stages:
            until_idx = default_stages.index(args.until_stage) + 1
        
        stages_override = default_stages[from_idx:until_idx]

    executor = WorkflowExecutor(
        project_name=args.project,
        execute=args.execute,
        template=args.template,
        stages_override=stages_override
    )
    if args.execute and executor.subagent_executor:
        executor.subagent_executor.gateway_url = args.gateway_url

    if args.status:
        result = executor.status()
        result["stages"] = [s.name for s in executor.stages]
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.pause:
        executor.pause()

    elif args.resume:
        executor.resume()

    elif args.reset:
        executor.reset()

    elif args.stages or args.from_stage or args.until_stage:
        stages = stages_override
        results = executor.execute_stages(stages)
        if not args.execute:
            print(f"\n📋 执行结果（仅配置，使用 --execute 实际执行）:")
            for r in results:
                print(f"  - [{r['phase'].upper()}] {r['stage']}")

    elif args.full_cycle:
        stats = executor.execute_full_cycle()
        if not args.execute:
            print(f"\n📋 生成的任务配置（使用 --execute 实际执行）:")
            print(json.dumps([s.get("params") for s in stats.get("stages", []) if s.get("params")], 
                           indent=2, ensure_ascii=False))

    elif args.next:
        result = executor.execute_next()
        if result and not args.execute:
            print(f"\n📋 sessions_spawn 配置（使用 --execute 实际执行）:")
            print(json.dumps(result["params"], indent=2, ensure_ascii=False))

    elif args.start:
        executor.run_continuous()

    else:
        # 默认显示状态
        result = executor.status()
        result["stages"] = [s.name for s in executor.stages]
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    exit(main())