#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工单去重工具
Ticket Deduplication Tool

扫描 input/tickets/ 目录，识别并合并重复问题

使用方式：
  python3 scripts/ticket_dedup.py --project demo_project
"""

import argparse
import json
import re
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


class TicketDeduplicator:
    """工单去重器"""
    
    def __init__(self, project_name: str, base_dir: str = None):
        self.project_name = project_name
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent
        self.tickets_dir = self.base_dir / "projects" / project_name / "input" / "tickets"
        self.output_dir = self.base_dir / "projects" / project_name / "output" / "optimizer"
        
    def _extract_keywords(self, text: str) -> set:
        """提取关键词"""
        # 移除标点和特殊字符
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text.lower())
        # 分词
        words = text.split()
        # 过滤停用词
        stop_words = {'的', '是', '有', '在', '和', '了', '不', '这', '我', '你', '他', '她', '它'}
        keywords = set(w for w in words if w not in stop_words and len(w) > 1)
        return keywords
    
    def _compute_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（Jaccard 相似度）"""
        keywords1 = self._extract_keywords(text1)
        keywords2 = self._extract_keywords(text2)
        
        if not keywords1 or not keywords2:
            return 0.0
        
        intersection = keywords1 & keywords2
        union = keywords1 | keywords2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _extract_issues(self, content: str) -> List[Dict]:
        """从工单内容提取问题列表"""
        issues = []
        
        # 匹配问题模式：问题标题 或 - 问题描述 或 | ID | 描述 |
        patterns = [
            r'###?\s*(.+?)(?:\n|$)',  ### 标题
            r'-\s*\*\*(.+?)\*\*',     # **加粗**
            r'\|\s*([A-Z]+-\d+)\s*\|', # | ID |
            r'问题\s*[:：]\s*(.+?)(?:\n|$)',  # 问题：xxx
        ]
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 尝试匹配各种模式
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    issues.append({
                        'text': match.group(1).strip(),
                        'line': line
                    })
                    break
        
        return issues
    
    def scan_tickets(self) -> List[Dict]:
        """扫描所有工单"""
        tickets = []
        
        if not self.tickets_dir.exists():
            return tickets
        
        for ticket_file in self.tickets_dir.glob("*.md"):
            with open(ticket_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            issues = self._extract_issues(content)
            
            tickets.append({
                'file': ticket_file.name,
                'path': str(ticket_file),
                'content': content,
                'issues': issues,
                'issue_count': len(issues)
            })
        
        return tickets
    
    def find_duplicates(self, tickets: List[Dict], threshold: float = 0.5) -> List[Dict]:
        """查找重复问题"""
        duplicate_groups = []
        checked = set()
        
        for i, ticket1 in enumerate(tickets):
            for issue1 in ticket1.get('issues', []):
                key1 = f"{ticket1['file']}:{issue1['text']}"
                if key1 in checked:
                    continue
                
                group = {
                    'primary': {
                        'file': ticket1['file'],
                        'issue': issue1['text'],
                        'line': issue1['line']
                    },
                    'duplicates': []
                }
                
                for j, ticket2 in enumerate(tickets):
                    if i == j:
                        continue
                    
                    for issue2 in ticket2.get('issues', []):
                        key2 = f"{ticket2['file']}:{issue2['text']}"
                        if key2 in checked:
                            continue
                        
                        similarity = self._compute_similarity(issue1['text'], issue2['text'])
                        
                        if similarity >= threshold:
                            group['duplicates'].append({
                                'file': ticket2['file'],
                                'issue': issue2['text'],
                                'line': issue2['line'],
                                'similarity': round(similarity, 2)
                            })
                            checked.add(key2)
                
                if group['duplicates']:
                    duplicate_groups.append(group)
                
                checked.add(key1)
        
        return duplicate_groups
    
    def generate_report(self, tickets: List[Dict], duplicates: List[Dict]) -> str:
        """生成去重报告"""
        report = f"""# 工单去重报告

**项目**: {self.project_name}
**生成时间**: {datetime.now().isoformat()}
**工单总数**: {len(tickets)}

---

## 📊 统计

| 指标 | 数值 |
|------|------|
| 扫描工单数 | {len(tickets)} |
| 识别问题总数 | {sum(t.get('issue_count', 0) for t in tickets)} |
| 重复问题组 | {len(duplicates)} |
| 可合并问题数 | {sum(len(d['duplicates']) for d in duplicates)} |

---

## 📁 工单列表

"""
        for ticket in tickets:
            report += f"- {ticket['file']} ({ticket.get('issue_count', 0)} 个问题)\n"
        
        if duplicates:
            report += f"""
---

## 🔄 重复问题详情

"""
            for i, group in enumerate(duplicates, 1):
                report += f"""### 重复组 {i}

**主要问题**: {group['primary']['file']}
> {group['primary']['issue']}

**重复项**:
"""
                for dup in group['duplicates']:
                    report += f"- [{dup['similarity']*100:.0f}%] {dup['file']}: {dup['issue']}\n"
                report += "\n"
        
        report += f"""
---

## 📝 建议

"""
        if duplicates:
            report += """1. 合并重复问题，减少工单数量
2. 保留最详细的描述，删除重复项
3. 在 ticket 系统中实现自动去重
"""
        else:
            report += "无重复问题，工单管理良好。"
        
        report += f"""
---

**生成工具**: ticket_dedup.py
"""
        
        return report
    
    def run(self, threshold: float = 0.5) -> Dict:
        """执行去重分析"""
        # 扫描工单
        tickets = self.scan_tickets()
        
        # 查找重复
        duplicates = self.find_duplicates(tickets, threshold)
        
        # 生成报告
        report = self.generate_report(tickets, duplicates)
        
        # 保存报告
        self.output_dir.mkdir(parents=True, exist_ok=True)
        report_file = self.output_dir / f"ticket-dedup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return {
            'tickets_scanned': len(tickets),
            'total_issues': sum(t.get('issue_count', 0) for t in tickets),
            'duplicate_groups': len(duplicates),
            'issues_to_merge': sum(len(d['duplicates']) for d in duplicates),
            'report_file': str(report_file)
        }


def main():
    parser = argparse.ArgumentParser(description="工单去重工具")
    parser.add_argument("--project", "-p", required=True, help="项目名称")
    parser.add_argument("--threshold", "-t", type=float, default=0.5, help="相似度阈值 (0-1)")
    
    args = parser.parse_args()
    
    deduper = TicketDeduplicator(project_name=args.project)
    result = deduper.run(threshold=args.threshold)
    
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    exit(main())