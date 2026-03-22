#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上下文管理器
Context Manager

为智能体提供增强的上下文传递能力，包括：
- 阶段专属上下文生成
- 相关决策过滤
- 依赖关系追踪
- 上下文版本控制
- 输出摘要提取

使用方式：
  from scripts.context_manager import ContextManager
  
  cm = ContextManager(project_name="my_project")
  
  # 为特定阶段准备上下文
  context = cm.prepare_context(stage="design")
  
  # 获取上下文摘要
  summary = cm.get_context_summary(stage="design")
  
  # 提取输出摘要
  cm.extract_output_summary(stage="requirement")
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

# 使用绝对导入
import sys
sys.path.insert(0, str(Path(__file__).parent))

from state_manager import StateManager


class ContextManager:
    """上下文管理器 - 增强智能体间的上下文传递"""
    
    # 阶段依赖关系
    STAGE_DEPENDENCIES = {
        "requirement": [],
        "design": ["requirement"],
        "development": ["design", "requirement"],
        "testing": ["development", "design"],
        "deployment": ["testing", "development"],
        "operations": ["deployment", "testing"],
        "monitor": ["operations", "deployment"],
        "optimizer": ["monitor", "operations", "all"]
    }
    
    # 每个阶段需要的决策类型
    RELEVANT_DECISIONS = {
        "requirement": ["需求决策", "优先级决策", "业务规则"],
        "design": ["技术选型", "架构决策", "接口设计", "需求决策", "优先级决策"],
        "development": ["技术选型", "架构决策", "实现决策", "代码规范", "接口设计"],
        "testing": ["测试策略", "覆盖决策", "技术选型", "接口设计"],
        "deployment": ["部署决策", "环境配置", "技术选型", "测试策略"],
        "operations": ["运维决策", "监控策略", "部署决策", "环境配置"],
        "monitor": ["监控策略", "告警规则", "运维决策", "性能指标"],
        "optimizer": ["优化决策", "性能策略", "监控策略", "告警规则"]
    }
    
    # 每个阶段需要的输入文件模式
    INPUT_PATTERNS = {
        "requirement": [
            "input/feedback/*.md",
            "input/meetings/*.md",
            "input/emails/*.md",
            "input/tickets/*.md"
        ],
        "design": [
            "output/requirements/*.md",
            "output/requirements/*.json"
        ],
        "development": [
            "output/design/*.md",
            "output/design/**/*.md"
        ],
        "testing": [
            "output/src/**/*.py",
            "output/src/**/*.js",
            "output/design/*.md"
        ],
        "deployment": [
            "output/tests/*.md",
            "output/src/**/*"
        ],
        "operations": [
            "output/deploy/*",
            "output/tests/*.md"
        ],
        "monitor": [
            "output/deploy/*",
            "output/operations/*"
        ],
        "optimizer": [
            "output/**/*"
        ]
    }
    
    # 上下文模板
    CONTEXT_TEMPLATE = """
# 项目: {project_name} | 阶段: {stage} | 角色: {agent_role}

## 📋 任务说明
{task_description}

---

## 🎯 项目上下文

### 项目信息
- **名称**: {project_name}
- **目标**: {project_goal}
- **状态**: {project_status}
- **当前阶段**: {current_stage}
- **已完成阶段**: {completed_stages}

### 技术栈
{tech_stack}

### 约束条件
{constraints}

---

## 📊 上游输出摘要

{upstream_summaries}

---

## 📝 相关决策记录

{relevant_decisions}

---

## ⚠️ 待处理反馈

{pending_feedback}

---

## 📁 输入文件

{input_files}

---

## 📂 输出要求

**输出目录**: `{output_dir}`

### 必需输出
{required_outputs}

### 输出格式要求
{output_format}

---

## ✅ 完成标准

{completion_criteria}

---

## 📌 注意事项

{notes}

---

**请根据以上上下文完成任务，并在完成后生成执行日志。**
"""
    
    def __init__(self, project_name: str, base_dir: str = None):
        self.project_name = project_name
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent
        self.project_dir = self.base_dir / "projects" / project_name
        
        # 初始化状态管理器
        self.state = StateManager(project_name, base_dir)
        
        # 上下文缓存目录
        self.context_cache_dir = self.project_dir / "state" / "contexts"
        self.context_cache_dir.mkdir(parents=True, exist_ok=True)
    
    # ==================== 核心方法 ====================
    
    def prepare_context(self, stage: str, phase: str = None, 
                        task_description: str = None) -> dict:
        """
        为特定阶段准备完整上下文
        
        Args:
            stage: 阶段名称
            phase: PDCA 阶段
            task_description: 自定义任务描述
        
        Returns:
            完整上下文字典
        """
        # 获取状态
        state = self.state.get()
        
        # 获取阶段依赖的上下文
        upstream_summaries = self._get_upstream_summaries(stage)
        
        # 获取相关决策
        relevant_decisions = self._get_relevant_decisions(stage)
        
        # 获取待处理反馈
        pending_feedback = self.state.get_pending_feedback(agent=stage)
        
        # 获取输入文件
        input_files = self._get_input_files(stage)
        
        # 获取输出要求
        output_requirements = self._get_output_requirements(stage)
        
        # 构建上下文
        context = {
            "meta": {
                "stage": stage,
                "phase": phase or self._infer_phase(stage),
                "prepared_at": datetime.now().isoformat()
            },
            "project": {
                "name": state["project"]["name"],
                "goal": state["project"]["goal"],
                "description": state["project"].get("description", ""),
                "status": state["project"]["status"],
                "tech_stack": state["project"].get("tech_stack", []),
                "constraints": state["context"]["constraints"]
            },
            "workflow": {
                "cycle": state["workflow"]["cycle"],
                "current_stage": state["workflow"]["current_stage"],
                "completed_stages": state["workflow"]["completed_stages"]
            },
            "upstream_summaries": upstream_summaries,
            "decisions": relevant_decisions,
            "feedback": pending_feedback,
            "inputs": {
                "files": input_files,
                "directories": self._get_input_directories(stage)
            },
            "outputs": output_requirements,
            "quality_criteria": self._get_quality_criteria(stage),
            "notes": self._get_stage_notes(stage)
        }
        
        # 如果有自定义任务描述
        if task_description:
            context["task_description"] = task_description
        else:
            context["task_description"] = self._get_default_task_description(stage)
        
        # 缓存上下文
        self._cache_context(stage, context)
        
        return context
    
    def generate_task_prompt(self, stage: str, phase: str = None,
                              task_description: str = None) -> str:
        """
        生成完整的任务提示词
        
        Args:
            stage: 阶段名称
            phase: PDCA 阶段
            task_description: 自定义任务描述
        
        Returns:
            格式化的任务提示词
        """
        context = self.prepare_context(stage, phase, task_description)
        state = self.state.get()
        
        # 加载阶段提示词模板
        system_prompt = self._load_stage_prompt(stage)
        
        # 格式化上游摘要
        upstream_str = self._format_upstream_summaries(context["upstream_summaries"])
        
        # 格式化决策
        decisions_str = self._format_decisions(context["decisions"])
        
        # 格式化反馈
        feedback_str = self._format_feedback(context["feedback"])
        
        # 格式化输入文件
        input_files_str = self._format_input_files(context["inputs"]["files"])
        
        # 格式化输出要求
        output_str = self._format_output_requirements(context["outputs"])
        
        # 格式化约束
        constraints_str = self._format_constraints(context["project"]["constraints"])
        
        # 格式化技术栈
        tech_stack_str = self._format_tech_stack(context["project"]["tech_stack"])
        
        # 生成完整提示词
        task_prompt = self.CONTEXT_TEMPLATE.format(
            project_name=context["project"]["name"],
            stage=stage.upper(),
            agent_role=self._get_agent_role(stage),
            task_description=context["task_description"],
            project_goal=context["project"]["goal"],
            project_status=context["project"]["status"],
            current_stage=context["workflow"]["current_stage"] or "未开始",
            completed_stages=", ".join(context["workflow"]["completed_stages"]) or "无",
            tech_stack=tech_stack_str,
            constraints=constraints_str,
            upstream_summaries=upstream_str,
            relevant_decisions=decisions_str,
            pending_feedback=feedback_str,
            input_files=input_files_str,
            output_dir=self._get_output_dir(stage),
            required_outputs=output_str["required"],
            output_format=output_str["format"],
            completion_criteria=self._format_completion_criteria(context["quality_criteria"]),
            notes=context["notes"]
        )
        
        return system_prompt + "\n\n" + task_prompt
    
    def extract_output_summary(self, stage: str) -> dict:
        """
        从阶段输出中提取摘要
        
        Args:
            stage: 阶段名称
        
        Returns:
            输出摘要
        """
        output_dir = self._get_output_dir(stage)
        
        if not output_dir.exists():
            return {"status": "no_output", "files": [], "summary": ""}
        
        # 扫描输出文件
        files = []
        for pattern in ["*.md", "*.json", "*.py", "*.js", "*.yaml", "*.yml"]:
            files.extend(output_dir.glob(pattern))
        
        # 提取摘要
        summary = self._extract_summary_from_files(stage, files)
        
        # 更新状态
        self.state.update(
            f"agents.{stage}.output_summary",
            summary["summary"][:500] if summary.get("summary") else None
        )
        
        return {
            "status": "success",
            "files": [str(f.relative_to(self.project_dir)) for f in files],
            "summary": summary.get("summary", ""),
            "stats": summary.get("stats", {})
        }
    
    def get_context_summary(self, stage: str) -> str:
        """
        获取阶段上下文的简短摘要
        
        用于快速了解当前上下文状态
        """
        context = self.prepare_context(stage)
        
        lines = [
            f"## {stage.upper()} 阶段上下文摘要",
            "",
            f"- 项目: {context['project']['name']}",
            f"- 已完成阶段: {', '.join(context['workflow']['completed_stages']) or '无'}",
            f"- 相关决策: {len(context['decisions'])} 条",
            f"- 待处理反馈: {len(context['feedback'])} 条",
            f"- 输入文件: {len(context['inputs']['files'])} 个"
        ]
        
        if context["upstream_summaries"]:
            lines.append("")
            lines.append("### 上游输出摘要")
            for upstream_stage, summary in context["upstream_summaries"].items():
                lines.append(f"- {upstream_stage}: {summary[:100]}..." if len(summary) > 100 else f"- {upstream_stage}: {summary}")
        
        return "\n".join(lines)
    
    # ==================== 内部方法 ====================
    
    def _get_upstream_summaries(self, stage: str) -> Dict[str, str]:
        """获取上游阶段的输出摘要"""
        dependencies = self.STAGE_DEPENDENCIES.get(stage, [])
        summaries = {}
        
        state = self.state.get()
        completed_stages = state["workflow"]["completed_stages"]
        
        for dep_stage in dependencies:
            if dep_stage == "all":
                # 获取所有已完成阶段的摘要
                for completed in completed_stages:
                    summary = self._get_stage_summary(completed)
                    if summary:
                        summaries[completed] = summary
            elif dep_stage in completed_stages:
                summary = self._get_stage_summary(dep_stage)
                if summary:
                    summaries[dep_stage] = summary
        
        return summaries
    
    def _get_stage_summary(self, stage: str) -> Optional[str]:
        """获取特定阶段的输出摘要"""
        # 从状态中获取
        state = self.state.get()
        if stage in state.get("agents", {}):
            summary = state["agents"][stage].get("output_summary")
            if summary:
                return summary
        
        # 从摘要文件获取
        summary_file = self._get_output_dir(stage) / ".summary.json"
        if summary_file.exists():
            try:
                data = json.loads(summary_file.read_text(encoding="utf-8"))
                return data.get("summary")
            except:
                pass
        
        return None
    
    def _get_relevant_decisions(self, stage: str) -> List[dict]:
        """获取与阶段相关的决策"""
        state = self.state.get()
        all_decisions = state["context"]["decisions"]
        
        relevant_types = self.RELEVANT_DECISIONS.get(stage, [])
        
        return [
            d for d in all_decisions 
            if d.get("type") in relevant_types
        ]
    
    def _get_input_files(self, stage: str) -> List[dict]:
        """获取阶段的输入文件列表"""
        patterns = self.INPUT_PATTERNS.get(stage, [])
        files = []
        
        for pattern in patterns:
            for file_path in self.project_dir.glob(pattern):
                if file_path.is_file():
                    files.append({
                        "path": str(file_path.relative_to(self.project_dir)),
                        "size": file_path.stat().st_size,
                        "modified": datetime.fromtimestamp(
                            file_path.stat().st_mtime
                        ).isoformat()
                    })
        
        return files
    
    def _get_input_directories(self, stage: str) -> List[str]:
        """获取阶段的输入目录"""
        # 直接定义输入映射，避免循环导入
        input_map = {
            "requirement": "input/",
            "design": "output/requirements/",
            "development": "output/design/",
            "testing": "output/src/",
            "deployment": "output/tests/",
            "operations": "output/deploy/",
            "monitor": "output/",
            "optimizer": "output/monitor/"
        }
        input_dir = input_map.get(stage, "input/")
        return [str(self.project_dir / input_dir)]
    
    def _get_output_requirements(self, stage: str) -> dict:
        """获取阶段的输出要求"""
        requirements = {
            "requirement": {
                "required": [
                    "用户需求文档.md",
                    "软件需求规格说明书.md",
                    "rtm.json"
                ],
                "format": "Markdown + JSON"
            },
            "design": {
                "required": [
                    "架构设计文档.md",
                    "接口设计文档.md",
                    "数据库设计.md"
                ],
                "format": "Markdown"
            },
            "development": {
                "required": [
                    "src/backend/",
                    "src/frontend/"
                ],
                "format": "代码文件"
            },
            "testing": {
                "required": [
                    "测试报告.md",
                    "tests/"
                ],
                "format": "测试文件 + Markdown"
            },
            "deployment": {
                "required": [
                    "docker-compose.yml",
                    "Dockerfile",
                    "部署文档.md"
                ],
                "format": "YAML + Markdown"
            },
            "operations": {
                "required": [
                    "README.md",
                    "health_check.sh"
                ],
                "format": "Markdown + Shell"
            },
            "monitor": {
                "required": [
                    "quality-report.md"
                ],
                "format": "Markdown"
            },
            "optimizer": {
                "required": [
                    "optimization-plan.md"
                ],
                "format": "Markdown"
            }
        }
        
        return requirements.get(stage, {
            "required": [],
            "format": "Markdown"
        })
    
    def _get_quality_criteria(self, stage: str) -> dict:
        """获取阶段的质量标准"""
        criteria = {
            "requirement": {
                "min_score": 90,
                "checks": [
                    "每条需求有清晰的用户故事",
                    "每条需求有≥3条验收标准",
                    "优先级标注明确",
                    "需求符合INVEST原则"
                ]
            },
            "design": {
                "min_score": 85,
                "checks": [
                    "架构图清晰",
                    "接口定义完整",
                    "数据库设计规范",
                    "技术选型合理"
                ]
            },
            "development": {
                "min_score": 80,
                "checks": [
                    "代码可运行",
                    "代码规范",
                    "基本功能实现",
                    "无明显Bug"
                ]
            },
            "testing": {
                "min_score": 80,
                "checks": [
                    "测试覆盖主要功能",
                    "测试报告完整",
                    "无严重问题遗留"
                ]
            },
            "deployment": {
                "min_score": 85,
                "checks": [
                    "Docker配置正确",
                    "部署文档完整",
                    "启动脚本可用"
                ]
            },
            "operations": {
                "min_score": 80,
                "checks": [
                    "运维文档完整",
                    "健康检查可用",
                    "监控配置合理"
                ]
            },
            "monitor": {
                "min_score": 80,
                "checks": [
                    "质量报告完整",
                    "指标定义清晰",
                    "问题记录详尽"
                ]
            },
            "optimizer": {
                "min_score": 75,
                "checks": [
                    "优化计划可行",
                    "问题分析准确",
                    "改进建议具体"
                ]
            }
        }
        
        return criteria.get(stage, {"min_score": 70, "checks": []})
    
    def _get_stage_notes(self, stage: str) -> str:
        """获取阶段特定注意事项"""
        notes = {
            "requirement": """
- 从用户角度出发，避免技术术语
- 优先级排序要考虑业务价值
- 验收标准要可测试、可验证
- 注意区分需求和解决方案
""",
            "design": """
- 架构设计要考虑扩展性
- 接口设计要前后端对齐
- 数据库设计要规范
- 技术选型要有理由
""",
            "development": """
- 代码风格要统一
- 关键函数要有注释
- 注意安全性问题
- 错误处理要完善
""",
            "testing": """
- 覆盖主要业务场景
- 边界条件测试
- 异常情况测试
- 性能基准测试
""",
            "deployment": """
- 环境变量配置
- 数据持久化
- 日志收集
- 监控接入
""",
            "operations": """
- 启动/停止脚本
- 健康检查
- 日志查看
- 故障排查
""",
            "monitor": """
- 关键指标监控
- 告警阈值设置
- 性能趋势分析
- 问题追踪
""",
            "optimizer": """
- 数据驱动优化
- ROI评估
- 渐进式改进
- 持续迭代
"""
        }
        
        return notes.get(stage, "- 按照最佳实践执行")
    
    def _get_output_dir(self, stage: str) -> Path:
        """获取阶段输出目录"""
        # 直接定义输出映射，避免循环导入
        output_map = {
            "requirement": "output/requirements/",
            "design": "output/design/",
            "development": "output/src/",
            "testing": "output/tests/",
            "deployment": "output/deploy/",
            "operations": "output/operations/",
            "monitor": "output/monitor/",
            "optimizer": "output/optimizer/"
        }
        output_dir = output_map.get(stage, f"output/{stage}/")
        return self.project_dir / output_dir
    
    def _infer_phase(self, stage: str) -> str:
        """从阶段名称推断 PDCA 阶段"""
        phase_map = {
            "requirement": "plan",
            "design": "plan",
            "development": "do",
            "testing": "do",
            "deployment": "do",
            "operations": "check",
            "monitor": "check",
            "optimizer": "act"
        }
        return phase_map.get(stage, "unknown")
    
    def _get_agent_role(self, stage: str) -> str:
        """获取智能体角色名称"""
        roles = {
            "requirement": "需求分析师",
            "design": "架构师",
            "development": "开发工程师",
            "testing": "测试专家",
            "deployment": "部署工程师",
            "operations": "运维工程师",
            "monitor": "质量监控员",
            "optimizer": "优化专家"
        }
        return roles.get(stage, "智能体")
    
    def _get_default_task_description(self, stage: str) -> str:
        """获取默认任务描述"""
        descriptions = {
            "requirement": "分析输入的需求信息，生成规范的需求文档",
            "design": "根据需求文档，设计系统架构和详细方案",
            "development": "根据设计文档，实现功能代码",
            "testing": "对实现的代码进行测试验证",
            "deployment": "准备部署配置和文档",
            "operations": "编写运维文档和脚本",
            "monitor": "检查质量并生成报告",
            "optimizer": "分析问题并提出优化方案"
        }
        return descriptions.get(stage, "完成阶段任务")
    
    def _load_stage_prompt(self, stage: str) -> str:
        """加载阶段系统提示词"""
        prompt_path = self.base_dir / "prompts" / stage / "system.md"
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        return f"你是 {self._get_agent_role(stage)}，请完成你的任务。"
    
    def _cache_context(self, stage: str, context: dict):
        """缓存上下文"""
        cache_file = self.context_cache_dir / f"{stage}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        cache_file.write_text(json.dumps(context, indent=2, ensure_ascii=False), encoding="utf-8")
    
    def _extract_summary_from_files(self, stage: str, files: List[Path]) -> dict:
        """从输出文件中提取摘要"""
        summary = ""
        stats = {
            "file_count": len(files),
            "total_size": sum(f.stat().st_size for f in files if f.is_file())
        }
        
        # 尝试读取摘要文件
        summary_file = self._get_output_dir(stage) / ".summary.json"
        if summary_file.exists():
            try:
                data = json.loads(summary_file.read_text(encoding="utf-8"))
                summary = data.get("summary", "")
            except:
                pass
        
        # 如果没有摘要文件，尝试从主要文档提取
        if not summary:
            main_docs = {
                "requirement": "用户需求文档.md",
                "design": "架构设计文档.md",
                "development": "README.md",
                "testing": "测试报告.md",
                "deployment": "部署文档.md",
                "operations": "README.md",
                "monitor": "quality-report.md",
                "optimizer": "optimization-plan.md"
            }
            
            main_doc = main_docs.get(stage)
            if main_doc:
                doc_path = self._get_output_dir(stage) / main_doc
                if doc_path.exists():
                    content = doc_path.read_text(encoding="utf-8")
                    # 提取前500字符作为摘要
                    summary = content[:500].replace("#", "").strip()
        
        return {"summary": summary, "stats": stats}
    
    # ==================== 格式化方法 ====================
    
    def _format_upstream_summaries(self, summaries: Dict[str, str]) -> str:
        """格式化上游摘要"""
        if not summaries:
            return "无上游输出（这是第一个阶段）"
        
        lines = []
        for stage, summary in summaries.items():
            lines.append(f"### {stage.upper()}")
            lines.append(summary)
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_decisions(self, decisions: List[dict]) -> str:
        """格式化决策列表"""
        if not decisions:
            return "无相关决策记录"
        
        lines = []
        for d in decisions:
            lines.append(f"- **[{d.get('id', '?')}]** {d.get('type', '?')}: {d.get('content', '?')}")
            lines.append(f"  - 决策者: {d.get('by', '?')} | 时间: {d.get('at', '?')}")
            if d.get('rationale'):
                lines.append(f"  - 理由: {d['rationale']}")
        
        return "\n".join(lines)
    
    def _format_feedback(self, feedback: List[dict]) -> str:
        """格式化反馈列表"""
        if not feedback:
            return "无待处理反馈"
        
        lines = []
        for f in feedback:
            lines.append(f"- **[{f.get('id', '?')}]** {f.get('type', '?')} (来自 {f.get('from', '?')})")
            lines.append(f"  - 内容: {f.get('content', {})}")
        
        return "\n".join(lines)
    
    def _format_input_files(self, files: List[dict]) -> str:
        """格式化输入文件列表"""
        if not files:
            return "无输入文件"
        
        lines = []
        for f in files[:20]:  # 限制显示数量
            size_kb = f["size"] / 1024
            lines.append(f"- `{f['path']}` ({size_kb:.1f} KB)")
        
        if len(files) > 20:
            lines.append(f"- ... 还有 {len(files) - 20} 个文件")
        
        return "\n".join(lines)
    
    def _format_output_requirements(self, requirements: dict) -> dict:
        """格式化输出要求"""
        required = "\n".join(f"- {r}" for r in requirements.get("required", []))
        return {
            "required": required or "无特定要求",
            "format": requirements.get("format", "Markdown")
        }
    
    def _format_constraints(self, constraints: dict) -> str:
        """格式化约束条件"""
        if not constraints:
            return "无特殊约束"
        
        lines = []
        for key, value in constraints.items():
            if isinstance(value, dict):
                lines.append(f"- **{key}**: {value.get('value', '?')}")
            else:
                lines.append(f"- **{key}**: {value}")
        
        return "\n".join(lines)
    
    def _format_tech_stack(self, tech_stack: List[str]) -> str:
        """格式化技术栈"""
        if not tech_stack:
            return "未指定"
        return ", ".join(tech_stack)
    
    def _format_completion_criteria(self, criteria: dict) -> str:
        """格式化完成标准"""
        lines = [f"**最低质量分**: {criteria.get('min_score', 70)}%"]
        lines.append("")
        lines.append("**检查项**:")
        for check in criteria.get("checks", []):
            lines.append(f"- [ ] {check}")
        
        return "\n".join(lines)


# ==================== CLI 接口 ====================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="上下文管理器")
    parser.add_argument("--project", "-p", required=True, help="项目名称")
    parser.add_argument("--stage", "-s", required=True, help="阶段名称")
    parser.add_argument("--summary", action="store_true", help="查看上下文摘要")
    parser.add_argument("--prompt", action="store_true", help="生成完整提示词")
    parser.add_argument("--extract", action="store_true", help="提取输出摘要")
    
    args = parser.parse_args()
    
    cm = ContextManager(project_name=args.project)
    
    if args.summary:
        print(cm.get_context_summary(args.stage))
    elif args.prompt:
        print(cm.generate_task_prompt(args.stage))
    elif args.extract:
        result = cm.extract_output_summary(args.stage)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        context = cm.prepare_context(args.stage)
        print(json.dumps(context, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    exit(main())