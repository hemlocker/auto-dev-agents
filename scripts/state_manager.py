#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一状态管理器
Unified State Manager

为智能体协作提供统一的状态管理，包括：
- 单一状态源（Single Source of Truth）
- 状态变更追踪
- 状态版本控制
- 状态回滚支持
- 事件日志记录

使用方式：
  from scripts.state_manager import StateManager
  
  state = StateManager(project_name="my_project")
  
  # 获取状态
  current = state.get()
  
  # 更新状态
  state.update("workflow.current_stage", "design")
  
  # 记录事件
  state.log_event(agent="requirement", action="completed", result="生成需求文档")
  
  # 记录决策
  state.record_decision(
      decision_id="ARCH-001",
      decision_type="技术选型",
      content="使用 FastAPI 作为后端框架",
      by="design"
  )
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
from copy import deepcopy


class StateManager:
    """统一状态管理器 - 单一状态源"""
    
    # 状态结构定义
    STATE_SCHEMA = {
        "meta": {
            "version": "1.0",
            "created_at": None,
            "updated_at": None,
            "updated_by": None
        },
        "project": {
            "name": None,
            "goal": None,
            "description": None,
            "tech_stack": [],
            "constraints": {},
            "status": "created"  # created/running/paused/completed/failed
        },
        "workflow": {
            "cycle": 0,
            "current_phase": None,  # plan/do/check/act
            "current_stage": None,  # requirement/design/...
            "paused": False,
            "started_at": None,
            "completed_stages": []
        },
        "agents": {
            # "{agent_name}": {
            #     "status": "idle",  # idle/running/completed/failed
            #     "last_run": None,
            #     "last_result": None,
            #     "output_summary": None,
            #     "error": None
            # }
        },
        "context": {
            "decisions": [],  # 重大决策记录
            "constraints": {},  # 约束条件
            "assumptions": []   # 假设条件
        },
        "events": [
            # {
            #     "timestamp": "ISO时间戳",
            #     "agent": "智能体名称",
            #     "action": "动作类型",
            #     "result": "结果描述",
            #     "details": {}
            # }
        ],
        "feedback": {
            "pending": [],  # 待处理的反馈
            "resolved": []  # 已解决的反馈
        },
        "quality": {
            "stage_scores": {},  # {stage: score}
            "avg_score": 0,
            "issues": []
        }
    }
    
    # 智能体列表
    AGENTS = ["coordinator", "requirement", "design", "development", 
              "testing", "deployment", "operations", "monitor", "optimizer"]
    
    # 阶段列表
    STAGES = ["requirement", "design", "development", "testing",
              "deployment", "operations", "monitor", "optimizer"]
    
    # PDCA 阶段映射
    PHASE_MAP = {
        "plan": ["requirement", "design"],
        "do": ["development", "testing", "deployment"],
        "check": ["operations", "monitor"],
        "act": ["optimizer"]
    }
    
    def __init__(self, project_name: str, base_dir: str = None):
        self.project_name = project_name
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent
        self.project_dir = self.base_dir / "projects" / project_name
        self.state_file = self.project_dir / "state" / "state.json"
        self.history_dir = self.project_dir / "state" / "history"
        self.events_file = self.project_dir / "state" / "events.jsonl"
        
        # 确保目录存在
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)
    
    # ==================== 核心操作 ====================
    
    def get(self) -> dict:
        """获取完整状态"""
        if not self.state_file.exists():
            return self._init_state()
        return self._load_state()
    
    def get_section(self, section: str) -> Any:
        """
        获取状态的某个部分
        
        Args:
            section: 部分名称，支持点号分隔，如 "workflow.current_stage"
        """
        state = self.get()
        keys = section.split(".")
        result = state
        for key in keys:
            if isinstance(result, dict) and key in result:
                result = result[key]
            else:
                return None
        return result
    
    def update(self, path: str, value: Any, by: str = "system") -> bool:
        """
        更新状态
        
        Args:
            path: 状态路径，如 "workflow.current_stage"
            value: 新值
            by: 更新者
        
        Returns:
            是否成功
        """
        state = self.get()
        
        # 保存历史版本
        self._save_history(state)
        
        # 更新值
        keys = path.split(".")
        target = state
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        
        target[keys[-1]] = value
        
        # 更新元数据
        state["meta"]["updated_at"] = datetime.now().isoformat()
        state["meta"]["updated_by"] = by
        
        # 保存
        self._save_state(state)
        return True
    
    def batch_update(self, updates: Dict[str, Any], by: str = "system") -> bool:
        """
        批量更新状态
        
        Args:
            updates: {path: value} 格式的更新字典
        """
        state = self.get()
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
        self._save_state(state)
        return True
    
    def reset(self, keep_project: bool = True) -> dict:
        """
        重置状态
        
        Args:
            keep_project: 是否保留项目信息
        """
        new_state = self._init_state()
        
        if keep_project:
            old_state = self.get()
            new_state["project"] = old_state.get("project", new_state["project"])
        
        self._save_state(new_state)
        return new_state
    
    # ==================== 工作流状态 ====================
    
    def start_workflow(self) -> dict:
        """启动工作流"""
        return self.batch_update({
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
        state = self.get()
        current_stage = state["workflow"]["current_stage"]
        current_phase = state["workflow"]["current_phase"]
        
        # 获取下一阶段
        next_phase, next_stage = self._get_next_stage(current_phase, current_stage)
        
        if next_stage is None:
            # 循环结束
            return None
        
        # 更新状态
        self.batch_update({
            "workflow.current_phase": next_phase,
            "workflow.current_stage": next_stage
        }, by="workflow")
        
        return next_stage
    
    def complete_stage(self, stage: str, result: dict = None) -> bool:
        """
        完成一个阶段
        
        Args:
            stage: 阶段名称
            result: 阶段结果
        """
        state = self.get()
        
        if stage not in state["workflow"]["completed_stages"]:
            state["workflow"]["completed_stages"].append(stage)
        
        # 更新智能体状态
        if stage in state["agents"]:
            state["agents"][stage]["status"] = "completed"
            state["agents"][stage]["last_run"] = datetime.now().isoformat()
            if result:
                state["agents"][stage]["last_result"] = result.get("status")
                state["agents"][stage]["output_summary"] = result.get("summary")
        
        state["meta"]["updated_at"] = datetime.now().isoformat()
        self._save_state(state)
        return True
    
    def pause_workflow(self) -> bool:
        """暂停工作流"""
        return self.update("workflow.paused", True, by="workflow")
    
    def resume_workflow(self) -> bool:
        """恢复工作流"""
        return self.update("workflow.paused", False, by="workflow")
    
    def complete_workflow(self, success: bool = True) -> bool:
        """完成工作流"""
        status = "completed" if success else "failed"
        return self.batch_update({
            "project.status": status,
            "workflow.current_phase": None,
            "workflow.current_stage": None
        }, by="workflow")
    
    # ==================== 智能体状态 ====================
    
    def init_agents(self):
        """初始化所有智能体状态"""
        agents_state = {}
        for agent in self.AGENTS:
            agents_state[agent] = {
                "status": "idle",
                "last_run": None,
                "last_result": None,
                "output_summary": None,
                "error": None
            }
        self.update("agents", agents_state, by="system")
    
    def set_agent_status(self, agent: str, status: str, error: str = None):
        """
        设置智能体状态
        
        Args:
            agent: 智能体名称
            status: 状态 (idle/running/completed/failed)
            error: 错误信息
        """
        if agent not in self.AGENTS:
            return False
        
        updates = {
            f"agents.{agent}.status": status,
            f"agents.{agent}.last_run": datetime.now().isoformat()
        }
        if error:
            updates[f"agents.{agent}.error"] = error
        
        return self.batch_update(updates, by=agent)
    
    def get_agent_status(self, agent: str) -> Optional[dict]:
        """获取智能体状态"""
        return self.get_section(f"agents.{agent}")
    
    # ==================== 上下文管理 ====================
    
    def record_decision(self, decision_id: str, decision_type: str, 
                         content: str, by: str, rationale: str = None):
        """
        记录重要决策
        
        Args:
            decision_id: 决策ID，如 "ARCH-001"
            decision_type: 决策类型，如 "技术选型"、"架构决策"
            content: 决策内容
            by: 决策者
            rationale: 决策理由
        """
        state = self.get()
        
        decision = {
            "id": decision_id,
            "type": decision_type,
            "content": content,
            "by": by,
            "at": datetime.now().isoformat(),
            "rationale": rationale
        }
        
        state["context"]["decisions"].append(decision)
        self._save_state(state)
        
        # 记录事件
        self.log_event(
            agent=by,
            action="decision",
            result=f"做出决策: {decision_id}",
            details=decision
        )
    
    def get_decisions(self, decision_type: str = None) -> list:
        """获取决策列表"""
        state = self.get()
        decisions = state["context"]["decisions"]
        
        if decision_type:
            return [d for d in decisions if d["type"] == decision_type]
        return decisions
    
    def add_constraint(self, key: str, value: Any, by: str = "system"):
        """添加约束条件"""
        state = self.get()
        state["context"]["constraints"][key] = {
            "value": value,
            "added_by": by,
            "added_at": datetime.now().isoformat()
        }
        self._save_state(state)
    
    def get_context_for_stage(self, stage: str) -> dict:
        """
        获取特定阶段的上下文
        
        返回该阶段需要的所有上下文信息
        """
        state = self.get()
        
        # 根据阶段确定需要哪些决策
        decision_types = self._get_relevant_decision_types(stage)
        
        context = {
            "project": state["project"],
            "decisions": [d for d in state["context"]["decisions"] 
                         if d["type"] in decision_types],
            "constraints": state["context"]["constraints"],
            "completed_stages": state["workflow"]["completed_stages"],
            "quality_scores": state["quality"]["stage_scores"]
        }
        
        return context
    
    # ==================== 事件日志 ====================
    
    def log_event(self, agent: str, action: str, result: str, 
                  details: dict = None):
        """
        记录事件
        
        Args:
            agent: 智能体名称
            action: 动作类型
            result: 结果描述
            details: 详细信息
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "action": action,
            "result": result,
            "details": details or {}
        }
        
        # 追加到事件文件
        with open(self.events_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        
        # 也更新到状态中（最近100条）
        state = self.get()
        state["events"].append(event)
        if len(state["events"]) > 100:
            state["events"] = state["events"][-100:]
        self._save_state(state)
    
    def get_events(self, agent: str = None, action: str = None, 
                   limit: int = 50) -> list:
        """
        获取事件日志
        
        Args:
            agent: 按智能体过滤
            action: 按动作类型过滤
            limit: 限制数量
        """
        state = self.get()
        events = state["events"]
        
        if agent:
            events = [e for e in events if e["agent"] == agent]
        if action:
            events = [e for e in events if e["action"] == action]
        
        return events[-limit:]
    
    # ==================== 反馈系统 ====================
    
    def send_feedback(self, from_agent: str, to_agent: str, 
                      feedback_type: str, content: dict):
        """
        发送反馈
        
        Args:
            from_agent: 来源智能体
            to_agent: 目标智能体
            feedback_type: 类型 (issue/suggestion/request)
            content: 反馈内容
        """
        state = self.get()
        
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
        self._save_state(state)
        
        # 记录事件
        self.log_event(
            agent=from_agent,
            action="feedback",
            result=f"发送反馈给 {to_agent}",
            details=feedback
        )
    
    def get_pending_feedback(self, agent: str = None) -> list:
        """获取待处理的反馈"""
        state = self.get()
        pending = state["feedback"]["pending"]
        
        if agent:
            pending = [f for f in pending if f["to"] == agent]
        
        return pending
    
    def resolve_feedback(self, feedback_id: str, resolution: str, 
                         by: str = "system"):
        """解决反馈"""
        state = self.get()
        
        for i, feedback in enumerate(state["feedback"]["pending"]):
            if feedback["id"] == feedback_id:
                feedback["status"] = "resolved"
                feedback["resolved_at"] = datetime.now().isoformat()
                feedback["resolved_by"] = by
                feedback["resolution"] = resolution
                
                state["feedback"]["resolved"].append(feedback)
                state["feedback"]["pending"].pop(i)
                self._save_state(state)
                return True
        
        return False
    
    # ==================== 质量追踪 ====================
    
    def record_quality_score(self, stage: str, score: float, 
                              issues: list = None):
        """记录质量分数"""
        state = self.get()
        
        state["quality"]["stage_scores"][stage] = score
        
        if issues:
            state["quality"]["issues"].extend(issues)
        
        # 计算平均分
        scores = list(state["quality"]["stage_scores"].values())
        state["quality"]["avg_score"] = sum(scores) / len(scores)
        
        self._save_state(state)
    
    # ==================== 内部方法 ====================
    
    def _init_state(self) -> dict:
        """初始化状态"""
        state = deepcopy(self.STATE_SCHEMA)
        state["meta"]["created_at"] = datetime.now().isoformat()
        state["meta"]["updated_at"] = datetime.now().isoformat()
        state["project"]["name"] = self.project_name
        
        # 初始化智能体状态
        for agent in self.AGENTS:
            state["agents"][agent] = {
                "status": "idle",
                "last_run": None,
                "last_result": None,
                "output_summary": None,
                "error": None
            }
        
        self._save_state(state)
        return state
    
    def _load_state(self) -> dict:
        """加载状态"""
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return self._init_state()
    
    def _save_state(self, state: dict):
        """保存状态"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    
    def _save_history(self, state: dict):
        """保存历史版本"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        history_file = self.history_dir / f"state_{timestamp}.json"
        
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        
        # 只保留最近 50 个历史版本
        history_files = sorted(self.history_dir.glob("state_*.json"))
        if len(history_files) > 50:
            for old_file in history_files[:-50]:
                old_file.unlink()
    
    def _get_next_stage(self, current_phase: str, current_stage: str) -> tuple:
        """获取下一阶段"""
        if current_phase is None:
            return "plan", "requirement"
        
        phase_order = ["plan", "do", "check", "act"]
        stage_map = self.PHASE_MAP
        
        phase_idx = phase_order.index(current_phase)
        stages = stage_map[current_phase]
        stage_idx = stages.index(current_stage)
        
        if stage_idx + 1 < len(stages):
            return current_phase, stages[stage_idx + 1]
        elif phase_idx + 1 < len(phase_order):
            next_phase = phase_order[phase_idx + 1]
            return next_phase, stage_map[next_phase][0]
        else:
            # 循环完成
            state = self.get()
            state["workflow"]["cycle"] += 1
            self._save_state(state)
            return "plan", "requirement"
    
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
    
    # ==================== 状态摘要 ====================
    
    def get_summary(self) -> dict:
        """获取状态摘要"""
        state = self.get()
        
        return {
            "project": {
                "name": state["project"]["name"],
                "status": state["project"]["status"]
            },
            "workflow": {
                "cycle": state["workflow"]["cycle"],
                "current_phase": state["workflow"]["current_phase"],
                "current_stage": state["workflow"]["current_stage"],
                "paused": state["workflow"]["paused"],
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


# ==================== CLI 接口 ====================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="统一状态管理器")
    parser.add_argument("--project", "-p", required=True, help="项目名称")
    parser.add_argument("--status", "-s", action="store_true", help="查看状态")
    parser.add_argument("--summary", action="store_true", help="查看摘要")
    parser.add_argument("--reset", action="store_true", help="重置状态")
    parser.add_argument("--events", "-e", action="store_true", help="查看事件日志")
    parser.add_argument("--decisions", "-d", action="store_true", help="查看决策记录")
    parser.add_argument("--feedback", "-f", action="store_true", help="查看待处理反馈")
    
    args = parser.parse_args()
    
    sm = StateManager(project_name=args.project)
    
    if args.summary:
        print(json.dumps(sm.get_summary(), indent=2, ensure_ascii=False))
    elif args.reset:
        sm.reset()
        print("✅ 状态已重置")
    elif args.events:
        events = sm.get_events(limit=20)
        print(json.dumps(events, indent=2, ensure_ascii=False))
    elif args.decisions:
        decisions = sm.get_decisions()
        print(json.dumps(decisions, indent=2, ensure_ascii=False))
    elif args.feedback:
        feedback = sm.get_pending_feedback()
        print(json.dumps(feedback, indent=2, ensure_ascii=False))
    else:
        # 默认显示完整状态
        print(json.dumps(sm.get(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    exit(main())