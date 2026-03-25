#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流执行器
Workflow Executor

统一的开发工作流执行器，提供：
- 阶段执行（单次/批量/子任务）
- 状态管理
- 日志记录

使用方式：
  # 查看状态
  python3 scripts/workflow.py --project my_project --status

  # 单步执行下一阶段
  python3 scripts/workflow.py --project my_project --next

  # 指定阶段运行
  python3 scripts/workflow.py --project my_project --stages requirement,design

  # 运行完整 PDCA 循环
  python3 scripts/workflow.py --project my_project --full-cycle --execute

  # 使用模板
  python3 scripts/workflow.py --project my_project --template dev-only --execute
"""

import argparse
import json
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple

# 导入拆分的模块
from workflow.models import StageConfig, STAGE_SUBTASKS, WorkflowError, StageExecutionError, StageTimeoutError, DependencyError
from workflow.executors import InputAnalyzer, SubtaskExecutor, SubagentExecutor, http_post
from workflow.state_facade import WorkflowFacade


# ==================== WorkflowExecutor ====================

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
                 template: str = None, stages_override: List[str] = None,
                 project_type: str = None, subtask_strategy: str = None):
        self.project_name = project_name
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent
        self.project_dir = self.base_dir / "projects" / project_name
        self.running = True
        self.execute = execute
        self.subagent_executor = SubagentExecutor() if execute else None

        # 统一状态门面（共享配置，config.yaml 为唯一真相源）
        self.facade = WorkflowFacade(self.project_dir, base_dir=self.base_dir)
        self.config = self.facade.config  # 统一配置入口

        # 输入输出目录（从 facade 配置读取）
        self.input_dir = self.facade.input_dir
        self.output_dir = self.facade.output_dir

        # 项目类型（从参数或配置读取）
        self.project_type = project_type or self.config.get("projects", {}).get("type", "fullstack")

        # 子任务拆分策略（从参数或配置读取）
        self.subtask_strategy = subtask_strategy or self.config.get("workflow", {}).get("subtask_strategy", "layer")
        
        # 模块信息（从需求阶段读取）
        self.modules = []
        
        # 项目元信息（从需求阶段读取，包含包名等）
        self.project_meta = {}
        
        # 加载阶段配置
        self.stages = self._load_stages(template, stages_override)
        self.stage_map = {s.name: s for s in self.stages}

    def _load_stages(self, template: str = None, stages_override: List[str] = None) -> List[StageConfig]:
        """加载阶段配置"""
        if stages_override:
            return [s for s in self.DEFAULT_STAGES if s.name in stages_override]
        
        workflow_config = self.config.get("workflow", {})
        
        if template:
            templates = workflow_config.get("templates", {})
            template_stages = templates.get(template, {}).get("stages", [])
            if template_stages:
                return [s for s in self.DEFAULT_STAGES if s.name in template_stages]
        
        stages_config = workflow_config.get("stages", [])
        if stages_config:
            return [StageConfig.from_dict(s) for s in stages_config]
        
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

    def _load_modules(self) -> List[dict]:
        """从需求阶段输出加载模块信息
        
        Returns:
            List[dict]: 模块列表 [{"name": "user", "dependencies": [], ...}]
        """
        # 尝试从需求输出读取（使用配置的输出路径）
        req_dir = self.facade.get_output_dir("requirement")
        modules_file = req_dir / "modules.json"
        if modules_file.exists():
            try:
                data = json.loads(modules_file.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    return data
                if isinstance(data, dict) and "modules" in data:
                    return data["modules"]
            except (json.JSONDecodeError, OSError):
                pass
        
        # 尝试从分析结果读取
        analysis_file = req_dir / "module_analysis.json"
        if analysis_file.exists():
            try:
                data = json.loads(analysis_file.read_text(encoding="utf-8"))
                if "modules" in data:
                    return data["modules"]
            except (json.JSONDecodeError, OSError):
                pass
        
        return []
    
    def _load_project_meta(self) -> dict:
        """从需求阶段输出加载项目元信息
        
        包含：项目名称、包名、技术栈等
        
        Returns:
            dict: {
                "project_name": "device-management",
                "package_name": "com.example.device",
                "package_path": "com/example/device/",
                "backend_language": "java",
                "frontend_framework": "vue",
                ...
            }
        """
        # 优先从统一状态门面读取
        meta = self.facade.load_project_meta()
        if meta.package_name:
            return {
                "project_name": meta.project_name or meta.name,
                "package_name": meta.package_name,
                "package_path": meta.package_path,
                "backend_language": meta.backend_language,
                "frontend_framework": meta.frontend_framework
            }
        
        # 尝试从 project.json 读取
        project_file = self.project_dir / "project.json"
        if project_file.exists():
            try:
                return json.loads(project_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        
        # 尝试从需求阶段的软件需求文档提取（使用配置的输出路径）
        req_dir = self.facade.get_output_dir("requirement")
        sw_req_file = req_dir / "software_requirements.md"
        if sw_req_file.exists():
            content = sw_req_file.read_text(encoding="utf-8")
            meta = self._extract_meta_from_requirements(content)
            if meta:
                # 保存到统一状态门面
                self.facade.update_project_meta(**meta)
                return meta
        
        # 尝试从架构设计文档提取
        arch_file = self.facade.get_output_dir("design") / "architecture_design.md"
        if arch_file.exists():
            content = arch_file.read_text(encoding="utf-8")
            meta = self._extract_meta_from_architecture(content)
            if meta:
                self.facade.update_project_meta(**meta)
                return meta
        
        # 默认值：从项目名称生成
        return self._generate_default_meta()
    
    def _extract_meta_from_requirements(self, content: str) -> Optional[dict]:
        """从需求文档提取项目元信息"""
        import re
        
        meta = {}
        
        # 提取项目名称
        name_match = re.search(r'项目名称[：:]\s*(.+?)(?:\n|$)', content)
        if name_match:
            meta["project_name"] = name_match.group(1).strip()
        
        # 提取包名（如果有）
        package_match = re.search(r'包名[：:]\s*([\w.]+)', content)
        if package_match:
            package_name = package_match.group(1).strip()
            meta["package_name"] = package_name
            meta["package_path"] = package_name.replace(".", "/") + "/"
        
        # 提取技术栈
        if "Spring Boot" in content or "Java" in content:
            meta["backend_language"] = "java"
        if "Vue" in content:
            meta["frontend_framework"] = "vue"
        if "React" in content:
            meta["frontend_framework"] = "react"
        
        return meta if meta else None
    
    def _extract_meta_from_architecture(self, content: str) -> Optional[dict]:
        """从架构设计文档提取项目元信息"""
        import re
        
        meta = {}
        
        # 提取包名（Java 项目常见格式：com.example.xxx）
        package_match = re.search(r'package\s+([\w.]+)', content)
        if package_match:
            package_name = package_match.group(1).strip()
            meta["package_name"] = package_name
            meta["package_path"] = package_name.replace(".", "/") + "/"
        
        # 从目录结构提取
        # 例如：com.example.device/
        dir_match = re.search(r'([\w.]+)/\s*\n', content)
        if dir_match:
            potential_package = dir_match.group(1)
            if "." in potential_package and potential_package.count(".") >= 2:
                meta["package_name"] = potential_package
                meta["package_path"] = potential_package.replace(".", "/") + "/"
        
        return meta if meta else None
    
    def _generate_default_meta(self) -> dict:
        """生成默认的项目元信息"""
        # 从项目名称生成包名
        # 例如：device-management -> com.example.device
        project_name = self.project_name
        
        # 转换项目名称为包名格式
        # 去掉版本号后缀
        name = re.sub(r'-v?\d+.*$', '', project_name)
        # 转换为小写，去掉连字符
        words = name.replace("-", " ").replace("_", " ").split()
        if len(words) >= 1:
            # 如果是单个词，使用 com.example.{word}
            package_name = f"com.example.{words[0]}"
        else:
            package_name = f"com.example.{name.replace('-', '').replace('_', '')}"
        
        return {
            "project_name": project_name,
            "package_name": package_name,
            "package_path": package_name.replace(".", "/") + "/",
            "backend_language": "java",
            "frontend_framework": "vue"
        }

    # ==================== 阶段管理 ====================

    def _get_next_stage(self, state: dict) -> Tuple[Optional[str], Optional[str]]:
        """获取下一阶段"""
        current_stage = state.get("current_stage")
        if current_stage is None:
            state["cycle"] = state.get("cycle", 0) + 1
            if self.stages:
                first_stage = self.stages[0]
                return first_stage.phase, first_stage.name
            return None, None

        stage_names = [s.name for s in self.stages]
        if current_stage not in stage_names:
            return None, None
        
        stage_idx = stage_names.index(current_stage)
        
        if stage_idx + 1 < len(self.stages):
            next_stage = self.stages[stage_idx + 1]
            return next_stage.phase, next_stage.name

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

    def _generate_spawn_config(self, stage: str, phase: str = None, batch_info: dict = None) -> dict:
        """生成 sessions_spawn 配置"""
        stage_config = self.stage_map.get(stage)
        
        if stage_config:
            input_path = self.project_dir / stage_config.input_dir if stage_config.input_dir else self.input_dir
            output_path = self.project_dir / stage_config.output_dir if stage_config.output_dir else self.facade.get_output_dir(stage)
            timeout = stage_config.timeout
            phase = phase or stage_config.phase
        else:
            input_path = self.facade.get_input_dir(stage)
            output_path = self.facade.get_output_dir(stage)
            timeout = self.config["engine"].get("stage_timeout_default", 1800)
        
        prompt = self._load_prompt(stage)
        
        if batch_info and not batch_info.get("is_full"):
            file_list = "\n".join(f"  - {f['relative']} ({f['size']} bytes)" for f in batch_info["files"])
            batch_context = f"""
## ⚠️ 分批处理说明

**这是第 {batch_info['batch']} 批，共 {batch_info['total_batches']} 批**

### 本次处理文件
{file_list}

### 处理要求
1. 只处理上述文件列表中的内容
2. 分析结果追加到输出目录（不要覆盖已有内容）
3. 如果是多批次，请在输出中标注批次信息
4. 最后一批完成后生成汇总报告
"""
        else:
            batch_context = f"\n## 任务\n请根据输入完成 {stage} 阶段的工作，结果写入输出目录。"

        task = f"""# 项目: {self.project_name} | PDCA 阶段: {phase.upper()} | 智能体: {stage}

## 系统提示词
{prompt}

## 输入目录
{input_path}

## 输出目录
{output_path}
{batch_context}
"""

        label = f"{self.project_name}_{phase}_{stage}"
        if batch_info and not batch_info.get("is_full"):
            label += f"_batch{batch_info['batch']}"

        return {
            "action": "sessions_spawn",
            "params": {
                "runtime": "subagent",
                "mode": "run",
                "task": task,
                "cwd": str(self.base_dir),
                "timeoutSeconds": timeout,
                "label": label
            },
            "stage": stage,
            "phase": phase,
            "input_dir": str(input_path),
            "output_dir": str(output_path),
            "batch_info": batch_info
        }

    # ==================== 执行模式 ====================

    def _check_dependencies(self, stage: str) -> Tuple[bool, Optional[str]]:
        """检查前置阶段输出是否存在"""
        stage_config = self.stage_map.get(stage)
        if not stage_config:
            return True, None
        
        input_path = stage_config.input_dir
        if not input_path:
            return True, None
        
        full_path = self.project_dir / input_path
        if not full_path.exists():
            return False, str(full_path)
        
        if stage != "requirement" and full_path.is_dir():
            if not any(full_path.iterdir()):
                return False, f"{full_path} (目录为空)"
        
        return True, None

    def execute_stage(self, stage: str, phase: str = None, wait: bool = True, 
                      skip_dependency_check: bool = False) -> dict:
        """执行单个阶段"""
        stage_config = self.stage_map.get(stage)
        if not stage_config:
            stage_config = StageConfig(stage, phase or "custom")
        
        if phase is None:
            phase = stage_config.phase

        if self.execute and not skip_dependency_check:
            passed, missing = self._check_dependencies(stage)
            if not passed:
                raise DependencyError(stage, missing)
        
        # 检查是否有子任务定义
        # 如果是 development 阶段，先加载模块信息
        if stage == "development" and not self.modules:
            self.modules = self._load_modules()
        
        # 加载项目元信息（用于动态路径替换）
        if not hasattr(self, 'project_meta') or not self.project_meta:
            self.project_meta = self._load_project_meta()
        
        # 获取正确的输出路径
        output_path = self.project_dir / (stage_config.output_dir or f"output/{stage}")
        
        subtask_executor = SubtaskExecutor(
            stage, output_path, self.base_dir,  # 使用正确的输出路径
            project_type=self.project_type,
            subtask_strategy=self.subtask_strategy,
            modules=self.modules,
            project_meta=self.project_meta
        )
        
        if subtask_executor.has_subtasks() and self.execute:
            return self._execute_stage_subtasks(stage, phase, subtask_executor, output_path, wait)
        
        # 分析输入，决定是否分批
        input_path = self.project_dir / (stage_config.input_dir or "input/")
        if self.execute:
            analyzer = InputAnalyzer(input_path, self.config)
            analysis = analyzer.analyze()
            
            if analysis["needs_batch"] and stage in ["requirement", "design", "development"]:
                return self._execute_stage_batch(stage, phase, analysis, analyzer, wait)
        
        return self._execute_stage_single(stage, phase, wait)
    
    def _execute_stage_single(self, stage: str, phase: str, wait: bool = True,
                               batch_info: dict = None) -> dict:
        """执行单个阶段（单批次）"""
        stage_config = self.stage_map.get(stage) or StageConfig(stage, phase or "custom")
        
        spawn_config = self._generate_spawn_config(stage, phase, batch_info or {"is_full": True})
        start_time = time.time()

        batch_label = ""
        if batch_info and not batch_info.get("is_full"):
            batch_label = f" [批次 {batch_info['batch']}/{batch_info['total_batches']}]"

        print(f"\n{'='*60}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 执行阶段{batch_label}")
        print(f"  PDCA: {phase.upper()}")
        print(f"  智能体: {stage}")
        print(f"  输入: {spawn_config['input_dir']}")
        print(f"  输出: {spawn_config['output_dir']}")
        print(f"{'='*60}")

        self.facade.record_execution_log(phase, stage, spawn_config)

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
                result_data = result.get("result", {})
                if "details" in result_data:
                    session_key = result_data["details"].get("childSessionKey")
                else:
                    session_key = result_data.get("childSessionKey")
                    
                if session_key:
                    print(f"⏳ 等待子智能体完成: {session_key}")
                    completed = self._wait_for_completion(session_key)
                    if not completed:
                        spawn_config["duration"] = time.time() - start_time
                        spawn_config["success"] = False
                        raise StageTimeoutError(stage, self.config["engine"].get("stage_timeout_max", 3600))

        spawn_config["duration"] = time.time() - start_time
        spawn_config["success"] = True
        return spawn_config
    
    def _execute_stage_batch(self, stage: str, phase: str, analysis: dict,
                              analyzer: InputAnalyzer, wait: bool = True) -> dict:
        """执行分批处理"""
        batches = analyzer.generate_batch_plan(analysis)
        
        print(f"\n{'='*60}")
        print(f"📦 输入较大，启用分批处理")
        print(f"   文件数: {analysis['file_count']}")
        print(f"   总大小: {analysis['total_size_kb']} KB")
        print(f"   预估Token: {analysis['estimated_tokens']}")
        print(f"   分批原因: {analysis['reason']}")
        print(f"   批次数: {len(batches)}")
        print(f"{'='*60}")
        
        start_time = time.time()
        batch_results = []
        
        for batch in batches:
            try:
                result = self._execute_stage_single(stage, phase, wait, batch)
                batch_results.append(result)
                
                if batch["batch"] < batch["total_batches"]:
                    delay = self.config["execution"].get("stage_delay_seconds", 30)
                    print(f"\n⏳ 等待 {delay}s 后处理下一批...")
                    time.sleep(delay)
                    
            except (DependencyError, StageExecutionError, StageTimeoutError) as e:
                print(f"❌ 批次 {batch['batch']} 失败: {e}")
                batch_results.append({
                    "batch": batch["batch"],
                    "success": False,
                    "error": str(e)
                })
                continue
        
        total_duration = time.time() - start_time
        success_count = sum(1 for r in batch_results if r.get("success"))
        
        return {
            "stage": stage,
            "phase": phase,
            "batch_mode": True,
            "total_batches": len(batches),
            "success_batches": success_count,
            "failed_batches": len(batches) - success_count,
            "duration": total_duration,
            "success": success_count == len(batches),
            "batch_results": batch_results,
            "analysis": {
                "file_count": analysis["file_count"],
                "total_size_kb": analysis["total_size_kb"],
                "estimated_tokens": analysis["estimated_tokens"]
            }
        }
    
    def _wait_for_no_active_subagents(self, max_wait: int = None) -> bool:
        if max_wait is None:
            max_wait = self.config["engine"].get("wait_active_max_seconds", 300)
        """等待所有活跃子智能体完成
        
        Returns:
            bool: True 表示无活跃子智能体，False 表示超时
        """
        if not self.subagent_executor:
            return True
        
        waited = 0
        poll_interval = self.config["engine"].get("http_timeout_short", 10)
        
        while waited < max_wait:
            status = self.subagent_executor.check_status("__list_all__")
            active_count = 0
            
            # check_status 返回的是单个 session 的状态
            # 我们需要通过 subagents list 获取所有活跃的
            headers = {"Content-Type": "application/json"}
            if self.subagent_executor.gateway_token:
                headers["Authorization"] = f"Bearer {self.subagent_executor.gateway_token}"
            
            payload = {"tool": "subagents", "args": {"action": "list"}}
            result = http_post(
                f"{self.subagent_executor.gateway_url}/tools/invoke",
                headers, payload, timeout=self.config["engine"].get("http_timeout_short", 10)
            )
            
            if result.get("status_code") == 200:
                data = result.get("json", {})
                if data.get("ok"):
                    details = data.get("result", {}).get("details", {})
                    if not details:
                        details = data.get("result", {})
                    active = details.get("active", [])
                    active_count = len(active)
                    
                    if active_count == 0:
                        return True
                    
                    if waited % self.config["engine"].get("status_print_interval_seconds", 30) == 0:  # 每 N 秒打印一次
                        print(f"  ⚠️ 等待 {active_count} 个活跃子智能体完成...")
            
            time.sleep(poll_interval)
            waited += poll_interval
        
        print(f"  ⏰ 等待活跃子智能体超时 ({max_wait}s)")
        return False
    
    def _execute_stage_subtasks(self, stage: str, phase: str, 
                                  subtask_executor: SubtaskExecutor,
                                  output_dir: Path, wait: bool = True) -> dict:
        """使用子任务增量执行阶段（支持断点续传）"""
        execution_plan = subtask_executor.get_execution_plan()
        all_subtask_names = [s["name"] for s in execution_plan]
        
        # 🔍 检查已完成的子任务（断点续传）
        pending_subtask_names = self.facade.get_pending_subtasks(stage, all_subtask_names)
        completed_subtask_names = self.facade.get_completed_subtasks(stage)
        
        # 打印进度
        progress = self.facade.get_progress(stage, all_subtask_names)
        
        print(f"\n{'='*60}")
        print(f"📦 阶段 {stage} 使用子任务增量执行")
        print(f"   总子任务数: {len(execution_plan)}")
        print(f"   已完成: {progress['completed']} | 待执行: {len(pending_subtask_names)}")
        print(f"   进度: {progress['progress_percent']}%")
        print(f"   执行模式: 严格串行 + 断点续传")
        print(f"{'='*60}")
        
        # 如果所有子任务都已完成
        if not pending_subtask_names:
            print(f"✅ 阶段 {stage} 所有子任务已完成，跳过执行")
            return {
                "stage": stage,
                "phase": phase,
                "subtask_mode": True,
                "skipped": True,
                "total_subtasks": len(execution_plan),
                "success_subtasks": len(completed_subtask_names),
                "message": "所有子任务已完成"
            }
        
        start_time = time.time()
        subtask_results = []
        current_session_key = None  # 追踪当前子任务的 session
        
        # 标记阶段开始
        self.facade.update_stage_status(stage, status="in_progress",
                                      started_at=datetime.now().isoformat())
        
        for i, subtask in enumerate(execution_plan):
            subtask_name = subtask["name"]
            
            # ⏭️ 跳过已完成的子任务
            if subtask_name in completed_subtask_names:
                print(f"\n{'─'*40}")
                print(f"[{i+1}/{len(execution_plan)}] ⏭️ 跳过已完成的子任务: {subtask_name}")
                continue
            
            print(f"\n{'─'*40}")
            print(f"[{i+1}/{len(execution_plan)}] 子任务: {subtask_name}")
            print(f"   描述: {subtask['description']}")
            
            # 🔒 在执行新子任务前，确保没有活跃的子智能体
            if self.execute and self.subagent_executor:
                print(f"   🔒 检查活跃子智能体...")
                if not self._wait_for_no_active_subagents(
                        max_wait=self.config["engine"].get("wait_active_first_seconds", 60)):
                    print(f"   ⚠️ 存在活跃子智能体，强制等待...")
                    self._wait_for_no_active_subagents(
                        max_wait=self.config["engine"].get("wait_active_max_seconds", 300))
            # 标记子任务开始
            subtask_start = time.time()
            self.facade.start_subtask(stage, subtask_name)
            
            try:
                task_prompt = subtask_executor.generate_subtask_prompt(
                    subtask, {"output_dir": output_dir}
                )
                
                result, session_key = self._execute_subtask_with_session(
                    stage, phase, subtask_name, task_prompt, output_dir, wait
                )
                current_session_key = session_key
                
                subtask_duration = int((time.time() - subtask_start) * 1000)
                
                if result.get("success"):
                    new_files = result.get("output_files", [])
                    print(f"   ✅ 子任务完成，生成 {len(new_files)} 个文件")
                    subtask_executor.record_result(subtask_name, {
                        "success": True,
                        "output_files": new_files,
                        "output_dir": result.get("output_dir"),
                        "summary": subtask["description"]
                    })
                    
                    # ✅ 标记子任务完成（分布式状态）
                    self.facade.complete_subtask(
                        stage, subtask_name,
                        duration_ms=subtask_duration,
                        output_dir=result.get("output_dir"),
                        output_files_count=len(new_files)
                    )
                    
                    # 更新已完成的子任务列表（用于后续跳过）
                    completed_subtask_names.append(subtask_name)
                else:
                    print(f"   ⚠️ 子任务可能不完整: {result.get('error', '未知')}")
                    subtask_executor.record_result(subtask_name, {
                        "success": False,
                        "error": result.get("error"),
                        "summary": subtask["description"]
                    })
                    
                    # 标记子任务失败
                    self.facade.fail_subtask(stage, subtask_name, error=result.get("error"))
                
                subtask_results.append({
                    "subtask": subtask_name,
                    "success": result.get("success", False),
                    "duration": result.get("duration", 0),
                    "session_key": session_key
                })
                
                # 子任务间增加间隔，确保资源释放
                if i < len(execution_plan) - 1:
                    delay = self.config["execution"].get("subtask", {}).get("delay_seconds", 5)
                    print(f"   ⏳ 等待 {delay}s 后执行下一个子任务...")
                    time.sleep(delay)
                    
            except Exception as e:
                print(f"   ❌ 子任务失败: {e}")
                self.facade.fail_subtask(stage, subtask_name, error=str(e))
                subtask_results.append({
                    "subtask": subtask_name,
                    "success": False,
                    "error": str(e)
                })
                continue
        
        total_duration = time.time() - start_time
        success_count = sum(1 for r in subtask_results if r.get("success"))
        
        # 重新获取进度
        final_progress = self.facade.get_progress(stage, all_subtask_names)
        
        print(f"\n{'='*60}")
        print(f"📊 阶段 {stage} 子任务执行完成")
        print(f"   成功: {final_progress['completed']}/{len(execution_plan)}")
        print(f"   失败: {final_progress['failed']}")
        print(f"   耗时: {total_duration:.1f}s")
        print(f"{'='*60}")
        
        # ✅ 阶段完成后更新状态
        if final_progress['completed'] == len(execution_plan):
            self.facade.update_stage_status(
                stage, status="completed",
                completed_at=datetime.now().isoformat(),
                duration_ms=int(total_duration * 1000)
            )
            self.facade.update_stage(phase, stage)
        
        return {
            "stage": stage,
            "phase": phase,
            "subtask_mode": True,
            "total_subtasks": len(execution_plan),
            "success_subtasks": final_progress['completed'],
            "failed_subtasks": final_progress['failed'],
            "duration": total_duration,
            "success": final_progress['completed'] == len(execution_plan),
            "subtask_results": subtask_results,
            "summary": subtask_executor.get_summary()
        }
    
    def _execute_subtask_with_session(self, stage: str, phase: str, subtask_name: str,
                                       task_prompt: str, output_dir: Path, wait: bool = True) -> Tuple[dict, Optional[str]]:
        """执行单个子任务并返回 session_key
        
        Returns:
            Tuple[dict, Optional[str]]: (结果字典, session_key)
        """
        stage_config = self.stage_map.get(stage) or StageConfig(stage, phase or "custom")
        timeout = stage_config.timeout if stage_config.timeout else self.config["engine"].get("stage_timeout_default", 1800)
        
        label = f"{self.project_name}_{phase}_{stage}_{subtask_name}"
        
        existing_files = set()
        if output_dir.exists():
            existing_files = {str(f) for f in output_dir.rglob("*") if f.is_file()}
        
        start_time = time.time()
        session_key = None
        
        if self.execute and self.subagent_executor:
            print(f"   🚀 启动子智能体: {label}")
            
            result = self.subagent_executor.spawn(
                task=task_prompt,
                cwd=str(self.base_dir),
                label=label,
                timeout_seconds=timeout
            )
            
            if not result.get("ok"):
                return {
                    "success": False,
                    "error": result.get("error", "未知错误"),
                    "duration": time.time() - start_time
                }, None
            
            # 提取 session_key
            result_data = result.get("result", {})
            if "details" in result_data:
                session_key = result_data["details"].get("childSessionKey")
            else:
                session_key = result_data.get("childSessionKey")
            
            if wait and session_key:
                print(f"   ⏳ 等待子智能体完成: {session_key[:50]}...")
                completed = self._wait_for_completion(session_key)
                if not completed:
                    return {
                        "success": False,
                        "error": "超时",
                        "duration": time.time() - start_time
                    }, session_key
        
        new_files = []
        if output_dir.exists():
            current_files = {str(f) for f in output_dir.rglob("*") if f.is_file()}
            new_files = [str(f) for f in (current_files - existing_files)]
        
        return {
            "success": True,
            "duration": time.time() - start_time,
            "output_dir": str(output_dir),
            "output_files": new_files,
            "total_files": len(new_files)
        }, session_key
    
    def _execute_subtask(self, stage: str, phase: str, subtask_name: str, 
                          task_prompt: str, output_dir: Path, wait: bool = True) -> dict:
        """执行单个子任务（兼容旧接口）"""
        result, _ = self._execute_subtask_with_session(stage, phase, subtask_name, task_prompt, output_dir, wait)
        return result
    
    def _wait_for_completion(self, session_key: str, poll_interval: int = None, max_wait: int = None):
        if poll_interval is None:
            poll_interval = self.config["engine"].get("http_timeout_short", 10)
        if max_wait is None:
            max_wait = self.config["engine"].get("stage_timeout_max", 3600)
        """等待子智能体完成"""
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
        """执行下一阶段"""
        state = self.facade.load_state()
        if state.get("paused"):
            print("工作流已暂停")
            return None

        phase, stage = self._get_next_stage(state)
        if not stage:
            print("工作流已完成")
            return None

        try:
            result = self.execute_stage(stage, phase)
            self.facade.update_stage(phase, stage)
            return result
        except WorkflowError as e:
            print(f"执行失败: {e}")
            return None

    def execute_stages(self, stages: List[str], incremental: bool = True) -> List[dict]:
        """执行指定阶段列表（支持版本化增量更新）
        
        Args:
            stages: 要执行的阶段列表
            incremental: 是否启用增量更新（默认启用）
        
        Returns:
            执行结果列表
        """
        stage_names = [s.name for s in self.stages]
        
        # 版本化增量检测
        if incremental:
            plan = self.facade.get_versioned_incremental_plan(stages)
            
            if plan["mode"] == "none":
                print(f"\n✅ {plan['reason']}，跳过执行")
                return []
            
            if plan["mode"] == "incremental":
                print(f"\n🔄 版本化增量执行模式")
                print(f"   原因: {plan['reason']}")
                print(f"   待处理版本: {', '.join(plan['pending_versions'])}")
                
                stats = plan.get("stats", {})
                if stats.get("new_requirements"):
                    print(f"   新增需求: {stats['new_requirements']} 项")
                    by_priority = stats.get("by_priority", {})
                    if by_priority:
                        print(f"   优先级分布: {by_priority}")
                
                stages = plan["stages_to_run"]
                if not stages:
                    print(f"\n✅ 指定阶段不受影响，跳过执行")
                    return []
            else:
                print(f"\n🚀 全量执行模式: {plan['reason']}")
                print(f"   版本: {', '.join(plan.get('pending_versions', []))}")
                print(f"   需求: {len(plan.get('new_requirements', []))} 项")
                stages = plan["stages_to_run"]
        else:
            print(f"\n🚀 执行指定阶段: {', '.join(stages)}")

        results = []
        for stage in stages:
            if stage not in stage_names:
                print(f"⚠️ 未知阶段: {stage}，跳过")
                continue

            try:
                result = self.execute_stage(stage)
                results.append(result)
                
                # 🔧 修复：只在 requirement 阶段完成后记录版本处理
                if incremental and result.get("success") and stage == "requirement":
                    pending_versions = plan.get("pending_versions", [])
                    for version in pending_versions:
                        # 统计该版本的需求
                        version_reqs = [r for r in plan.get("new_requirements", []) 
                                       if hasattr(r, 'version') and r.version == version]
                        self.facade.record_version_processed(
                            version=version,
                            requirements_added=len(version_reqs) if version_reqs else len(plan.get("new_requirements", []))
                        )
                    print(f"   ✅ 已记录版本处理完成: {', '.join(pending_versions)}")
                    
            except (DependencyError, StageExecutionError, StageTimeoutError) as e:
                print(f"❌ 阶段 {stage} 执行失败: {e}")
                results.append({
                    "stage": stage,
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__
                })
                # 继续执行下一个阶段而不是中断
                continue

        return results

    def execute_full_cycle(self) -> dict:
        """执行完整工作流"""
        self.facade.reset()

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
                
                if stage_config.skip:
                    print(f"⏭️ 跳过阶段: {stage}")
                    stats["skipped"] += 1
                    continue
                    
                try:
                    result = self.execute_stage(stage, phase)
                    result["phase"] = phase
                    stats["stages"].append(result)
                    stats["success"] += 1
                    self.facade.update_stage(phase, stage)
                    
                except DependencyError as e:
                    print(f"⚠️ 依赖检查失败: {e}")
                    stats["stages"].append({
                        "stage": stage, "phase": phase,
                        "success": False, "error": str(e), "error_type": "dependency"
                    })
                    stats["failed"] += 1
                    stats["error"] = str(e)
                    raise
                    
                except StageExecutionError as e:
                    print(f"❌ 阶段执行失败: {e}")
                    stats["stages"].append({
                        "stage": stage, "phase": phase,
                        "success": False, "error": str(e), "error_type": "execution"
                    })
                    stats["failed"] += 1
                    stats["error"] = str(e)
                    raise
                    
                except StageTimeoutError as e:
                    print(f"⏰ 阶段执行超时: {e}")
                    stats["stages"].append({
                        "stage": stage, "phase": phase,
                        "success": False, "error": str(e), "error_type": "timeout"
                    })
                    stats["failed"] += 1
                    stats["error"] = str(e)
                    raise

        except WorkflowError:
            pass

        stats["duration"] = time.time() - start_time
        
        if stats["failed"] == 0:
            self.facade.record_cycle_complete()
            print(f"\n✅ PDCA 循环完成")
        else:
            print(f"\n❌ PDCA 循环中断: {stats['error']}")

        print(f"   总计: {stats['total']} 阶段")
        print(f"   成功: {stats['success']}")
        print(f"   失败: {stats['failed']}")
        print(f"   耗时: {stats['duration']:.1f}s")
        
        return stats

    def run_continuous(self):
        """持续执行工作流"""
        print(f"\n🔄 开始持续执行工作流")
        cycle = 0
        while self.running:
            cycle += 1
            print(f"\n{'='*60}")
            print(f"第 {cycle} 轮 PDCA 循环")
            print(f"{'='*60}")
            
            self.execute_full_cycle()
            
            interval = self.config["pdca"].get("cycle_interval_seconds", 60)
            max_cycles = self.config["pdca"].get("max_cycles", 0)
            
            if max_cycles > 0 and cycle >= max_cycles:
                print(f"\n达到最大循环次数 {max_cycles}，停止")
                break
            
            print(f"\n⏳ 等待 {interval} 秒后开始下一轮...")
            time.sleep(interval)

    def status(self) -> dict:
        """获取状态（包含断点续传信息）"""
        project_info = self._load_project_info()
        project_meta = self.facade.load_project_meta()
        
        # 获取各阶段的子任务进度
        stage_progress = {}
        for stage in self.stages:
            subtasks = STAGE_SUBTASKS.get(stage.name, [])
            if subtasks:
                progress = self.facade.get_progress(stage.name, 
                    [s.get("name", s) if isinstance(s, dict) else s for s in subtasks])
                stage_progress[stage.name] = progress
        
        return {
            "project": self.project_name,
            "project_dir": str(self.project_dir),
            "project_meta": {
                "name": project_meta.name,
                "project_name": project_meta.project_name,
                "package_name": project_meta.package_name,
                "backend_language": project_meta.backend_language,
                "frontend_framework": project_meta.frontend_framework
            },
            "goal": project_info.get("goal", "未设置"),
            "stage_progress": stage_progress,
            **self.facade.get_status(),
            "config": {
                "max_cycles": self.config["pdca"].get("max_cycles", 0),
                "stage_delay": self.config["execution"].get("stage_delay_seconds", 30)
            }
        }


# ==================== 入口 ====================

def main():
    parser = argparse.ArgumentParser(
        description="工作流执行器 - 统一的 PDCA 工作流管理",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查看状态
  python3 scripts/workflow.py -p my_project --status

  # 单步执行
  python3 scripts/workflow.py -p my_project --next --execute

  # 指定阶段
  python3 scripts/workflow.py -p my_project --stages requirement,design --execute

  # 使用模板
  python3 scripts/workflow.py -p my_project --template dev-only --execute

  # 从指定阶段开始
  python3 scripts/workflow.py -p my_project --from development --execute

  # 执行到指定阶段
  python3 scripts/workflow.py -p my_project --until testing --execute

  # 完整循环
  python3 scripts/workflow.py -p my_project --full-cycle --execute
        """
    )

    parser.add_argument("--project", "-p", required=True, help="项目名称")
    parser.add_argument("--status", "-s", action="store_true", help="查看状态")
    parser.add_argument("--next", "-n", action="store_true", help="执行下一阶段")
    parser.add_argument("--stages", help="执行指定阶段（逗号分隔）")
    parser.add_argument("--template", "-t", help="使用预设模板")
    parser.add_argument("--project-type", choices=[
        "fullstack", "backend_only", "frontend_only", "django_monolith", "microservices", "custom"
    ], help="项目类型（影响子任务拆分）")
    parser.add_argument("--subtask-strategy", choices=["layer", "module", "auto"],
                        help="子任务拆分策略: layer(按技术层), module(按功能模块), auto(自动选择)")
    parser.add_argument("--from", dest="from_stage", help="从指定阶段开始")
    parser.add_argument("--until", dest="until_stage", help="执行到指定阶段")
    parser.add_argument("--full-cycle", "-f", action="store_true", help="执行完整工作流")
    parser.add_argument("--start", action="store_true", help="启动持续执行")
    parser.add_argument("--pause", action="store_true", help="暂停")
    parser.add_argument("--resume", action="store_true", help="恢复")
    parser.add_argument("--reset", action="store_true", help="重置状态")
    parser.add_argument("--execute", "-e", action="store_true", help="实际执行子智能体")
    parser.add_argument("--gateway-url", default="http://127.0.0.1:18799", help="Gateway URL")
    parser.add_argument("--incremental", "-i", action="store_true", default=True, 
                        help="启用增量更新（默认启用）")
    parser.add_argument("--full", action="store_true", 
                        help="强制全量执行（忽略增量检测）")
    parser.add_argument("--reset-incremental", action="store_true", 
                        help="重置增量状态")
    parser.add_argument("--version-status", action="store_true",
                        help="显示版本状态")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="静默模式，抑制详细日志输出")
    parser.add_argument("--pending-versions", action="store_true",
                        help="显示待处理版本")
    parser.add_argument("--reset-version", action="store_true",
                        help="重置版本状态")
    parser.add_argument("--validate-input", action="store_true",
                        help="验证输入数据")
    parser.add_argument("--reset-for-incremental", action="store_true",
                        help="统一重置增量更新状态（输入状态 + 子任务状态 + 阶段状态）")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.WARNING if args.quiet else logging.INFO,
        format="%(message)s",
    )

    stages_override = None
    if args.stages:
        stages_override = [s.strip() for s in args.stages.split(",")]
    elif args.from_stage or args.until_stage:
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
        stages_override=stages_override,
        project_type=getattr(args, 'project_type', None),
        subtask_strategy=getattr(args, 'subtask_strategy', None)
    )
    if args.execute and executor.subagent_executor:
        executor.subagent_executor.gateway_url = args.gateway_url

    if args.status:
        result = executor.status()
        result["stages"] = [s.name for s in executor.stages]
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # 打印断点续传状态
        print("\n" + "=" * 60)
        print("📊 断点续传状态")
        print("=" * 60)
        executor.facade.print_status(
            stage=args.stages.split(",")[0] if args.stages else None
        )

    elif args.pause:
        executor.facade.pause()
        print("已暂停")

    elif args.resume:
        executor.facade.resume()
        print("已恢复")

    elif args.reset:
        executor.facade.reset()
        print("已重置")

    elif args.reset_incremental:
        executor.facade.reset_incremental_state()

    elif args.reset_version:
        executor.facade.reset_version_state()

    elif args.reset_for_incremental:
        executor.facade.reset_for_incremental_update()

    elif args.version_status:
        executor.facade.print_version_status()

    elif args.pending_versions:
        plan = executor.facade.get_versioned_incremental_plan()
        print(f"\n📋 待处理版本: {plan.get('pending_versions', [])}")
        print(f"   新增需求: {len(plan.get('new_requirements', []))}")

    elif args.validate_input:
        result = executor.facade.csv_parser.validate_input()
        print(f"\n✅ 输入验证: {'通过' if result['valid'] else '失败'}")
        if result['errors']:
            print(f"❌ 错误: {result['errors']}")
        if result['warnings']:
            print(f"⚠️ 警告: {result['warnings']}")
        print(f"\n📊 统计: {result['stats']}")

    elif args.stages or args.from_stage or args.until_stage:
        # 确定是否使用增量模式
        use_incremental = args.incremental and not args.full
        results = executor.execute_stages(stages_override, incremental=use_incremental)
        if not args.execute:
            print(f"\n📋 执行结果（使用 --execute 实际执行）:")
            for r in results:
                print(f"  - [{r.get('phase', '').upper()}] {r.get('stage')}")

    elif args.full_cycle:
        stats = executor.execute_full_cycle()
        if not args.execute:
            print(f"\n📋 任务配置（使用 --execute 实际执行）:")
            print(json.dumps([s.get("params") for s in stats.get("stages", []) if s.get("params")], 
                           indent=2, ensure_ascii=False))

    elif args.next:
        result = executor.execute_next()
        if result and not args.execute:
            print(f"\n📋 配置（使用 --execute 实际执行）:")
            print(json.dumps(result.get("params"), indent=2, ensure_ascii=False))

    elif args.start:
        executor.run_continuous()

    else:
        result = executor.status()
        result["stages"] = [s.name for s in executor.stages]
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()