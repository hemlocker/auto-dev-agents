"""
版本化输出生成 - 所有输出文件带版本信息和修订历史

输出规范：
1. 所有文档必须有版本信息（当前版本、创建日期、最后更新）
2. 所有文档必须有修订历史表格
3. 结构化数据存储在 JSON 文件中
4. Markdown 文档是渲染输出
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from .revision_history import RevisionHistoryManager, ChangeType


class VersionedOutputGenerator:
    """版本化输出生成器"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.revision_manager = RevisionHistoryManager(self.output_dir)
        
        # 输出文件路径
        self.requirements_json = self.output_dir / "requirements.json"
        self.user_requirements_md = self.output_dir / "user_requirements.md"
        self.software_requirements_md = self.output_dir / "software_requirements.md"
        self.rtm_json = self.output_dir / "rtm.json"
    
    # ========== requirements.json 管理 ==========
    
    def load_requirements(self) -> dict:
        """加载现有需求"""
        if self.requirements_json.exists():
            try:
                return json.loads(self.requirements_json.read_text(encoding="utf-8"))
            except Exception:
                pass
        
        return {
            "schema": "requirements-v1",
            "project": "",
            "last_version": None,
            "requirements": [],
            "by_version": {}
        }
    
    def save_requirements(self, data: dict):
        """保存需求"""
        data["updated_at"] = datetime.now().isoformat()
        self.requirements_json.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
    
    def append_requirements(self, new_requirements: List[dict], version: str):
        """追加需求（增量）"""
        data = self.load_requirements()
        
        # 获取现有 ID
        existing_ids = {r["id"] for r in data["requirements"]}
        
        # 过滤：只添加新需求
        added = []
        for req in new_requirements:
            if req["id"] not in existing_ids:
                data["requirements"].append(req)
                added.append(req)
                existing_ids.add(req["id"])
        
        # 更新版本索引
        if version not in data["by_version"]:
            data["by_version"][version] = []
        
        data["by_version"][version].extend([r["id"] for r in added])
        data["last_version"] = version
        
        # 保存
        self.save_requirements(data)
        
        return added
    
    # ========== Markdown 文档生成 ==========
    
    def generate_user_requirements(self, version: str, requirements: List[dict]) -> str:
        """生成用户需求文档
        
        Args:
            version: 当前版本
            requirements: 所有需求（包括历史）
        
        Returns:
            Markdown 文档内容
        """
        # 文档头部
        content = f"""# 用户需求文档 (URD)

**当前版本**: {version}
**创建日期**: {datetime.now().strftime("%Y-%m-%d")}
**最后更新**: {datetime.now().strftime("%Y-%m-%d")}

---

{self.revision_manager.generate_revision_table("user_requirements.md")}

---

## 目录

1. 项目背景
2. 用户需求列表
3. 业务流程
4. 验收标准
5. 需求追溯矩阵

---

## 1. 项目背景

（从需求中提取或需要补充）

---

## 2. 用户需求列表

"""
        
        # 按版本分组
        by_version: Dict[str, List[dict]] = {}
        for req in requirements:
            v = req.get("version", "unknown")
            if v not in by_version:
                by_version[v] = []
            by_version[v].append(req)
        
        # 按版本顺序输出
        sorted_versions = sorted(by_version.keys(), key=self._version_sort_key)
        
        for v in sorted_versions:
            reqs = by_version[v]
            content += f"\n### {v} ({len(reqs)} 项需求)\n\n"
            
            for req in reqs:
                if req.get("status") == "deprecated":
                    continue
                
                content += f"""#### {req['id']}: {req['title']}

**优先级**: {req.get('priority', 'Should')} | **状态**: {req.get('status', 'active')}

{req.get('description', '无描述')}

"""
                
                # 验收标准
                if req.get('acceptance_criteria'):
                    content += "**验收标准**:\n"
                    for ac in req['acceptance_criteria']:
                        content += f"- {ac}\n"
                    content += "\n"
                
                content += "---\n\n"
        
        return content
    
    def generate_software_requirements(self, version: str, requirements: List[dict]) -> str:
        """生成软件需求规格文档"""
        content = f"""# 软件需求规格说明书 (SRS)

**当前版本**: {version}
**创建日期**: {datetime.now().strftime("%Y-%m-%d")}
**最后更新**: {datetime.now().strftime("%Y-%m-%d")}

---

{self.revision_manager.generate_revision_table("software_requirements.md")}

---

## 1. 引言

### 1.1 目的

本文档详细描述系统的功能需求和非功能需求。

### 1.2 范围

（从需求中提取）

---

## 2. 功能需求

"""
        
        # 功能需求
        functional = [r for r in requirements if r.get('type') == 'functional' and r.get('status') == 'active']
        
        for req in functional:
            content += f"""### {req['id']}: {req['title']}

**版本**: {req.get('version', '')}
**优先级**: {req.get('priority', 'Should')}

{req.get('description', '')}

"""
            if req.get('acceptance_criteria'):
                content += "**验收标准**:\n"
                for ac in req['acceptance_criteria']:
                    content += f"- {ac}\n"
                content += "\n"
        
        # 非功能需求
        non_functional = [r for r in requirements if r.get('type') == 'non-functional' and r.get('status') == 'active']
        
        if non_functional:
            content += "\n## 3. 非功能需求\n\n"
            
            for req in non_functional:
                content += f"""### {req['id']}: {req['title']}

**版本**: {req.get('version', '')}

{req.get('description', '')}

"""
        
        return content
    
    # ========== 文档写入 ==========
    
    def write_document(self, document: str, content: str, version: str, change_type: str, description: str):
        """写入文档并记录修订历史"""
        
        # 确定文件路径
        if document == "user_requirements.md":
            file_path = self.user_requirements_md
        elif document == "software_requirements.md":
            file_path = self.software_requirements_md
        else:
            file_path = self.output_dir / document
        
        # 写入文件
        file_path.write_text(content, encoding="utf-8")
        
        # 记录修订历史
        self.revision_manager.add_revision(
            document=document,
            version=version,
            change_type=change_type,
            description=description
        )
        
        print(f"✅ 已写入文档: {document} (v{version})")
    
    def append_to_document(self, document: str, new_content: str, version: str, description: str):
        """追加内容到文档"""
        
        file_path = self.output_dir / document
        
        # 读取现有内容
        existing = ""
        if file_path.exists():
            existing = file_path.read_text(encoding="utf-8")
        
        # 在修订历史之后插入新内容
        # 找到修订历史结束位置
        marker = "---\n\n##"
        
        if marker in existing:
            # 在第一个 ## 之前插入
            parts = existing.split(marker, 1)
            updated = parts[0] + marker + "\n\n" + new_content + "\n\n" + parts[1]
        else:
            # 追加到末尾
            updated = existing + "\n\n" + new_content
        
        # 写入
        file_path.write_text(updated, encoding="utf-8")
        
        # 记录修订历史
        self.revision_manager.add_revision(
            document=document,
            version=version,
            change_type=ChangeType.APPENDED,
            description=description
        )
        
        print(f"✅ 已追加到文档: {document} (v{version})")
    
    # ========== 辅助方法 ==========
    
    @staticmethod
    def _version_sort_key(version: str) -> tuple:
        """版本号排序键"""
        if not version.startswith('v'):
            return (0, 0)
        
        try:
            parts = version[1:].split('.')
            return (int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)
        except (ValueError, IndexError):
            return (0, 0)
    
    def get_output_files(self) -> List[Path]:
        """获取所有输出文件"""
        return [
            self.requirements_json,
            self.user_requirements_md,
            self.software_requirements_md,
            self.rtm_json
        ]
    
    def get_current_versions(self) -> Dict[str, str]:
        """获取各文档当前版本"""
        versions = {}
        
        for doc in ["user_requirements.md", "software_requirements.md", "rtm.json"]:
            history = self.revision_manager.get_document_history(doc)
            if history:
                versions[doc] = history.get("current_version", "")
        
        return versions