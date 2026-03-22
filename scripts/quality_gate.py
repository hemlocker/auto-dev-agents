#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
质量门禁工具
Quality Gate Tool

检查各阶段输出是否达到质量标准，不达标则阻止进入下一阶段

使用方式：
  python3 scripts/quality_gate.py --project demo_project --stage requirement
  python3 scripts/quality_gate.py --project demo_project --all
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


class QualityGate:
    """质量门禁检查器"""
    
    def __init__(self, project_name: str, base_dir: str = None):
        self.project_name = project_name
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent
        self.project_dir = self.base_dir / "projects" / project_name
        self.output_dir = self.project_dir / "output"
        
        # 质量门禁配置
        self.gates = {
            "requirement": {
                "name": "需求阶段",
                "required_files": ["requirements/用户需求文档.md", "requirements/软件需求规格说明书.md"],
                "min_score": 90
            },
            "design": {
                "name": "设计阶段",
                "required_files": ["design/架构设计文档.md"],
                "min_score": 85
            },
            "development": {
                "name": "开发阶段",
                "required_files": ["src/backend/package.json", "src/frontend/package.json"],
                "min_score": 80
            },
            "testing": {
                "name": "测试阶段",
                "required_files": ["tests/测试报告.md"],
                "min_score": 80
            },
            "deployment": {
                "name": "部署阶段",
                "required_files": ["deploy/docker-compose.yml"],
                "min_score": 85
            },
            "operations": {
                "name": "运维阶段",
                "required_files": ["operations/README.md"],
                "min_score": 80
            },
            "monitor": {
                "name": "监控阶段",
                "required_files": ["monitor/quality-report-20260321.md"],
                "min_score": 80
            },
            "optimizer": {
                "name": "优化阶段",
                "required_files": ["optimizer/optimization-plan-20260321.md"],
                "min_score": 75
            }
        }
    
    def check_stage(self, stage: str) -> Dict:
        """检查指定阶段"""
        if stage not in self.gates:
            return {"stage": stage, "passed": False, "score": 0, "message": f"未知阶段"}
        
        gate = self.gates[stage]
        passed = 0
        total = len(gate["required_files"])
        details = []
        
        for file_path in gate["required_files"]:
            full_path = self.output_dir / file_path
            exists = full_path.exists()
            size = full_path.stat().st_size if exists else 0
            passed += 1 if exists and size > 100 else 0
            details.append({"file": file_path, "exists": exists, "size": size})
        
        score = int(passed / total * 100) if total > 0 else 0
        passed_gate = score >= gate["min_score"]
        
        return {
            "stage": stage,
            "stage_name": gate["name"],
            "passed": passed_gate,
            "score": score,
            "min_score": gate["min_score"],
            "details": details,
            "message": f"{'✅' if passed_gate else '❌'} {score}% (要求 {gate['min_score']}%)"
        }
    
    def check_all(self) -> Dict:
        """检查所有阶段"""
        stages = {}
        for stage in self.gates:
            stages[stage] = self.check_stage(stage)
        
        all_passed = all(s["passed"] for s in stages.values())
        avg_score = sum(s["score"] for s in stages.values()) / len(stages)
        
        return {
            "project": self.project_name,
            "check_time": datetime.now().isoformat(),
            "all_passed": all_passed,
            "average_score": round(avg_score, 1),
            "stages": stages
        }


def main():
    parser = argparse.ArgumentParser(description="质量门禁检查")
    parser.add_argument("--project", "-p", required=True, help="项目名称")
    parser.add_argument("--stage", "-s", help="检查指定阶段")
    parser.add_argument("--all", "-a", action="store_true", help="检查所有阶段")
    
    args = parser.parse_args()
    gate = QualityGate(project_name=args.project)
    
    if args.stage:
        result = gate.check_stage(args.stage)
    else:
        result = gate.check_all()
    
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    exit(main())