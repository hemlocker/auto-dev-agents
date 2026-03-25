"""
CSV 输入解析器 - 支持版本化需求输入

输入格式：
- input/versions.csv          # 版本清单（必需）
- input/feedback/*.csv        # 需求文件（必须包含 version 列）
"""

import csv
import logging
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict
from datetime import datetime
from .revision_history import version_sort_key


logger = logging.getLogger(__name__)


@dataclass
class Requirement:
    """需求数据结构"""
    id: str
    version: str
    title: str
    type: str = "functional"  # functional / non-functional
    priority: str = "Should"   # Must / Should / Could / Won't
    status: str = "active"     # active / deprecated / superseded
    module: Optional[str] = None
    role: Optional[str] = None
    description: str = ""
    acceptance_criteria: List[str] = field(default_factory=list)
    input_source: Optional[str] = None
    created_at: Optional[str] = None
    deprecated_at: Optional[str] = None
    superseded_by: Optional[str] = None
    notes: Optional[str] = None
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Version:
    """版本数据结构"""
    version: str
    created_at: str
    author: Optional[str] = None
    status: str = "active"
    description: Optional[str] = None
    input_files: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d["input_files"] = ";".join(self.input_files) if self.input_files else ""
        return d


class CSVInputParser:
    """CSV 输入解析器"""
    
    # 必需的列
    REQUIRED_COLUMNS = {"id", "version", "title"}
    
    # 所有支持的列
    SUPPORTED_COLUMNS = [
        "id", "version", "title", "type", "priority", "status",
        "module", "role", "description", "acceptance_criteria",
        "input_source", "created_at", "deprecated_at", "superseded_by", "notes"
    ]
    
    def __init__(self, input_dir: Path):
        self.input_dir = Path(input_dir)
        self._versions_cache: Optional[List[Version]] = None
    
    # ========== 版本管理 ==========
    
    def parse_versions(self) -> List[Version]:
        """解析版本清单
        
        Returns:
            版本列表，按版本号排序
        """
        if self._versions_cache is not None:
            return self._versions_cache
        
        versions_file = self.input_dir / "versions.csv"
        
        if not versions_file.exists():
            logger.warning("版本清单文件不存在: %s", versions_file)
            return []
        
        versions = []
        
        with open(versions_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                version = Version(
                    version=row.get('version', '').strip(),
                    created_at=row.get('created_at', '').strip(),
                    author=row.get('author', '').strip() or None,
                    status=row.get('status', 'active').strip(),
                    description=row.get('description', '').strip() or None,
                    input_files=[f.strip() for f in row.get('input_files', '').split(';') if f.strip()]
                )
                
                if version.version:  # 忽略空版本
                    versions.append(version)
        
        # 按版本号排序
        from .revision_history import version_sort_key
        versions.sort(key=lambda v: version_sort_key(v.version))
        
        self._versions_cache = versions
        return versions
    
    def get_version(self, version: str) -> Optional[Version]:
        """获取指定版本信息"""
        versions = self.parse_versions()
        return next((v for v in versions if v.version == version), None)
    
    def get_latest_version(self) -> Optional[str]:
        """获取最新版本号"""
        versions = self.parse_versions()
        return versions[-1].version if versions else None
    
    def get_all_versions(self) -> List[str]:
        """获取所有版本号列表"""
        return [v.version for v in self.parse_versions()]
    
    # ========== 需求解析 ==========
    
    def parse_requirements(self, version: str = None) -> List[Requirement]:
        """解析需求
        
        Args:
            version: 指定版本，None 表示解析所有版本
        
        Returns:
            需求列表
        """
        all_requirements = []
        
        # 扫描所有 CSV 文件
        for csv_file in self.input_dir.rglob("*.csv"):
            if csv_file.name == "versions.csv":
                continue
            
            reqs = self._parse_requirements_file(csv_file)
            all_requirements.extend(reqs)
        
        # 按版本过滤
        if version:
            all_requirements = [r for r in all_requirements if r.version == version]
        
        return all_requirements
    
    def parse_requirements_by_version(self, version: str) -> List[Requirement]:
        """解析指定版本的需求
        
        从 versions.csv 中找到该版本的 input_files，只解析这些文件
        """
        version_info = self.get_version(version)
        
        if not version_info:
            logger.warning("版本 %s 不存在", version)
            return []
        
        requirements = []
        
        for input_file in version_info.input_files:
            file_path = self.input_dir / input_file
            if file_path.exists():
                reqs = self._parse_requirements_file(file_path, version)
                requirements.extend(reqs)
            else:
                logger.warning("输入文件不存在: %s", file_path)
        
        return requirements
    
    def _parse_requirements_file(self, file_path: Path, filter_version: str = None) -> List[Requirement]:
        """解析单个需求文件"""
        requirements = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # 验证必需列
                if not self.REQUIRED_COLUMNS.issubset(set(reader.fieldnames or [])):
                    missing = self.REQUIRED_COLUMNS - set(reader.fieldnames or [])
                    logger.warning("文件 %s 缺少必需列: %s", file_path, missing)
                    return []
                
                for row_num, row in enumerate(reader, start=2):  # start=2 因为有表头
                    try:
                        req = self._parse_requirement_row(row, file_path, filter_version)
                        if req:
                            requirements.append(req)
                    except Exception as e:
                        logger.warning("文件 %s 第 %s 行解析失败: %s", file_path, row_num, e)
        
        except Exception as e:
            logger.warning("无法读取文件 %s: %s", file_path, e)
        
        return requirements
    
    def _parse_requirement_row(self, row: dict, file_path: Path, filter_version: str = None) -> Optional[Requirement]:
        """解析单行需求"""
        version = row.get('version', '').strip()
        
        # 必须有版本号
        if not version:
            return None
        
        # 如果指定了过滤版本，只返回匹配的
        if filter_version and version != filter_version:
            return None
        
        # 解析验收标准（分号分隔）
        acceptance_criteria = []
        if row.get('acceptance_criteria'):
            acceptance_criteria = [
                ac.strip() for ac in row['acceptance_criteria'].split(';') 
                if ac.strip()
            ]
        
        return Requirement(
            id=row.get('id', '').strip(),
            version=version,
            title=row.get('title', '').strip(),
            type=row.get('type', 'functional').strip(),
            priority=row.get('priority', 'Should').strip(),
            status=row.get('status', 'active').strip(),
            module=row.get('module', '').strip() or None,
            role=row.get('role', '').strip() or None,
            description=row.get('description', '').strip(),
            acceptance_criteria=acceptance_criteria,
            input_source=str(file_path.relative_to(self.input_dir)),
            created_at=row.get('created_at', '').strip() or None,
            deprecated_at=row.get('deprecated_at', '').strip() or None,
            superseded_by=row.get('superseded_by', '').strip() or None,
            notes=row.get('notes', '').strip() or None
        )
    
    # ========== 辅助方法 ==========
    
    def get_active_requirements(self) -> List[Requirement]:
        """获取所有活跃需求（排除废弃）"""
        all_reqs = self.parse_requirements()
        return [r for r in all_reqs if r.status == 'active']
    
    def get_requirements_by_priority(self, priority: str) -> List[Requirement]:
        """按优先级获取需求"""
        all_reqs = self.parse_requirements()
        return [r for r in all_reqs if r.priority == priority]
    
    def get_requirements_by_module(self, module: str) -> List[Requirement]:
        """按模块获取需求"""
        all_reqs = self.parse_requirements()
        return [r for r in all_reqs if r.module == module]
    
    def get_requirement(self, req_id: str) -> Optional[Requirement]:
        """获取单个需求"""
        all_reqs = self.parse_requirements()
        return next((r for r in all_reqs if r.id == req_id), None)
    
    def validate_input(self) -> Dict[str, any]:
        """验证输入数据
        
        Returns:
            {
                "valid": bool,
                "errors": [str, ...],
                "warnings": [str, ...],
                "stats": {...}
            }
        """
        errors = []
        warnings = []
        
        # 检查 versions.csv
        versions_file = self.input_dir / "versions.csv"
        if not versions_file.exists():
            errors.append("缺少 versions.csv 文件")
            return {"valid": False, "errors": errors, "warnings": warnings, "stats": {}}
        
        versions = self.parse_versions()
        if not versions:
            errors.append("versions.csv 中没有有效版本")
        else:
            # 检查每个版本的输入文件
            for v in versions:
                for input_file in v.input_files:
                    file_path = self.input_dir / input_file
                    if not file_path.exists():
                        errors.append(f"版本 {v.version} 的输入文件不存在: {input_file}")
        
        # 检查需求文件
        all_reqs = self.parse_requirements()
        
        # 检查重复 ID
        ids = [r.id for r in all_reqs]
        duplicates = [id for id in set(ids) if ids.count(id) > 1]
        if duplicates:
            errors.append(f"存在重复的需求 ID: {', '.join(duplicates)}")
        
        # 检查无效引用
        for req in all_reqs:
            if req.superseded_by and req.superseded_by not in ids:
                warnings.append(f"需求 {req.id} 引用了不存在的替代需求: {req.superseded_by}")
        
        # 统计
        stats = {
            "total_versions": len(versions),
            "total_requirements": len(all_reqs),
            "by_priority": {},
            "by_status": {},
            "by_type": {}
        }
        
        for req in all_reqs:
            stats["by_priority"][req.priority] = stats["by_priority"].get(req.priority, 0) + 1
            stats["by_status"][req.status] = stats["by_status"].get(req.status, 0) + 1
            stats["by_type"][req.type] = stats["by_type"].get(req.type, 0) + 1
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "stats": stats
        }
    
    def clear_cache(self):
        """清除缓存"""
        self._versions_cache = None