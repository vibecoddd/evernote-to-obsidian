#!/usr/bin/env python3
"""
去重管理器 - 防止多次导出时产生重复笔记
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Set, List, Optional, Tuple
from datetime import datetime

class DeduplicationManager:
    """去重管理器"""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.dedup_db_path = self.output_dir / '.migration_history.json'
        self.history = self._load_history()

    def _load_history(self) -> Dict:
        """加载历史记录"""
        if self.dedup_db_path.exists():
            try:
                with open(self.dedup_db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ 加载历史记录失败: {e}")

        return {
            'migrations': [],
            'processed_notes': {},  # note_id -> file_info
            'processed_files': {},  # file_hash -> file_path
            'deleted_notes': {},    # note_id -> deletion_info
            'last_migration': None
        }

    def _save_history(self):
        """保存历史记录"""
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            with open(self.dedup_db_path, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ 保存历史记录失败: {e}")

    def start_migration(self, migration_id: str, source_info: Dict) -> Dict:
        """开始新的迁移会话"""
        migration_info = {
            'migration_id': migration_id,
            'start_time': datetime.now().isoformat(),
            'source_info': source_info,
            'status': 'running',
            'stats': {
                'total_notes': 0,
                'new_notes': 0,
                'skipped_duplicates': 0,
                'updated_notes': 0
            }
        }

        self.history['migrations'].append(migration_info)
        self.history['last_migration'] = migration_id
        self._save_history()

        print(f"🆕 开始迁移会话: {migration_id}")

        # 检查是否有之前的迁移
        previous_migrations = [m for m in self.history['migrations'] if m['migration_id'] != migration_id]
        if previous_migrations:
            print(f"📋 发现 {len(previous_migrations)} 个历史迁移")
            print(f"📊 已处理笔记: {len(self.history['processed_notes'])} 个")

        return migration_info

    def is_note_deleted(self, note_id: str) -> bool:
        """检查笔记是否已删除"""
        return note_id in self.history['deleted_notes']

    def mark_note_deleted(self, note_id: str, note_title: str = "Unknown"):
        """标记笔记为已删除"""
        deletion_info = {
            'deleted_time': datetime.now().isoformat(),
            'title': note_title,
            'migration_id': self.history['last_migration']
        }

        self.history['deleted_notes'][note_id] = deletion_info

        # 如果文件已存在，删除它
        if note_id in self.history['processed_notes']:
            note_info = self.history['processed_notes'][note_id]
            output_file = note_info.get('output_file')

            if output_file and Path(output_file).exists():
                try:
                    Path(output_file).unlink()
                    print(f"🗑️ 已删除笔记文件: {Path(output_file).name}")
                except Exception as e:
                    print(f"❌ 删除文件失败: {e}")

            # 从已处理记录中移除
            del self.history['processed_notes'][note_id]

        print(f"🗑️ 标记笔记已删除: {note_title}")

    def detect_deleted_notes(self, current_note_ids: Set[str]):
        """
        检测已删除的笔记

        Args:
            current_note_ids: 当前导出中的笔记ID集合
        """
        previously_processed = set(self.history['processed_notes'].keys())
        deleted_note_ids = previously_processed - current_note_ids

        if deleted_note_ids:
            print(f"🔍 检测到 {len(deleted_note_ids)} 个已删除的笔记")

            for note_id in deleted_note_ids:
                if note_id not in self.history['deleted_notes']:
                    note_info = self.history['processed_notes'].get(note_id, {})
                    title = note_info.get('title', 'Unknown')
                    self.mark_note_deleted(note_id, title)

    def should_process_note(self, note_data: Dict) -> Tuple[bool, str]:
        """
        检查是否应该处理这个笔记
        返回: (should_process, reason)
        """
        note_id = note_data.get('guid') or note_data.get('id')
        title = note_data.get('title', 'Untitled')
        content = note_data.get('content', '')

        # 0. 检查笔记是否已被标记为删除
        if note_id and self.is_note_deleted(note_id):
            # 如果笔记重新出现，从删除列表中移除
            del self.history['deleted_notes'][note_id]
            print(f"🔄 笔记重新出现，从删除列表移除: {title}")

        # 1. 检查笔记ID是否已存在
        if note_id and note_id in self.history['processed_notes']:
            existing_info = self.history['processed_notes'][note_id]

            # 检查内容是否有更新
            content_hash = self._calculate_content_hash(content)
            if existing_info.get('content_hash') == content_hash:
                return False, f"笔记已存在且内容未变化: {title}"
            else:
                return True, f"笔记内容已更新，需要重新处理: {title}"

        # 2. 检查内容哈希
        content_hash = self._calculate_content_hash(content)
        for processed_id, info in self.history['processed_notes'].items():
            if info.get('content_hash') == content_hash:
                return False, f"发现内容重复笔记: {title} (重复于 {info.get('title', 'Unknown')})"

        # 3. 检查标题重复（可选，可能有合理的重复标题）
        title_normalized = self._normalize_title(title)
        similar_notes = []
        for processed_id, info in self.history['processed_notes'].items():
            if self._normalize_title(info.get('title', '')) == title_normalized:
                similar_notes.append(info.get('title'))

        if similar_notes:
            print(f"⚠️ 发现相似标题: {title} (与 {len(similar_notes)} 个笔记标题相似)")

        return True, f"新笔记，可以处理: {title}"

    def should_process_file(self, file_path: str, content: str = None) -> Tuple[bool, str]:
        """
        检查是否应该处理这个文件
        返回: (should_process, reason)
        """
        file_path = Path(file_path)

        # 如果文件已存在，检查内容
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_content = f.read()

                if content and existing_content == content:
                    return False, f"文件内容相同，跳过: {file_path.name}"
                elif content:
                    return True, f"文件内容不同，需要更新: {file_path.name}"
                else:
                    return False, f"文件已存在: {file_path.name}"
            except Exception:
                return True, f"无法读取现有文件，重新创建: {file_path.name}"

        return True, f"新文件: {file_path.name}"

    def mark_note_processed(self, note_data: Dict, output_file: str, is_update: bool = False):
        """标记笔记已处理"""
        note_id = note_data.get('guid') or note_data.get('id')
        title = note_data.get('title', 'Untitled')
        content = note_data.get('content', '')

        if not note_id:
            # 如果没有ID，生成一个基于内容的ID
            note_id = self._calculate_content_hash(content)

        note_info = {
            'note_id': note_id,
            'title': title,
            'content_hash': self._calculate_content_hash(content),
            'output_file': str(output_file),
            'processed_time': datetime.now().isoformat(),
            'migration_id': self.history['last_migration'],
            'is_update': is_update,
            'file_size': Path(output_file).stat().st_size if Path(output_file).exists() else 0
        }

        self.history['processed_notes'][note_id] = note_info
        self._update_migration_stats('updated_notes' if is_update else 'new_notes')

        action = "更新" if is_update else "新建"
        print(f"✅ {action}笔记: {title} -> {Path(output_file).name}")

    def mark_note_skipped(self, note_data: Dict, reason: str):
        """标记笔记已跳过"""
        title = note_data.get('title', 'Untitled')
        self._update_migration_stats('skipped_duplicates')
        print(f"⏭️ 跳过笔记: {title} - {reason}")

    def mark_file_processed(self, file_path: str, content_hash: str = None):
        """标记文件已处理"""
        file_path = Path(file_path)

        if not content_hash and file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                content_hash = self._calculate_content_hash(content)
            except Exception:
                content_hash = str(file_path.stat().st_mtime)

        self.history['processed_files'][content_hash] = str(file_path)

    def finish_migration(self, success: bool = True, error: str = None):
        """完成迁移会话"""
        migration_id = self.history['last_migration']
        if not migration_id:
            return

        # 更新迁移信息
        for migration in self.history['migrations']:
            if migration['migration_id'] == migration_id:
                migration['status'] = 'completed' if success else 'failed'
                migration['end_time'] = datetime.now().isoformat()
                if error:
                    migration['error'] = error
                break

        self._save_history()

        # 打印统计信息
        current_migration = next((m for m in self.history['migrations']
                               if m['migration_id'] == migration_id), None)

        if current_migration:
            stats = current_migration['stats']
            print(f"\n📊 迁移统计 ({migration_id}):")
            print(f"   总计笔记: {stats['total_notes']}")
            print(f"   新建笔记: {stats['new_notes']}")
            print(f"   更新笔记: {stats['updated_notes']}")
            print(f"   跳过重复: {stats['skipped_duplicates']}")

    def get_migration_summary(self) -> Dict:
        """获取迁移摘要"""
        total_migrations = len(self.history['migrations'])
        total_notes = len(self.history['processed_notes'])

        recent_migration = None
        if self.history['migrations']:
            recent_migration = self.history['migrations'][-1]

        return {
            'total_migrations': total_migrations,
            'total_processed_notes': total_notes,
            'recent_migration': recent_migration,
            'deduplication_enabled': True
        }

    def clean_orphaned_files(self, current_files: Set[str]) -> int:
        """清理孤立文件"""
        cleaned_count = 0

        # 检查历史记录中的文件是否仍然存在
        valid_notes = {}
        for note_id, note_info in self.history['processed_notes'].items():
            output_file = note_info.get('output_file')
            if output_file and Path(output_file).exists():
                valid_notes[note_id] = note_info
            else:
                cleaned_count += 1

        if cleaned_count > 0:
            self.history['processed_notes'] = valid_notes
            self._save_history()
            print(f"🧹 清理了 {cleaned_count} 个孤立的文件记录")

        return cleaned_count

    def _calculate_content_hash(self, content: str) -> str:
        """计算内容哈希"""
        # 标准化内容
        normalized = content.strip()
        # 去除多余空行
        normalized = '\n'.join(line.rstrip() for line in normalized.split('\n'))
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()

    def _normalize_title(self, title: str) -> str:
        """标准化标题"""
        return title.strip().lower()

    def _update_migration_stats(self, stat_key: str):
        """更新迁移统计"""
        migration_id = self.history['last_migration']
        if not migration_id:
            return

        for migration in self.history['migrations']:
            if migration['migration_id'] == migration_id:
                migration['stats'][stat_key] += 1
                migration['stats']['total_notes'] += 1
                break

def create_dedup_manager(config: Dict) -> DeduplicationManager:
    """创建去重管理器"""
    output_dir = config.get('output', {}).get('obsidian_vault', '/tmp/obsidian_vault')
    return DeduplicationManager(output_dir)