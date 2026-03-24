"""
版本清单管理 - 跟踪已处理的版本

manifest.json 结构：
{
    "project": "project-name",
    "last_processed_version": "v1.2",
    "processed_versions": ["v1.0", "v1.1", "v1.2"],
    "versions": {
        "v1.0": {
            "processed_at": "2026-03-23T10:00:00",
            "input_files": [...],
            "requirements_added": 10,
            "output_changes": {...}
        },
        ...
    }
}
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from threading import Lock


from .revision_history import version_sort_key


logger = logging.getLogger(__name__)


class ManifestManager:
    """版本清单管理器"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.manifest_file = self.project_dir / "output" / "manifest.json"
        self._lock = Lock()
        
        # 确保目录存在
        self.manifest_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _load(self) -> dict:
        """加载清单"""
        if self.manifest_file.exists():
            try:
                return json.loads(self.manifest_file.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning("加载 manifest 失败: %s", e)
        
        return {
            "project": self.project_dir.name,
            "last_processed_version": None,
            "processed_versions": [],
            "versions": {}
        }
    
    def _save(self, manifest: dict):
        """保存清单"""
        with self._lock:
            manifest["updated_at"] = datetime.now().isoformat()
            self.manifest_file.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
    
    # ========== 版本查询 ==========
    
    def get_processed_versions(self) -> List[str]:
        """获取已处理的版本列表"""
        manifest = self._load()
        return manifest.get("processed_versions", [])
    
    def get_last_processed_version(self) -> Optional[str]:
        """获取最后处理的版本"""
        manifest = self._load()
        return manifest.get("last_processed_version")
    
    def is_version_processed(self, version: str) -> bool:
        """检查版本是否已处理"""
        return version in self.get_processed_versions()
    
    def get_version_info(self, version: str) -> Optional[dict]:
        """获取版本详情"""
        manifest = self._load()
        return manifest.get("versions", {}).get(version)
    
    # ========== 版本记录 ==========
    
    def record_version_processed(
        self, 
        version: str,
        input_files: List[str] = None,
        requirements_added: int = 0,
        output_changes: Dict = None
    ):
        """记录版本已处理"""
        manifest = self._load()
        
        # 更新版本列表
        if version not in manifest["processed_versions"]:
            manifest["processed_versions"].append(version)
            # 排序
            manifest["processed_versions"].sort(key=version_sort_key)
        
        # 更新最后处理版本
        manifest["last_processed_version"] = version
        
        # 记录版本详情
        manifest["versions"][version] = {
            "processed_at": datetime.now().isoformat(),
            "input_files": input_files or [],
            "requirements_added": requirements_added,
            "output_changes": output_changes or {}
        }
        
        self._save(manifest)
    
    def update_version_info(self, version: str, **kwargs):
        """更新版本信息"""
        manifest = self._load()
        
        if version in manifest.get("versions", {}):
            manifest["versions"][version].update(kwargs)
            self._save(manifest)
    
    # ========== 待处理版本 ==========
    
    def get_pending_versions(self, all_versions: List[str]) -> List[str]:
        """获取待处理的版本
        
        Args:
            all_versions: 所有版本列表（从 versions.csv 解析）
        
        Returns:
            未处理的版本列表（已排序）
        """
        processed = set(self.get_processed_versions())
        pending = [v for v in all_versions if v not in processed]
        pending.sort(key=version_sort_key)
        return pending
    
    # ========== 重置 ==========
    
    def reset(self):
        """重置清单"""
        self._save({
            "project": self.project_dir.name,
            "last_processed_version": None,
            "processed_versions": [],
            "versions": {},
            "reset_at": datetime.now().isoformat()
        })
        logger.info("版本清单已重置")
    
    def reset_to_version(self, version: str):
        """重置到指定版本（删除该版本之后的记录）"""
        manifest = self._load()
        
        # 找到版本索引
        processed = manifest.get("processed_versions", [])
        if version in processed:
            idx = processed.index(version)
            # 保留到该版本（不含）
            manifest["processed_versions"] = processed[:idx]
            # 删除该版本及之后的详情
            for v in processed[idx:]:
                manifest.get("versions", {}).pop(v, None)
            
            # 更新最后处理版本
            manifest["last_processed_version"] = processed[idx-1] if idx > 0 else None
            
            self._save(manifest)
            logger.info("已重置到版本 %s 之前", version)
        else:
            logger.warning("版本 %s 未找到", version)
    
    # ========== 统计 ==========
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        manifest = self._load()
        
        versions = manifest.get("versions", {})
        
        return {
            "total_versions_processed": len(manifest.get("processed_versions", [])),
            "last_processed": manifest.get("last_processed_version"),
            "total_requirements_added": sum(
                v.get("requirements_added", 0) for v in versions.values()
            )
        }
    
    # ========== 辅助方法 ==========
    
    def print_status(self):
        """打印状态"""
        manifest = self._load()
        
        logger.info("\n%s", "=" * 60)
        logger.info("📊 版本清单状态")
        logger.info("%s", "=" * 60)
        logger.info("项目: %s", manifest.get('project'))
        logger.info("最后处理版本: %s", manifest.get('last_processed_version') or '无')
        logger.info("已处理版本数: %s", len(manifest.get('processed_versions', [])))
        
        if manifest.get("processed_versions"):
            logger.info("\n已处理版本:")
            for v in manifest["processed_versions"]:
                info = manifest.get("versions", {}).get(v, {})
                reqs = info.get("requirements_added", 0)
                processed_at = info.get("processed_at", "")[:10] if info.get("processed_at") else ""
                logger.info("  ✅ %s (%s 需求) - %s", v, reqs, processed_at)
        
        logger.info("\n%s", "=" * 60)