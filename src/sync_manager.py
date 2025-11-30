#!/usr/bin/env python3
"""
同步管理器模块 - 印象笔记到Obsidian同步工具
"""

import json
import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import asdict

from enex_parser import Note


class SyncState:
    """同步状态管理"""

    def __init__(self, state_file: str):
        """
        初始化同步状态

        Args:
            state_file: 状态文件路径
        """
        self.state_file = Path(state_file)
        self.state_data = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        """
        加载同步状态

        Returns:
            状态数据
        """
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load sync state: {e}")

        return {
            'last_sync': None,
            'processed_files': {},  # {enex_path: {hash, modified_time}}
            'note_hashes': {},      # {note_id: content_hash}
            'file_mappings': {},    # {note_id: output_file_path}
            'statistics': {
                'total_synced': 0,
                'last_sync_count': 0
            }
        }

    def save_state(self) -> None:
        """保存同步状态"""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state_data, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            print(f"Warning: Failed to save sync state: {e}")

    def is_file_processed(self, enex_path: str) -> bool:
        """
        检查文件是否已处理

        Args:
            enex_path: ENEX文件路径

        Returns:
            是否已处理
        """
        if enex_path not in self.state_data['processed_files']:
            return False

        file_info = self.state_data['processed_files'][enex_path]
        current_hash = self._calculate_file_hash(enex_path)
        current_mtime = os.path.getmtime(enex_path)

        return (file_info.get('hash') == current_hash and
                file_info.get('modified_time') == current_mtime)

    def mark_file_processed(self, enex_path: str) -> None:
        """
        标记文件为已处理

        Args:
            enex_path: ENEX文件路径
        """
        self.state_data['processed_files'][enex_path] = {
            'hash': self._calculate_file_hash(enex_path),
            'modified_time': os.path.getmtime(enex_path),
            'processed_at': datetime.now().isoformat()
        }

    def is_note_changed(self, note: Note) -> bool:
        """
        检查笔记是否发生变化

        Args:
            note: 笔记对象

        Returns:
            是否发生变化
        """
        note_id = self._generate_note_id(note)
        content_hash = self._calculate_note_hash(note)

        stored_hash = self.state_data['note_hashes'].get(note_id)
        return stored_hash != content_hash

    def update_note_hash(self, note: Note, output_path: str) -> None:
        """
        更新笔记哈希值

        Args:
            note: 笔记对象
            output_path: 输出路径
        """
        note_id = self._generate_note_id(note)
        content_hash = self._calculate_note_hash(note)

        self.state_data['note_hashes'][note_id] = content_hash
        self.state_data['file_mappings'][note_id] = output_path

    def get_note_output_path(self, note: Note) -> Optional[str]:
        """
        获取笔记的输出路径

        Args:
            note: 笔记对象

        Returns:
            输出路径或None
        """
        note_id = self._generate_note_id(note)
        return self.state_data['file_mappings'].get(note_id)

    def update_statistics(self, sync_count: int) -> None:
        """
        更新统计信息

        Args:
            sync_count: 本次同步数量
        """
        self.state_data['last_sync'] = datetime.now().isoformat()
        self.state_data['statistics']['last_sync_count'] = sync_count
        self.state_data['statistics']['total_synced'] += sync_count

    def cleanup_deleted_files(self, vault_path: Path) -> List[str]:
        """
        清理已删除的文件

        Args:
            vault_path: Obsidian库路径

        Returns:
            清理的文件列表
        """
        cleaned_files = []
        note_mappings = self.state_data['file_mappings'].copy()

        for note_id, file_path in note_mappings.items():
            full_path = vault_path / file_path
            if not full_path.exists():
                # 文件不存在，从状态中移除
                del self.state_data['file_mappings'][note_id]
                if note_id in self.state_data['note_hashes']:
                    del self.state_data['note_hashes'][note_id]
                cleaned_files.append(file_path)

        return cleaned_files

    def _calculate_file_hash(self, file_path: str) -> str:
        """
        计算文件哈希值

        Args:
            file_path: 文件路径

        Returns:
            SHA256哈希值
        """
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return ""

    def _calculate_note_hash(self, note: Note) -> str:
        """
        计算笔记哈希值

        Args:
            note: 笔记对象

        Returns:
            SHA256哈希值
        """
        # 创建笔记的唯一标识字符串
        note_data = {
            'title': note.title,
            'content': note.content,
            'tags': sorted(note.tags) if note.tags else [],
            'created': note.created.isoformat() if note.created else None,
            'updated': note.updated.isoformat() if note.updated else None,
            'attachments_count': len(note.attachments)
        }

        content_str = json.dumps(note_data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(content_str.encode('utf-8')).hexdigest()

    def _generate_note_id(self, note: Note) -> str:
        """
        生成笔记ID

        Args:
            note: 笔记对象

        Returns:
            笔记ID
        """
        # 使用标题和创建时间生成ID
        id_data = f"{note.title}_{note.created.isoformat() if note.created else 'no_date'}"
        return hashlib.md5(id_data.encode('utf-8')).hexdigest()[:16]


class SyncManager:
    """同步管理器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化同步管理器

        Args:
            config: 配置字典
        """
        self.config = config
        self.incremental = config.get('sync.incremental', True)
        self.check_modification_time = config.get('sync.check_modification_time', True)
        self.skip_unchanged = config.get('sync.skip_unchanged', True)

        # 初始化同步状态
        state_file = config.get('sync.state_file', '.sync_state.json')
        vault_path = Path(config.get('output.obsidian_vault', ''))
        self.state_file_path = vault_path / state_file
        self.sync_state = SyncState(str(self.state_file_path))

    def should_process_file(self, enex_path: str) -> bool:
        """
        判断是否应该处理文件

        Args:
            enex_path: ENEX文件路径

        Returns:
            是否应该处理
        """
        if not self.incremental:
            return True

        if not os.path.exists(enex_path):
            return False

        # 检查文件是否已处理且未发生变化
        if self.sync_state.is_file_processed(enex_path):
            if self.skip_unchanged:
                return False

        return True

    def should_process_note(self, note: Note) -> bool:
        """
        判断是否应该处理笔记

        Args:
            note: 笔记对象

        Returns:
            是否应该处理
        """
        if not self.incremental:
            return True

        # 检查笔记是否发生变化
        return self.sync_state.is_note_changed(note)

    def filter_notes_for_sync(self, notes: List[Note]) -> List[Note]:
        """
        过滤需要同步的笔记

        Args:
            notes: 笔记列表

        Returns:
            需要同步的笔记列表
        """
        if not self.incremental:
            return notes

        filtered_notes = []
        for note in notes:
            if self.should_process_note(note):
                filtered_notes.append(note)

        return filtered_notes

    def mark_file_processed(self, enex_path: str) -> None:
        """
        标记文件为已处理

        Args:
            enex_path: ENEX文件路径
        """
        self.sync_state.mark_file_processed(enex_path)

    def mark_note_processed(self, note: Note, output_path: str) -> None:
        """
        标记笔记为已处理

        Args:
            note: 笔记对象
            output_path: 输出路径
        """
        self.sync_state.update_note_hash(note, output_path)

    def finalize_sync(self, sync_count: int) -> None:
        """
        完成同步

        Args:
            sync_count: 同步的文件数量
        """
        # 更新统计信息
        self.sync_state.update_statistics(sync_count)

        # 清理已删除的文件
        vault_path = Path(self.config.get('output.obsidian_vault', ''))
        cleaned_files = self.sync_state.cleanup_deleted_files(vault_path)

        if cleaned_files:
            print(f"Cleaned up {len(cleaned_files)} deleted files from sync state")

        # 保存状态
        self.sync_state.save_state()

    def get_sync_statistics(self) -> Dict[str, Any]:
        """
        获取同步统计信息

        Returns:
            统计信息字典
        """
        stats = self.sync_state.state_data['statistics'].copy()
        stats['last_sync_time'] = self.sync_state.state_data.get('last_sync')
        stats['tracked_files'] = len(self.sync_state.state_data['processed_files'])
        stats['tracked_notes'] = len(self.sync_state.state_data['note_hashes'])

        return stats

    def reset_sync_state(self) -> None:
        """重置同步状态"""
        self.sync_state.state_data = {
            'last_sync': None,
            'processed_files': {},
            'note_hashes': {},
            'file_mappings': {},
            'statistics': {
                'total_synced': 0,
                'last_sync_count': 0
            }
        }
        self.sync_state.save_state()

    def create_sync_report(self, processed_files: List[str],
                          total_notes: int, skipped_notes: int) -> str:
        """
        创建同步报告

        Args:
            processed_files: 处理的文件列表
            total_notes: 总笔记数
            skipped_notes: 跳过的笔记数

        Returns:
            同步报告文本
        """
        report_lines = [
            "# 印象笔记同步报告",
            "",
            f"同步时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"同步模式: {'增量同步' if self.incremental else '完整同步'}",
            "",
            "## 处理统计",
            f"- 处理文件数: {len(processed_files)}",
            f"- 总笔记数: {total_notes}",
            f"- 跳过笔记数: {skipped_notes}",
            f"- 实际处理: {total_notes - skipped_notes}",
            ""
        ]

        if processed_files:
            report_lines.extend([
                "## 处理的文件",
                ""
            ])
            for file_path in processed_files:
                report_lines.append(f"- {file_path}")
            report_lines.append("")

        # 添加历史统计
        stats = self.get_sync_statistics()
        report_lines.extend([
            "## 历史统计",
            f"- 累计同步: {stats.get('total_synced', 0)} 个笔记",
            f"- 上次同步: {stats.get('last_sync_time', '从未同步')}",
            f"- 跟踪文件: {stats.get('tracked_files', 0)} 个",
            f"- 跟踪笔记: {stats.get('tracked_notes', 0)} 个"
        ])

        return "\n".join(report_lines)

    def save_sync_report(self, report_content: str) -> str:
        """
        保存同步报告

        Args:
            report_content: 报告内容

        Returns:
            报告文件路径
        """
        vault_path = Path(self.config.get('output.obsidian_vault', ''))
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = vault_path / f"Sync_Report_{timestamp}.md"

        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            return str(report_path)
        except Exception as e:
            print(f"Warning: Failed to save sync report: {e}")
            return ""


class ConflictResolver:
    """冲突解决器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化冲突解决器

        Args:
            config: 配置字典
        """
        self.config = config

    def resolve_file_conflict(self, file_path: Path, new_content: str) -> str:
        """
        解决文件冲突

        Args:
            file_path: 文件路径
            new_content: 新内容

        Returns:
            解决策略 ('overwrite', 'skip', 'backup')
        """
        strategy = self.config.get('file_organization.handle_duplicates', 'rename')

        if strategy == 'overwrite':
            return 'overwrite'
        elif strategy == 'skip':
            return 'skip'
        else:  # rename or backup
            return 'backup'

    def resolve_content_conflict(self, existing_content: str,
                               new_content: str, note: Note) -> str:
        """
        解决内容冲突

        Args:
            existing_content: 现有内容
            new_content: 新内容
            note: 笔记对象

        Returns:
            解决后的内容
        """
        # 简单的冲突解决：如果内容不同，创建合并版本
        if existing_content.strip() != new_content.strip():
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            conflict_marker = f"""
---
**内容冲突检测** (合并于 {timestamp})

**原有内容:**
{existing_content}

---

**新内容:**
{new_content}

---
"""
            return conflict_marker

        return new_content


if __name__ == "__main__":
    # 测试同步管理器
    config = {
        'sync': {
            'incremental': True,
            'state_file': '.sync_state.json',
            'skip_unchanged': True
        },
        'output': {
            'obsidian_vault': './test_vault'
        }
    }

    sync_manager = SyncManager(config)
    print("Sync Manager initialized successfully")