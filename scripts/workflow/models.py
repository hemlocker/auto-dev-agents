# -*- coding: utf-8 -*-
"""
工作流数据模型
包含：数据类、异常、子任务定义
"""

import os
from pathlib import Path
from typing import Optional, Dict, List
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

# 默认子任务模板（前后端分离项目）
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
            "description": "创建数据模型（entity、dto、vo、enums）",
            "depends_on": ["project_structure"],
            "output_dirs": [
                "backend/src/main/java/{package_path}entity/",
                "backend/src/main/java/{package_path}dto/",
                "backend/src/main/java/{package_path}vo/",
                "backend/src/main/java/{package_path}enums/"
            ],
            "excludes": ["repository", "repositories", "service", "services", "controller", "controllers"],
            "max_tokens_estimate": 8000
        },
        {
            "name": "repositories",
            "description": "创建数据访问层（Repository 接口）",
            "depends_on": ["models"],
            "output_dir": "backend/src/main/java/{package_path}repository/",
            "excludes": ["service", "services", "controller", "controllers"],
            "max_tokens_estimate": 6000
        },
        {
            "name": "services",
            "description": "创建业务逻辑层（Service 接口和实现）",
            "depends_on": ["repositories"],
            "output_dir": "backend/src/main/java/{package_path}service/",
            "excludes": ["controller", "controllers"],
            "max_tokens_estimate": 10000
        },
        {
            "name": "controllers",
            "description": "创建控制器层（Controller）",
            "depends_on": ["services"],
            "output_dir": "backend/src/main/java/{package_path}controller/",
            "max_tokens_estimate": 8000
        },
        {
            "name": "common",
            "description": "创建公共模块（config、exception、response、util）",
            "depends_on": ["controllers"],
            "output_dirs": [
                "backend/src/main/java/{package_path}config/",
                "backend/src/main/java/{package_path}exception/",
                "backend/src/main/java/{package_path}response/",
                "backend/src/main/java/{package_path}util/"
            ],
            "max_tokens_estimate": 6000
        },
        {
            "name": "frontend_api",
            "description": "创建前端 API 客户端",
            "depends_on": ["controllers"],
            "output_dir": "frontend/src/api/",
            "max_tokens_estimate": 5000
        },
        {
            "name": "frontend_components",
            "description": "创建前端组件",
            "depends_on": ["frontend_api"],
            "output_dir": "frontend/src/components/",
            "max_tokens_estimate": 8000
        },
        {
            "name": "frontend_views",
            "description": "创建前端页面",
            "depends_on": ["frontend_components"],
            "output_dir": "frontend/src/views/",
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


# ==================== 项目类型子任务模板 ====================

SUBTASK_TEMPLATES = {
    # 前后端分离项目（默认）
    "fullstack": None,  # 使用默认 STAGE_SUBTASKS
    
    # 纯后端项目
    "backend_only": {
        "development": [
            {"name": "project_structure", "description": "创建项目结构和配置文件"},
            {"name": "models", "description": "创建数据模型", "depends_on": ["project_structure"]},
            {"name": "repositories", "description": "创建数据访问层", "depends_on": ["models"]},
            {"name": "services", "description": "创建业务逻辑层", "depends_on": ["repositories"]},
            {"name": "controllers", "description": "创建控制器层", "depends_on": ["services"]},
            {"name": "cli", "description": "创建 CLI 入口", "depends_on": ["controllers"]}
        ]
    },
    
    # 纯前端项目
    "frontend_only": {
        "development": [
            {"name": "project_structure", "description": "创建项目结构和配置文件"},
            {"name": "components", "description": "创建 UI 组件"},
            {"name": "pages", "description": "创建页面", "depends_on": ["components"]},
            {"name": "api_client", "description": "创建 API 客户端"},
            {"name": "store", "description": "创建状态管理", "depends_on": ["api_client"]}
        ]
    },
    
    # Django 单体应用
    "django_monolith": {
        "development": [
            {"name": "project_structure", "description": "创建 Django 项目结构"},
            {"name": "models", "description": "创建数据模型"},
            {"name": "views", "description": "创建视图", "depends_on": ["models"]},
            {"name": "templates", "description": "创建模板", "depends_on": ["views"]},
            {"name": "forms", "description": "创建表单", "depends_on": ["models"]},
            {"name": "urls", "description": "配置路由", "depends_on": ["views"]}
        ]
    },
    
    # 微服务项目
    "microservices": {
        "development": [
            {"name": "project_structure", "description": "创建微服务项目结构"},
            {"name": "shared_models", "description": "创建共享数据模型"},
            {"name": "service_core", "description": "创建核心服务", "depends_on": ["shared_models"]},
            {"name": "api_gateway", "description": "创建 API 网关", "depends_on": ["service_core"]},
            {"name": "docker", "description": "创建 Docker 配置", "depends_on": ["service_core", "api_gateway"]}
        ]
    }
}


# ==================== 模块依赖推断规则 ====================

DEPENDENCY_INFERENCE_RULES = [
    # 规则1: 外键/关联关系
    {
        "name": "foreign_key",
        "patterns": [
            r"(\w+?)需要关联(\w+)",
            r"(\w+?)关联到(\w+)",
            r"(\w+?)属于(\w+)",
            r"(\w+?)的(\w+)",
        ],
        "dependency_type": "foreign_key",
        "extract": lambda m: (m.group(1), m.group(2))
    },
    
    # 规则2: 包含/组合关系
    {
        "name": "composition",
        "patterns": [
            r"(\w+?)包含(\w+)",
            r"(\w+?)有多个(\w+)",
            r"(\w+?)下的(\w+)",
        ],
        "dependency_type": "composition",
        "extract": lambda m: (m.group(1), m.group(2))
    },
    
    # 规则3: 操作/引用关系
    {
        "name": "reference",
        "patterns": [
            r"(\w+?)需要(\w+?)信息",
            r"(\w+?)调用(\w+)",
            r"(\w+?)使用(\w+)",
        ],
        "dependency_type": "reference",
        "extract": lambda m: (m.group(1), m.group(2))
    },
    
    # 规则4: 常见业务模式（自动依赖）
    {
        "name": "business_pattern",
        "module_patterns": {
            "order": {"auto_deps": ["user"], "reason": "订单通常需要用户"},
            "订单": {"auto_deps": ["user", "用户"], "reason": "订单需要用户信息"},
            "comment": {"auto_deps": ["user"], "reason": "评论需要用户"},
            "评论": {"auto_deps": ["user", "用户"], "reason": "评论需要用户"},
            "repair": {"auto_deps": ["user", "device"], "reason": "维修需要用户和设备"},
            "维修": {"auto_deps": ["user", "device", "用户", "设备"], "reason": "维修需要用户和设备"},
            "log": {"auto_deps": ["user"], "reason": "日志通常需要用户"},
            "日志": {"auto_deps": ["user", "用户"], "reason": "日志需要用户"},
        }
    }
]

# 常见模块名称映射（标准化）
MODULE_NAME_MAPPING = {
    "用户": "user",
    "设备": "device",
    "订单": "order",
    "评论": "comment",
    "维修": "repair",
    "日志": "log",
    "通知": "notification",
    "消息": "message",
    "配置": "config",
    "权限": "permission",
    "角色": "role",
}


class ModuleDependencyAnalyzer:
    """模块依赖分析器"""
    
    def __init__(self, rules: List[dict] = None):
        self.rules = rules or DEPENDENCY_INFERENCE_RULES
        self.name_mapping = MODULE_NAME_MAPPING
    
    def normalize_name(self, name: str) -> str:
        """标准化模块名称"""
        name = name.lower().strip()
        return self.name_mapping.get(name, name)
    
    def extract_modules(self, text: str) -> List[str]:
        """从文本中提取模块名称"""
        import re
        
        # 常见模块关键词
        module_keywords = list(self.name_mapping.keys()) + list(self.name_mapping.values())
        
        found = set()
        for keyword in module_keywords:
            if keyword in text:
                found.add(self.normalize_name(keyword))
        
        # 添加中文关键词的英文映射
        for cn, en in self.name_mapping.items():
            if cn in text:
                found.add(en)
        
        return list(found)
    
    def infer_dependencies(self, text: str, modules: List[str] = None) -> dict:
        """推断模块依赖关系
        
        Args:
            text: 需求文本
            modules: 已识别的模块列表（可选，不传则自动提取）
        
        Returns:
            dict: {module_name: {"dependencies": [...], "inferred_from": [...]}}
        """
        import re
        
        if modules is None:
            modules = self.extract_modules(text)
        
        dependencies = {m: {"dependencies": set(), "reasons": []} for m in modules}
        
        # 应用规则推断
        for rule in self.rules:
            if rule["name"] == "business_pattern":
                # 业务模式规则
                for module in modules:
                    if module in rule["module_patterns"]:
                        pattern = rule["module_patterns"][module]
                        for dep in pattern["auto_deps"]:
                            dep_normalized = self.normalize_name(dep)
                            if dep_normalized in modules and dep_normalized != module:
                                dependencies[module]["dependencies"].add(dep_normalized)
                                dependencies[module]["reasons"].append(pattern["reason"])
            else:
                # 模式匹配规则
                for pattern in rule["patterns"]:
                    for match in re.finditer(pattern, text):
                        try:
                            source, target = rule["extract"](match)
                            source = self.normalize_name(source)
                            target = self.normalize_name(target)
                            
                            if source in modules and target in modules:
                                dependencies[source]["dependencies"].add(target)
                                dependencies[source]["reasons"].append(
                                    f"{rule['name']}: {match.group(0)}"
                                )
                        except:
                            continue
        
        # 转换为列表
        for m in dependencies:
            dependencies[m]["dependencies"] = list(dependencies[m]["dependencies"])
        
        return dependencies
    
    def build_dependency_graph(self, modules_info: List[dict]) -> Dict[str, List[str]]:
        """构建依赖图
        
        Args:
            modules_info: [{"name": "user", "dependencies": []}, ...]
        
        Returns:
            dict: {module: [dep1, dep2, ...]}
        """
        graph = {}
        for module in modules_info:
            graph[module["name"]] = module.get("dependencies", [])
        return graph
    
    def topological_sort(self, graph: Dict[str, List[str]]) -> List[str]:
        """拓扑排序
        
        Returns:
            List[str]: 开发顺序（依赖在前）
        """
        visited = set()
        result = []
        
        def visit(node):
            if node in visited:
                return
            visited.add(node)
            for dep in graph.get(node, []):
                visit(dep)
            result.append(node)
        
        for node in graph:
            visit(node)
        
        return result
    
    def get_parallel_groups(self, graph: Dict[str, List[str]]) -> List[List[str]]:
        """获取可并行执行的模块组
        
        Returns:
            List[List[str]]: [[batch1_modules], [batch2_modules], ...]
        """
        groups = []
        remaining = set(graph.keys())
        completed = set()
        
        while remaining:
            # 找出所有依赖已满足的模块
            ready = []
            for node in list(remaining):
                deps = set(graph.get(node, []))
                if deps.issubset(completed):
                    ready.append(node)
            
            if not ready:
                # 循环依赖
                raise ValueError(f"检测到循环依赖: {remaining}")
            
            groups.append(sorted(ready))  # 排序保证可重复性
            for node in ready:
                remaining.remove(node)
                completed.add(node)
        
        return groups
    
    def analyze(self, text: str, modules: List[str] = None, 
                priorities: Dict[str, str] = None) -> dict:
        """完整分析：提取模块、推断依赖、计算开发顺序
        
        Args:
            text: 需求文本
            modules: 已识别的模块（可选）
            priorities: 模块优先级 {"user": "P0", ...}
        
        Returns:
            dict: 完整的分析结果
        """
        # 1. 提取/使用模块
        if modules is None:
            modules = self.extract_modules(text)
        
        # 2. 推断依赖
        deps = self.infer_dependencies(text, modules)
        
        # 3. 构建模块信息
        modules_info = []
        for m in modules:
            info = {
                "name": m,
                "dependencies": deps[m]["dependencies"],
                "inferred_from": deps[m]["reasons"],
                "priority": (priorities or {}).get(m, "P1")
            }
            modules_info.append(info)
        
        # 4. 构建依赖图
        graph = self.build_dependency_graph(modules_info)
        
        # 5. 计算开发顺序
        order = self.topological_sort(graph)
        parallel_groups = self.get_parallel_groups(graph)
        
        return {
            "modules": modules_info,
            "dependency_graph": graph,
            "development_order": order,
            "parallel_groups": parallel_groups,
            "analysis_summary": {
                "total_modules": len(modules),
                "total_batches": len(parallel_groups),
                "max_parallelism": max(len(g) for g in parallel_groups) if parallel_groups else 0
            }
        }


def get_subtasks_for_project(project_type: str = "fullstack", custom_subtasks: dict = None) -> dict:
    """根据项目类型获取子任务定义
    
    Args:
        project_type: 项目类型
            - fullstack: 前后端分离（默认）
            - backend_only: 纯后端
            - frontend_only: 纯前端
            - django_monolith: Django 单体
            - microservices: 微服务
            - custom: 自定义
        custom_subtasks: 自定义子任务定义（project_type="custom" 时使用）
    
    Returns:
        dict: 完整的子任务定义
    """
    if project_type == "custom" and custom_subtasks:
        return custom_subtasks
    
    if project_type in SUBTASK_TEMPLATES and SUBTASK_TEMPLATES[project_type]:
        # 合并默认子任务和项目类型特定子任务
        result = dict(STAGE_SUBTASKS)
        result.update(SUBTASK_TEMPLATES[project_type])
        return result
    
    return STAGE_SUBTASKS


def generate_development_subtasks(
    strategy: str,
    modules: List[dict] = None,
    project_type: str = "fullstack"
) -> List[dict]:
    """生成开发阶段的子任务
    
    Args:
        strategy: 拆分策略
            - module: 按功能模块拆分（垂直切片）
            - layer: 按技术层拆分（水平切片）
            - auto: 根据模块数量自动选择
        modules: 模块信息列表 [{"name": "user", "dependencies": [], ...}]
        project_type: 项目类型
    
    Returns:
        List[dict]: 子任务列表
    """
    
    # 自动策略：根据模块数量选择
    if strategy == "auto":
        module_count = len(modules) if modules else 0
        strategy = "layer" if module_count <= 2 else "module"
    
    if strategy == "layer":
        # 使用预定义的分层子任务
        subtasks = get_subtasks_for_project(project_type)
        return subtasks.get("development", [])
    
    elif strategy == "module":
        # 按功能模块拆分
        if not modules:
            # 没有模块信息，回退到分层
            subtasks = get_subtasks_for_project(project_type)
            return subtasks.get("development", [])
        
        # 构建依赖图并排序
        analyzer = ModuleDependencyAnalyzer()
        graph = analyzer.build_dependency_graph(modules)
        order = analyzer.topological_sort(graph)
        parallel_groups = analyzer.get_parallel_groups(graph)
        
        subtasks = [
            {
                "name": "shared_infra",
                "description": "公共基础设施（配置、工具类、基类）",
                "output_dir": "src/shared/",
                "output_files": ["__init__.py", "config.py", "utils.py", "base.py"],
                "max_tokens_estimate": 5000,
                "batch": 0
            }
        ]
        
        # 模块名映射到中文描述
        name_desc = {
            "user": "用户管理",
            "device": "设备管理",
            "order": "订单管理",
            "comment": "评论管理",
            "repair": "维修管理",
            "log": "日志管理",
            "notification": "通知管理",
            "message": "消息管理",
        }
        
        for batch_idx, batch_modules in enumerate(parallel_groups, start=1):
            for module_name in batch_modules:
                # 查找模块信息
                module_info = next((m for m in modules if m["name"] == module_name), {})
                desc = module_info.get("description") or name_desc.get(module_name, module_name)
                deps = module_info.get("dependencies", [])
                
                # 构建依赖列表（shared_infra + 前置模块）
                task_deps = ["shared_infra"] + [f"{d}_module" for d in deps]
                
                subtasks.append({
                    "name": f"{module_name}_module",
                    "description": f"{desc}模块完整实现",
                    "module": module_name,
                    "output_dir": f"src/{module_name}/",
                    "includes": ["models", "services", "controllers", "schemas"],
                    "max_tokens_estimate": 12000,
                    "depends_on": task_deps,
                    "batch": batch_idx
                })
        
        return subtasks
    
    # 未知策略，回退到分层
    subtasks = get_subtasks_for_project(project_type)
    return subtasks.get("development", [])