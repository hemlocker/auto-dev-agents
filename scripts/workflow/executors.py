# -*- coding: utf-8 -*-
"""
工作流执行器
包含：HTTP辅助函数、SubagentExecutor、InputAnalyzer、SubtaskExecutor
"""

import os
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Iterator

from .models import StageConfig, STAGE_SUBTASKS, get_subtasks_for_project, generate_development_subtasks


# ==================== Gateway 配置 ====================

GATEWAY_URL = "http://127.0.0.1:18799"
GATEWAY_TOKEN = os.environ.get("OPENCLAW_GATEWAY_TOKEN", None)


def _load_gateway_token() -> Optional[str]:
    """从 OpenClaw 配置文件读取 Gateway token"""
    config_path = Path.home() / ".openclaw" / "openclaw.json"
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                auth = config.get("gateway", {}).get("auth", {})
                if auth.get("mode") == "token":
                    return auth.get("token")
        except (json.JSONDecodeError, IOError, OSError):
            pass
    return None


# 自动加载 Gateway token
if not GATEWAY_TOKEN:
    GATEWAY_TOKEN = _load_gateway_token()


# ==================== HTTP 辅助函数 ====================

# 延迟导入 requests，如果不可用则使用 subprocess + curl
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def http_post(url: str, headers: dict, payload: dict, timeout: int = 30) -> dict:
    """发送 HTTP POST 请求（优先使用 requests，否则使用 curl）"""
    if HAS_REQUESTS:
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            return {
                "status_code": response.status_code, 
                "text": response.text, 
                "json": response.json() if response.text else None
            }
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
                ["curl", "-s", "-X", "POST", url] + header_args + 
                ["-d", f"@{payload_file}", "--connect-timeout", str(timeout)],
                capture_output=True, text=True, timeout=timeout + 5
            )
            response_text = result.stdout
            try:
                return {"status_code": 200, "text": response_text, "json": json.loads(response_text) if response_text else None}
            except (json.JSONDecodeError, ValueError):
                return {"status_code": 500, "text": response_text}
        except Exception as e:
            return {"error": str(e)}
        finally:
            os.unlink(payload_file)


# ==================== SubagentExecutor ====================

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

        payload = {"tool": "subagents", "args": {"action": "list"}}

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
            if data.get("ok"):
                details = data.get("result", {}).get("details", {})
                if not details:
                    details = data.get("result", {})
                
                for sub in details.get("active", []):
                    if sub.get("sessionKey") == session_key:
                        return {"running": True, "info": sub}
                for sub in details.get("recent", []):
                    if sub.get("sessionKey") == session_key:
                        return {"running": False, "info": sub}
            return {"running": False, "info": None}
        return {"running": False, "error": result.get("text", "Unknown error")}


# ==================== InputAnalyzer ====================

class InputAnalyzer:
    """输入分析器 - 检查大小并决定处理策略"""
    
    # 中文约 1~2 字符/token，英文/代码约 4~5 字符/token
    
    def analyze(self) -> dict:
        """分析输入目录（按文件内容类型精确估算 token）"""
        files = list(self._scan_files())
        total_size = sum(f["size"] for f in files)

        # 逐文件按内容类型精确估算 token
        total_tokens = 0
        for f in files:
            file_path = Path(f["path"])
            try:
                # 小文件直接读取内容估算，中大文件按字节估算
                if f["size"] < 1024 * 1024:  # < 1MB 读内容
                    text = file_path.read_text(encoding="utf-8", errors="replace")
                    tokens = self._estimate_tokens(f["size"], path=file_path, text=text)
                else:
                    # 大文件只读前 2MB 做采样估算
                    with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
                        text = fh.read(2 * 1024 * 1024)
                    tokens = self._estimate_tokens(f["size"], path=file_path, text=text)
            except OSError:
                tokens = self._estimate_tokens(f["size"])
            total_tokens += tokens

        needs_batch = total_tokens > self.max_tokens or len(files) > self.max_files

        return {
            "file_count": len(files),
            "total_size_kb": round(total_size / 1024, 2),
            "estimated_tokens": total_tokens,
            "max_tokens": self.max_tokens,
            "needs_batch": needs_batch,
            "reason": self._get_batch_reason(files, total_tokens),
            "files": files
        }
    
    def _scan_files(self) -> Iterator[dict]:
        """扫描输入文件"""
        if not self.input_dir.exists():
            return
        for f in self.input_dir.rglob("*"):
            if f.is_file() and f.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                yield {
                    "path": str(f),
                    "size": f.stat().st_size,
                    "relative": str(f.relative_to(self.input_dir))
                }
    
    SUPPORTED_EXTENSIONS = {".md", ".txt", ".json", ".yaml", ".yml",
                             ".py", ".js", ".ts", ".java", ".go", ".rs", ".c", ".cpp",
                             ".h", ".cs", ".rb", ".php", ".swift", ".kt",
                             ".sql", ".sh", ".vue", ".jsx", ".tsx", ".html", ".css",
                             ".xml", ".toml", ".ini", ".rst", ".adoc", ".log"}

    # 逐文件按内容类型估算的 ratio
    _RATIO_CJK = 1.8       # 中文：~1.8 chars/token
    _RATIO_LATIN = 4.0     # 英文/纯文本：~4 chars/token
    _RATIO_CODE = 3.5      # 代码：~3.5 chars/token
    _RATIO_MIXED = 2.5     # 中英混合：~2.5 chars/token

    _EXT_CODE = {
        ".py", ".js", ".ts", ".java", ".go", ".rs", ".c", ".cpp",
        ".h", ".hpp", ".cs", ".rb", ".php", ".swift", ".kt",
        ".sql", ".sh", ".bash", ".ps1", ".bat", ".yaml", ".yml",
        ".json", ".xml", ".toml", ".ini", ".cfg", ".conf",
        ".vue", ".jsx", ".tsx", ".svelte", ".html", ".css",
        ".scss", ".sass", ".less", ".md",
    }
    _EXT_ENGLISH = {".txt", ".log", ".rst", ".adoc"}

    def _is_cjk_char(self, ch: str) -> bool:
        cp = ord(ch)
        # CJK 统一表意文字、扩展区、日韩兼容区
        return (0x4E00 <= cp <= 0x9FFF or
                0x3400 <= cp <= 0x4DBF or
                0x20000 <= cp <= 0x2A6DF or
                0x2A700 <= cp <= 0x2B73F or
                0x2B740 <= cp <= 0x2B81F or
                0x3000 <= cp <= 0x303F or   # CJK 符号
                0xFF00 <= cp <= 0xFFEF)    # 全角字符

    def _detect_content_type(self, path: Path, text: str) -> str:
        """检测内容类型: 'code' | 'cjk' | 'latin' | 'mixed'"""
        ext = path.suffix.lower()

        # 代码类文件优先按代码估算
        if ext in self._EXT_CODE:
            return "code"

        # 纯文本文件
        if ext in self._EXT_ENGLISH:
            return "latin"

        # 扫描字符做统计
        cjk_count = 0
        latin_count = 0
        sample = text[: 1024 * 1024]  # 只采样前 1MB
        for ch in sample:
            if ch.isalpha():
                if self._is_cjk_char(ch):
                    cjk_count += 1
                else:
                    latin_count += 1

        total_chars = cjk_count + latin_count
        if total_chars == 0:
            return "code"  # 空文件或纯符号

        cjk_ratio = cjk_count / total_chars

        if cjk_ratio > 0.15:
            return "cjk"
        elif cjk_ratio > 0.02:
            return "mixed"
        else:
            return "latin"

    def _estimate_tokens(self, size_bytes: int, path: Path = None, text: str = None) -> int:
        """
        估算 token 数量（基于文件内容字符分布）
        - 代码/英文密集型：~3.5-5 chars/token
        - 中文密集型：~1.5-2 chars/token
        - 中英混合：~2-3 chars/token
        """
        # 如果提供了路径和文本内容，精确估算
        if path is not None and text is not None:
            content_type = self._detect_content_type(path, text)
            if content_type == "cjk":
                return int(len(text) / self._RATIO_CJK)
            elif content_type == "latin":
                return int(len(text) / self._RATIO_LATIN)
            elif content_type == "mixed":
                return int(len(text) / self._RATIO_MIXED)
            else:  # code
                return int(len(text) / self._RATIO_CODE)

        # 仅提供大小时，用分段假设估算
        # 小文件按实际字节，中等/大文件按代码类型
        if size_bytes < 50 * 1024:  # < 50KB，精确估算
            return size_bytes // 2
        elif size_bytes < 1024 * 1024:  # 50KB - 1MB，混合估算
            return int(size_bytes / self._RATIO_MIXED)
        else:  # > 1MB，按代码类型（通常压缩率高）
            return int(size_bytes / self._RATIO_CODE)
    
    def _get_batch_reason(self, files: list, total_tokens: int) -> str:
        """获取需要分批的原因"""
        reasons = []
        if total_tokens > self.max_tokens:
            reasons.append(f"预估 {total_tokens} tokens 超过限制 {self.max_tokens}")
        if len(files) > self.max_files:
            reasons.append(f"文件数 {len(files)} 超过限制 {self.max_files}")
        return "; ".join(reasons) if reasons else "无需分批"
    
    def generate_batch_plan(self, analysis: dict) -> List[dict]:
        """生成分批计划"""
        if not analysis["needs_batch"]:
            return [{"batch": 1, "files": analysis["files"], "total_batches": 1, "is_full": True}]
        
        files = analysis["files"]
        files_sorted = sorted(files, key=lambda x: x["size"], reverse=True)
        
        batches = []
        for i in range(0, len(files_sorted), self.batch_size):
            batch_files = files_sorted[i:i + self.batch_size]
            batches.append({
                "batch": i // self.batch_size + 1,
                "files": batch_files,
                "total_batches": (len(files_sorted) + self.batch_size - 1) // self.batch_size,
                "is_full": False
            })
        
        return batches


# ==================== SubtaskExecutor ====================

class SubtaskExecutor:
    """子任务执行器 - 处理任务拆分和增量执行"""
    
    def __init__(self, stage: str, output_dir: Path, base_dir: Path, 
                 project_type: str = "fullstack",
                 subtask_strategy: str = "layer",
                 modules: List[dict] = None,
                 project_meta: dict = None,
                 custom_subtasks: dict = None):
        self.stage = stage
        self.output_dir = output_dir
        self.base_dir = base_dir
        self.project_type = project_type
        self.subtask_strategy = subtask_strategy
        self.modules = modules or []
        self.project_meta = project_meta or {}
        
        # 根据策略获取子任务定义
        if stage == "development" and subtask_strategy in ["module", "auto"]:
            # development 阶段支持模块拆分
            self.subtasks = generate_development_subtasks(
                strategy=subtask_strategy,
                modules=modules,
                project_type=project_type
            )
        else:
            # 其他阶段使用预定义子任务
            all_subtasks = get_subtasks_for_project(project_type, custom_subtasks)
            self.subtasks = all_subtasks.get(stage, [])
        
        self.completed = set()
        self.results = {}
    
    def has_subtasks(self) -> bool:
        """是否有子任务定义"""
        return len(self.subtasks) > 0
    
    def get_execution_plan(self) -> List[dict]:
        """获取执行计划（拓扑排序）"""
        if not self.subtasks:
            return []
        
        ordered = []
        remaining = list(self.subtasks)
        temp_completed = set()
        
        while remaining:
            for subtask in remaining[:]:
                deps = subtask.get("depends_on", [])
                if all(d in temp_completed for d in deps):
                    ordered.append(subtask)
                    remaining.remove(subtask)
                    temp_completed.add(subtask["name"])
        
        return ordered
    
    # 子任务输出排除规则（防止越界输出）
    SUBTASK_EXCLUSIONS = {
        "models": {
            "exclude_dirs": ["repository", "repositories", "service", "services", "controller", "controllers"],
            "exclude_files": ["*Repository*.java", "*Service*.java", "*Controller*.java"],
            "message": "⚠️ 只输出数据模型相关代码（entity/dto/vo/enums），不要输出 repository/service/controller"
        },
        "repositories": {
            "exclude_dirs": ["service", "services", "controller", "controllers"],
            "exclude_files": ["*Service*.java", "*Controller*.java"],
            "message": "⚠️ 只输出数据访问层代码（Repository 接口和实现），不要输出 service/controller"
        },
        "services": {
            "exclude_dirs": ["controller", "controllers"],
            "exclude_files": ["*Controller*.java"],
            "message": "⚠️ 只输出业务逻辑层代码（Service 接口和实现），不要输出 controller"
        }
    }
    
    def generate_subtask_prompt(self, subtask: dict, context: dict) -> str:
        """生成子任务提示词（包含增量输出和边界限制）"""
        base_prompt = self._load_stage_prompt()
        
        # 动态变量替换
        subtask = self._replace_variables(subtask)
        
        # 构建上下文信息：包含已完成的子任务输出
        context_info = ""
        if subtask.get("depends_on"):
            context_info += "\n## 已完成的子任务输出\n"
            context_info += "请先读取以下已生成的文件，作为本次任务的输入：\n\n"
            
            for dep in subtask["depends_on"]:
                if dep in self.results:
                    dep_result = self.results[dep]
                    if dep_result.get("output_files"):
                        for f in dep_result["output_files"]:
                            context_info += f"- {f}\n"
                    elif dep_result.get("output_dir"):
                        context_info += f"- {dep_result['output_dir']}\n"
                    if dep_result.get("summary"):
                        context_info += f"  （{dep_result['summary']}）\n"
        
        # 输出限制 - 支持多种格式
        output_limit = ""
        
        # 优先使用 output_dirs（多个目录）
        if subtask.get("output_dirs"):
            dirs = subtask["output_dirs"]
            output_limit = f"\n## 本次输出目录\n只输出到以下目录:\n"
            for d in dirs:
                output_limit += f"- {d}\n"
        # 其次使用 output_dir（单个目录）
        elif subtask.get("output_dir"):
            output_limit = f"\n## 本次输出目录\n只输出到: {subtask['output_dir']}"
        # 最后使用 output_files（指定文件）
        elif subtask.get("output_files"):
            output_limit = f"\n## 本次输出文件\n只需输出以下文件: {', '.join(subtask['output_files'])}"
        
        # 排除规则 - 优先从子任务定义读取，否则使用默认规则
        exclusion_info = ""
        subtask_name = subtask.get("name", "")
        
        # 从子任务定义中读取排除规则
        excludes = subtask.get("excludes", [])
        if excludes:
            exclusion_info = f"\n## ⚠️ 输出边界限制\n"
            exclusion_info += f"不要输出以下类型的代码或目录:\n"
            for exc in excludes:
                exclusion_info += f"- ❌ {exc}/\n"
        # 或使用默认规则
        elif subtask_name in self.SUBTASK_EXCLUSIONS:
            rules = self.SUBTASK_EXCLUSIONS[subtask_name]
            exclusion_info = f"\n## ⚠️ 输出边界限制\n{rules['message']}\n"
            if rules.get("exclude_dirs"):
                exclusion_info += f"- 不要创建以下目录: {', '.join(rules['exclude_dirs'])}\n"
            if rules.get("exclude_files"):
                exclusion_info += f"- 不要输出以下类型文件: {', '.join(rules['exclude_files'])}\n"
        
        # 计算实际的输出根目录
        output_root = self.output_dir
        if subtask.get("output_dirs"):
            # 多个目录时，输出根目录是项目根目录
            output_root = self.output_dir.parent.parent  # 从 output/src 回到项目根
        
        # 添加项目元信息
        meta_info = ""
        if self.project_meta:
            meta_info = f"\n## 项目信息\n"
            if self.project_meta.get("package_name"):
                meta_info += f"- 包名: {self.project_meta['package_name']}\n"
            if self.project_meta.get("project_name"):
                meta_info += f"- 项目名称: {self.project_meta['project_name']}\n"
        
        return f"""# 子任务: {subtask['name']}

## 阶段: {self.stage}
{meta_info}
## 系统提示词
{base_prompt[:2000]}

## 任务描述
{subtask['description']}
{context_info}
{output_limit}
{exclusion_info}
## 输出根目录
{output_root}

## 增量执行要求
1. **读取前置输出**: 先读取依赖子任务生成的文件
2. **只输出本次内容**: 不要重复输出已有文件
3. **严格遵守边界**: 只输出本子任务负责的内容，不要越界输出其他层的代码
4. **完成标记**: 输出完成后添加 [SUBTASK_COMPLETE: {subtask['name']}]
5. **问题标记**: 如有问题添加 [SUBTASK_QUESTION: 问题描述]
"""
    
    def _replace_variables(self, subtask: dict) -> dict:
        """替换子任务中的动态变量
        
        支持的变量：
        - {package_path}: 包名路径，如 com/example/device/
        - {package_name}: 包名，如 com.example.device
        - {project_name}: 项目名称
        """
        import copy
        subtask = copy.deepcopy(subtask)
        
        # 获取变量值（确保不为 None）
        package_path = self.project_meta.get("package_path") or "com/example/app/"
        package_name = self.project_meta.get("package_name") or "com.example.app"
        project_name = self.project_meta.get("project_name") or "my-project"
        
        # 替换函数
        def replace(s):
            if isinstance(s, str):
                return s.replace("{package_path}", package_path) \
                        .replace("{package_name}", package_name) \
                        .replace("{project_name}", project_name)
            return s
        
        # 替换所有字符串字段
        for key in ["output_dir", "description"]:
            if subtask.get(key):
                subtask[key] = replace(subtask[key])
        
        # 替换 output_dirs 列表
        if subtask.get("output_dirs"):
            subtask["output_dirs"] = [replace(d) for d in subtask["output_dirs"]]
        
        return subtask
    
    def _load_stage_prompt(self) -> str:
        """加载阶段提示词（包含知识库）"""
        # 1. 加载提示词（指令）
        prompt_path = self.base_dir / "prompts" / self.stage / "system.md"
        if prompt_path.exists():
            prompt = prompt_path.read_text(encoding="utf-8")
        else:
            prompt = f"你是 {self.stage} 智能体，请完成你的任务。"
        
        # 2. 加载知识库（参考）
        knowledge_parts = []
        knowledge_dir = self.base_dir / "knowledge" / "agents" / self.stage
        
        # 加载编码规范
        guidelines_path = knowledge_dir / "guidelines.md"
        if guidelines_path.exists():
            guidelines = guidelines_path.read_text(encoding="utf-8")
            # 只取前 5000 字符，避免过长
            if len(guidelines) > 5000:
                guidelines = guidelines[:5000] + "\n\n... (内容已截断，请参考完整文件)"
            knowledge_parts.append(f"## 编码规范\n\n{guidelines}")
        
        # 加载代码模板
        templates_path = knowledge_dir / "templates.md"
        if templates_path.exists():
            templates = templates_path.read_text(encoding="utf-8")
            if len(templates) > 8000:
                templates = templates[:8000] + "\n\n... (内容已截断，请参考完整文件)"
            knowledge_parts.append(f"## 代码模板\n\n{templates}")
        
        # 加载最佳实践
        best_practices_path = knowledge_dir / "best-practices.md"
        if best_practices_path.exists():
            best_practices = best_practices_path.read_text(encoding="utf-8")
            if len(best_practices) > 5000:
                best_practices = best_practices[:5000] + "\n\n... (内容已截断，请参考完整文件)"
            knowledge_parts.append(f"## 最佳实践\n\n{best_practices}")
        
        # 合并提示词和知识库
        if knowledge_parts:
            knowledge_text = "\n\n---\n\n".join(knowledge_parts)
            return f"{prompt}\n\n# 知识库参考\n\n{knowledge_text}"
        
        return prompt
    
    def record_result(self, subtask_name: str, result: dict):
        """记录子任务结果（包含输出文件信息）"""
        self.results[subtask_name] = result
        self.completed.add(subtask_name)
    
    def get_summary(self) -> dict:
        """获取执行摘要"""
        return {
            "stage": self.stage,
            "total_subtasks": len(self.subtasks),
            "completed_subtasks": len(self.completed),
            "results": self.results
        }