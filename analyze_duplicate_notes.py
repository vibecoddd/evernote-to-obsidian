#!/usr/bin/env python3
"""
分析和解决笔记重复问题
"""

import os
import sys
from pathlib import Path
import hashlib
import json
from typing import List, Dict, Set, Tuple
from datetime import datetime

# 添加src目录到Python路径
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

class DuplicateNotesAnalyzer:
    """笔记重复分析器"""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.duplicate_groups = []
        self.stats = {
            'total_notes': 0,
            'duplicate_notes': 0,
            'duplicate_groups': 0,
            'space_saved_mb': 0
        }

    def find_duplicates(self) -> List[List[Path]]:
        """查找重复笔记"""
        print("🔍 分析笔记重复问题...")

        if not self.vault_path.exists():
            print(f"❌ 目录不存在: {self.vault_path}")
            return []

        # 收集所有markdown文件
        md_files = list(self.vault_path.rglob('*.md'))
        self.stats['total_notes'] = len(md_files)

        print(f"📊 找到 {len(md_files)} 个笔记文件")

        if len(md_files) == 0:
            print("⚠️ 没有找到任何笔记文件")
            return []

        # 分析重复类型
        content_groups = self._group_by_content_hash(md_files)
        title_groups = self._group_by_title(md_files)
        filename_groups = self._group_by_filename(md_files)

        # 合并重复组
        all_groups = []
        all_groups.extend([group for group in content_groups if len(group) > 1])
        all_groups.extend([group for group in title_groups if len(group) > 1])
        all_groups.extend([group for group in filename_groups if len(group) > 1])

        # 去重合并的组
        self.duplicate_groups = self._dedupe_groups(all_groups)

        self.stats['duplicate_groups'] = len(self.duplicate_groups)
        self.stats['duplicate_notes'] = sum(len(group) - 1 for group in self.duplicate_groups)

        return self.duplicate_groups

    def _group_by_content_hash(self, files: List[Path]) -> List[List[Path]]:
        """按内容哈希分组"""
        print("📋 按内容哈希分组...")

        content_hash_map = {}

        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 标准化内容（去除空白字符差异）
                normalized_content = self._normalize_content(content)
                content_hash = hashlib.md5(normalized_content.encode()).hexdigest()

                if content_hash not in content_hash_map:
                    content_hash_map[content_hash] = []
                content_hash_map[content_hash].append(file_path)

            except Exception as e:
                print(f"⚠️ 读取文件失败 {file_path}: {e}")

        return list(content_hash_map.values())

    def _group_by_title(self, files: List[Path]) -> List[List[Path]]:
        """按标题分组"""
        print("📋 按笔记标题分组...")

        title_map = {}

        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 提取标题
                title = self._extract_title(content, file_path)
                normalized_title = title.strip().lower()

                if normalized_title not in title_map:
                    title_map[normalized_title] = []
                title_map[normalized_title].append(file_path)

            except Exception as e:
                print(f"⚠️ 读取文件失败 {file_path}: {e}")

        return list(title_map.values())

    def _group_by_filename(self, files: List[Path]) -> List[List[Path]]:
        """按文件名分组"""
        print("📋 按文件名分组...")

        filename_map = {}

        for file_path in files:
            # 去除扩展名，标准化文件名
            stem = file_path.stem.strip().lower()

            if stem not in filename_map:
                filename_map[stem] = []
            filename_map[stem].append(file_path)

        return list(filename_map.values())

    def _normalize_content(self, content: str) -> str:
        """标准化内容"""
        # 去除多余的空白字符
        lines = content.split('\n')
        normalized_lines = []

        for line in lines:
            # 去除行首行尾空格
            line = line.strip()
            # 跳过空行
            if line:
                normalized_lines.append(line)

        return '\n'.join(normalized_lines)

    def _extract_title(self, content: str, file_path: Path) -> str:
        """提取笔记标题"""
        lines = content.split('\n')

        # 查找第一个非空行作为标题
        for line in lines:
            line = line.strip()
            if line:
                # 如果是markdown标题格式
                if line.startswith('#'):
                    return line.lstrip('#').strip()
                else:
                    return line

        # 如果没有找到标题，使用文件名
        return file_path.stem

    def _dedupe_groups(self, groups: List[List[Path]]) -> List[List[Path]]:
        """去重重复组"""
        seen_files = set()
        unique_groups = []

        for group in groups:
            if len(group) <= 1:
                continue

            # 检查是否已经在其他组中处理过
            group_files = set(group)
            if group_files & seen_files:
                continue

            unique_groups.append(group)
            seen_files.update(group_files)

        return unique_groups

    def generate_report(self) -> str:
        """生成重复分析报告"""
        report = []
        report.append("📋 笔记重复分析报告")
        report.append("=" * 50)
        report.append(f"总笔记数: {self.stats['total_notes']}")
        report.append(f"重复组数: {self.stats['duplicate_groups']}")
        report.append(f"重复笔记数: {self.stats['duplicate_notes']}")
        report.append("")

        if not self.duplicate_groups:
            report.append("✅ 没有发现重复笔记")
            return '\n'.join(report)

        report.append("🔍 发现的重复组:")
        report.append("")

        for i, group in enumerate(self.duplicate_groups, 1):
            report.append(f"重复组 {i} ({len(group)} 个文件):")

            for j, file_path in enumerate(group):
                file_size = file_path.stat().st_size
                mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)

                marker = "📍 [保留]" if j == 0 else "🗑️ [删除]"
                report.append(f"  {marker} {file_path.name}")
                report.append(f"     路径: {file_path}")
                report.append(f"     大小: {file_size} bytes")
                report.append(f"     修改时间: {mod_time}")

            report.append("")

        return '\n'.join(report)

    def create_deduplication_plan(self) -> Dict:
        """创建去重计划"""
        plan = {
            'keep_files': [],
            'remove_files': [],
            'backup_info': {}
        }

        for group in self.duplicate_groups:
            if len(group) <= 1:
                continue

            # 选择保留策略：保留最新的文件
            group_sorted = sorted(group, key=lambda x: x.stat().st_mtime, reverse=True)

            keep_file = group_sorted[0]
            remove_files = group_sorted[1:]

            plan['keep_files'].append(str(keep_file))

            for remove_file in remove_files:
                plan['remove_files'].append(str(remove_file))
                plan['backup_info'][str(remove_file)] = {
                    'kept_as': str(keep_file),
                    'original_size': remove_file.stat().st_size,
                    'original_mtime': remove_file.stat().st_mtime
                }

        return plan

    def execute_deduplication(self, dry_run: bool = True) -> bool:
        """执行去重操作"""
        if not self.duplicate_groups:
            print("✅ 没有重复文件需要处理")
            return True

        plan = self.create_deduplication_plan()

        print(f"📋 去重计划:")
        print(f"   保留文件: {len(plan['keep_files'])} 个")
        print(f"   删除文件: {len(plan['remove_files'])} 个")

        if dry_run:
            print("🔍 预演模式 - 不会实际删除文件")
            for remove_file in plan['remove_files']:
                kept_as = plan['backup_info'][remove_file]['kept_as']
                print(f"   🗑️ 将删除: {Path(remove_file).name}")
                print(f"     保留为: {Path(kept_as).name}")
            return True

        # 实际执行删除
        success_count = 0

        for remove_file_str in plan['remove_files']:
            try:
                remove_file = Path(remove_file_str)
                if remove_file.exists():
                    remove_file.unlink()
                    success_count += 1
                    print(f"🗑️ 已删除: {remove_file.name}")

            except Exception as e:
                print(f"❌ 删除失败 {remove_file}: {e}")

        print(f"✅ 成功删除 {success_count} 个重复文件")

        # 保存去重信息
        dedup_log = self.vault_path / 'deduplication_log.json'
        with open(dedup_log, 'w', encoding='utf-8') as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)

        print(f"📄 去重日志已保存: {dedup_log}")

        return True

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='分析和解决笔记重复问题')
    parser.add_argument('vault_path', help='Obsidian库路径')
    parser.add_argument('--execute', action='store_true', help='实际执行去重（默认为预演）')
    parser.add_argument('--report-only', action='store_true', help='仅生成报告')

    # 如果没有参数，使用默认路径进行分析
    if len(sys.argv) == 1:
        print("🔍 使用默认路径进行重复分析...")
        vault_paths = [
            '/tmp/debug_vault',
            '/tmp/test_vault_integration',
            '/tmp/obsidian_vault'
        ]

        for vault_path in vault_paths:
            if Path(vault_path).exists():
                print(f"\n分析路径: {vault_path}")
                analyzer = DuplicateNotesAnalyzer(vault_path)
                analyzer.find_duplicates()
                print(analyzer.generate_report())
        return

    args = parser.parse_args()

    analyzer = DuplicateNotesAnalyzer(args.vault_path)

    print(f"🔍 分析路径: {args.vault_path}")

    # 查找重复
    analyzer.find_duplicates()

    # 生成报告
    print(analyzer.generate_report())

    if args.report_only:
        return

    # 执行去重
    if analyzer.duplicate_groups:
        dry_run = not args.execute
        analyzer.execute_deduplication(dry_run=dry_run)

if __name__ == "__main__":
    main()