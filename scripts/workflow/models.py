# -*- coding: utf-8 -*-
"""
工作流数据模型
包含：数据类、异常、子任务定义
"""

import os
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field


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


# ==================== 子任务定义 ====================

STAGE_SUBTASKS = {
    "requirement": [
        {
            "name": "analyze_input",
            "description": "分析输入文件，提取需求点",
            "output_files": ["需求点清单.md"],
            "max_tokens_estimate": 5000
        },
        {
            "name": "user_requirements",
            "description": "生成用户需求文档",
            "depends_on": ["analyze_input"],
            "output_files": ["user_requirements.md"],
            "max_tokens_estimate": 8000
        },
        {
            "name": "software_requirements",
            "description": "生成软件需求规格",
            "depends_on": ["user_requirements"],
            "output_files": ["software_requirements.md"],
            "max_tokens_estimate": 10000
        },
        {
            "name": "rtm",
            "description": "生成需求追踪矩阵",
            "depends_on": ["software_requirements"],
            "output_files": ["rtm.json"],
            "max_tokens_estimate": 3000
        }
    ],
    
    "design": [
        {
            "name": "architecture",
            "description": "系统架构设计",
            "output_files": ["architecture_design.md"],
            "max_tokens_estimate": 8000
        },
        {
            "name": "data_model",
            "description": "数据模型设计",
            "depends_on": ["architecture"],
            "output_files": ["data_model.md"],
            "max_tokens_estimate": 6000
        },
        {
            "name": "api_design",
            "description": "API 接口设计",
            "depends_on": ["data_model"],
            "output_files": ["api_spec.md"],
            "max_tokens_estimate": 8000
        },
        {
            "name": "detailed_design",
            "description": "详细设计文档",
            "depends_on": ["api_design"],
            "output_files": ["detailed_design.md"],
            "max_tokens_estimate": 12000
        }
    ],
    
    "development": [
        {
            "name": "project_structure",
            "description": "创建项目结构和配置文件",
            "output_files": ["package.json", "requirements.txt", "*.config.*"],
            "max_tokens_estimate": 3000
        },
        {
            "name": "models",
            "description": "创建数据模型",
            "depends_on": ["project_structure"],
            "output_dir": "src/models/",
            "max_tokens_estimate": 8000
        },
        {
            "name": "repositories",
            "description": "创建数据访问层",
            "depends_on": ["models"],
            "output_dir": "src/repositories/",
            "max_tokens_estimate": 6000
        },
        {
            "name": "services",
            "description": "创建业务逻辑层",
            "depends_on": ["repositories"],
            "output_dir": "src/services/",
            "max_tokens_estimate": 10000
        },
        {
            "name": "controllers",
            "description": "创建控制器层",
            "depends_on": ["services"],
            "output_dir": "src/controllers/",
            "max_tokens_estimate": 8000
        },
        {
            "name": "frontend_components",
            "description": "创建前端组件",
            "depends_on": ["controllers"],
            "output_dir": "src/frontend/components/",
            "max_tokens_estimate": 10000
        },
        {
            "name": "frontend_pages",
            "description": "创建前端页面",
            "depends_on": ["frontend_components"],
            "output_dir": "src/frontend/pages/",
            "max_tokens_estimate": 10000
        }
    ],
    
    "testing": [
        {
            "name": "unit_tests",
            "description": "编写单元测试",
            "output_dir": "tests/unit/",
            "max_tokens_estimate": 10000
        },
        {
            "name": "integration_tests",
            "description": "编写集成测试",
            "depends_on": ["unit_tests"],
            "output_dir": "tests/integration/",
            "max_tokens_estimate": 8000
        },
        {
            "name": "test_report",
            "description": "生成测试报告",
            "depends_on": ["integration_tests"],
            "output_files": ["测试报告.md"],
            "max_tokens_estimate": 3000
        }
    ],
    
    "deployment": [
        {
            "name": "docker_config",
            "description": "创建 Docker 配置",
            "output_files": ["Dockerfile", "docker-compose.yml"],
            "max_tokens_estimate": 5000
        },
        {
            "name": "nginx_config",
            "description": "创建 Nginx 配置",
            "output_files": ["nginx.conf"],
            "max_tokens_estimate": 3000
        },
        {
            "name": "deploy_scripts",
            "description": "创建部署脚本",
            "depends_on": ["docker_config", "nginx_config"],
            "output_files": ["deploy.sh", "rollback.sh"],
            "max_tokens_estimate": 5000
        },
        {
            "name": "deploy_report",
            "description": "生成部署文档",
            "output_files": ["部署报告.md"],
            "max_tokens_estimate": 3000
        }
    ]
}