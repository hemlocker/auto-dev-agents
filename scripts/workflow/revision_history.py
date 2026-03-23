"""
修订历史管理 - 自动生成文档修订历史

所有输出文档必须包含修订历史表格，记录每次变更。

修订历史格式（Markdown）：
| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| v1.0 | 2026-03-23 | 系统 | 初始创建 |
| v1.1 | 2026-03-24 | 系统 | 新增导入导出功能 |
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict
from threading import Lock


@dataclass
class Revision:
    """修订记录"""
    version: str
    date: str
    author: str = "系统"
    changes: List[dict] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass 
class DocumentRevision:
    """文档修订历史"""
    document: str
    current_version: str
    created: str
    last_updated: str
    revisions: List[Revision] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d["revisions"] = [r.to_dict() for r in self.revisions]
        return d


class RevisionHistoryManager:
    """修订历史管理器"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.history_file = self.output_dir / "revision_history.json"
        self._lock = Lock()
        
        # 确保目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _load(self) -> dict:
        """加载修订历史"""
        if self.history_file.exists():
            try:
                return json.loads(self.history_file.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"⚠️ 加载修订历史失败: {e}")
        
        return {
            "project": "",
            "documents": {}
        }
    
    def _save(self, history: dict):
        """保存修订历史"""
        with self._lock:
            history["updated_at"] = datetime.now().isoformat()
            self.history_file.write_text(
                json.dumps(history, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
    
    # ========== 文档管理 ==========
    
    def register_document(self, document: str):
        """注册文档"""
        history = self._load()
        
        if document not in history["documents"]:
            history["documents"][document] = {
                "document": document,
                "current_version": None,
                "created": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "revisions": []
            }
            self._save(history)
    
    def add_revision(
        self,
        document: str,
        version: str,
        change_type: str,
        description: str,
        details: str = "",
        author: str = "系统"
    ):
        """添加修订记录
        
        Args:
            document: 文档名称
            version: 版本号
            change_type: 变更类型 (created/appended/updated/deprecated/removed)
            description: 变更说明
            details: 详细描述
            author: 作者
        """
        history = self._load()
        
        # 确保文档存在
        if document not in history["documents"]:
            self.register_document(document)
            history = self._load()
        
        doc = history["documents"][document]
        
        # 创建修订记录
        revision = {
            "version": version,
            "date": datetime.now().isoformat(),
            "author": author,
            "changes": [{
                "type": change_type,
                "description": description,
                "details": details
            }]
        }
        
        # 如果版本相同，合并变更
        existing = next(
            (r for r in doc["revisions"] if r["version"] == version),
            None
        )
        
        if existing:
            # 合并变更
            existing["changes"].append(revision["changes"][0])
        else:
            # 新增修订
            doc["revisions"].append(revision)
        
        # 更新版本信息
        doc["current_version"] = version
        doc["last_updated"] = datetime.now().isoformat()
        
        self._save(history)
    
    # ========== Markdown 生成 ==========
    
    def generate_revision_table(self, document: str) -> str:
        """生成修订历史 Markdown 表格"""
        history = self._load()
        
        if document not in history["documents"]:
            return ""
        
        doc = history["documents"][document]
        revisions = doc.get("revisions", [])
        
        if not revisions:
            return ""
        
        lines = [
            "## 修订历史",
            "",
            "| 版本 | 日期 | 作者 | 变更说明 |",
            "|------|------|------|----------|"
        ]
        
        for rev in revisions:
            date_str = rev["date"][:10]  # 只取日期
            changes_desc = "; ".join(
                c["description"] for c in rev.get("changes", [])
            )
            lines.append(
                f"| {rev['version']} | {date_str} | {rev['author']} | {changes_desc} |"
            )
        
        return "\n".join(lines)
    
    def generate_document_header(self, document: str, title: str) -> str:
        """生成文档头部（包含版本和修订历史）"""
        history = self._load()
        
        doc = history["documents"].get(document, {})
        current_version = doc.get("current_version", "")
        created = doc.get("created", "")[:10] if doc.get("created") else ""
        last_updated = doc.get("last_updated", "")[:10] if doc.get("last_updated") else ""
        
        header = f"""# {title}

**当前版本**: {current_version or '未设置'}
**创建日期**: {created}
**最后更新**: {last_updated}

---

{self.generate_revision_table(document)}

---

"""
        return header
    
    # ========== JSON 导出 ==========
    
    def get_document_history(self, document: str) -> Optional[dict]:
        """获取文档修订历史"""
        history = self._load()
        return history["documents"].get(document)
    
    def get_all_documents(self) -> List[str]:
        """获取所有文档列表"""
        history = self._load()
        return list(history.get("documents", {}).keys())
    
    def export_history_json(self) -> dict:
        """导出完整历史（JSON 格式）"""
        return self._load()
    
    # ========== 查询 ==========
    
    def get_version_changes(self, version: str) -> Dict[str, List[dict]]:
        """获取指定版本在所有文档的变更"""
        history = self._load()
        
        changes = {}
        for doc_name, doc in history.get("documents", {}).items():
            rev = next(
                (r for r in doc.get("revisions", []) if r["version"] == version),
                None
            )
            if rev:
                changes[doc_name] = rev.get("changes", [])
        
        return changes
    
    def print_history(self, document: str = None):
        """打印修订历史"""
        history = self._load()
        
        print("\n" + "=" * 60)
        print("📋 修订历史")
        print("=" * 60)
        
        if document:
            docs = {document: history["documents"].get(document, {})}
        else:
            docs = history.get("documents", {})
        
        for doc_name, doc in docs.items():
            print(f"\n📄 {doc_name}")
            print(f"   当前版本: {doc.get('current_version') or '无'}")
            print(f"   创建: {doc.get('created', '')[:10]}")
            
            if doc.get("revisions"):
                print("   修订记录:")
                for rev in doc["revisions"]:
                    date = rev["date"][:10]
                    for change in rev.get("changes", []):
                        print(f"     {rev['version']} ({date}): {change['description']}")
        
        print("\n" + "=" * 60)
    
    # ========== 重置 ==========
    
    def reset_document(self, document: str):
        """重置文档修订历史"""
        history = self._load()
        
        if document in history["documents"]:
            del history["documents"][document]
            self._save(history)
            print(f"✅ 已重置文档 {document} 的修订历史")
    
    def reset_all(self):
        """重置所有修订历史"""
        self._save({
            "project": "",
            "documents": {},
            "reset_at": datetime.now().isoformat()
        })
        print("✅ 已重置所有修订历史")


# ========== 变更类型常量 ==========

class ChangeType:
    """变更类型"""
    CREATED = "created"          # 创建
    APPENDED = "appended"        # 追加
    UPDATED = "updated"          # 更新
    DEPRECATED = "deprecated"    # 废弃
    REMOVED = "removed"          # 移除
    RESTRUCTURED = "restructured" # 重构