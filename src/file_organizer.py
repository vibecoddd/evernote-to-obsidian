#!/usr/bin/env python3
"""
文件组织器模块 - 印象笔记到Obsidian同步工具
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import hashlib
import json

from enex_parser import Note


class FileOrganizer:
    """文件组织器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化文件组织器

        Args:
            config: 配置字典
        """
        self.config = config
        self.vault_path = Path(config.get('output.obsidian_vault', ''))
        self.attachment_folder = config.get('conversion.image_folder', 'attachments')
        self.created_dirs = set()  # 跟踪已创建的目录

    def organize_notes(self, notes: List[Note], notebook_name: str) -> List[Tuple[Note, str]]:
        """
        组织笔记文件

        Args:
            notes: 笔记列表
            notebook_name: 笔记本名称

        Returns:
            (笔记, 文件路径) 元组列表
        """
        organized_notes = []

        for note in notes:
            file_path = self._determine_file_path(note, notebook_name)
            organized_notes.append((note, file_path))

        return organized_notes

    def _determine_file_path(self, note: Note, notebook_name: str) -> str:
        """
        确定笔记的文件路径

        Args:
            note: 笔记对象
            notebook_name: 笔记本名称

        Returns:
            文件路径
        """
        # 根据配置决定组织方式
        if self.config.get('file_organization.organize_by_notebook', True):
            return self._organize_by_notebook(note, notebook_name)
        elif self.config.get('file_organization.organize_by_tags', False):
            return self._organize_by_tags(note)
        elif self.config.get('file_organization.organize_by_date', False):
            return self._organize_by_date(note)
        else:
            return self._organize_flat(note)

    def _organize_by_notebook(self, note: Note, notebook_name: str) -> str:
        """
        按笔记本组织

        Args:
            note: 笔记对象
            notebook_name: 笔记本名称

        Returns:
            文件路径
        """
        # 清理笔记本名称
        folder_name = self._sanitize_folder_name(notebook_name)

        # 生成文件名
        filename = self._generate_unique_filename(note, folder_name)

        return os.path.join(folder_name, filename)

    def _organize_by_tags(self, note: Note) -> str:
        """
        按标签组织

        Args:
            note: 笔记对象

        Returns:
            文件路径
        """
        if note.tags:
            # 使用第一个标签作为文件夹
            folder_name = self._sanitize_folder_name(note.tags[0])
        else:
            folder_name = "untagged"

        filename = self._generate_unique_filename(note, folder_name)
        return os.path.join(folder_name, filename)

    def _organize_by_date(self, note: Note) -> str:
        """
        按日期组织

        Args:
            note: 笔记对象

        Returns:
            文件路径
        """
        date_format = self.config.get('file_organization.date_folder_format', '%Y/%m')

        if note.created:
            folder_name = note.created.strftime(date_format)
        elif note.updated:
            folder_name = note.updated.strftime(date_format)
        else:
            folder_name = datetime.now().strftime(date_format)

        filename = self._generate_unique_filename(note, folder_name)
        return os.path.join(folder_name, filename)

    def _organize_flat(self, note: Note) -> str:
        """
        平铺组织（所有文件在根目录）

        Args:
            note: 笔记对象

        Returns:
            文件路径
        """
        return self._generate_unique_filename(note, "")

    def _generate_unique_filename(self, note: Note, folder_path: str) -> str:
        """
        生成唯一文件名

        Args:
            note: 笔记对象
            folder_path: 文件夹路径

        Returns:
            唯一文件名
        """
        # 生成基础文件名
        base_name = self._sanitize_filename(note.title or "Untitled Note")
        extension = self.config.get('conversion.markdown_extensions', ['.md'])[0]

        # 处理文件名长度限制
        max_length = self.config.get('conversion.max_filename_length', 100)
        if len(base_name) > max_length - len(extension):
            base_name = base_name[:max_length - len(extension)].strip()

        filename = f"{base_name}{extension}"
        full_path = self.vault_path / folder_path / filename

        # 检查文件名冲突
        duplicate_strategy = self.config.get('file_organization.handle_duplicates', 'rename')

        if full_path.exists():
            if duplicate_strategy == 'skip':
                return str(full_path.relative_to(self.vault_path))
            elif duplicate_strategy == 'overwrite':
                return str(full_path.relative_to(self.vault_path))
            elif duplicate_strategy == 'rename':
                filename = self._get_unique_filename(full_path.parent, base_name, extension)

        return os.path.join(folder_path, filename) if folder_path else filename

    def _get_unique_filename(self, directory: Path, base_name: str, extension: str) -> str:
        """
        获取唯一文件名

        Args:
            directory: 目录路径
            base_name: 基础文件名
            extension: 文件扩展名

        Returns:
            唯一文件名
        """
        counter = 1
        while True:
            filename = f"{base_name}_{counter}{extension}"
            if not (directory / filename).exists():
                return filename
            counter += 1

    def _sanitize_folder_name(self, folder_name: str) -> str:
        """
        清理文件夹名称

        Args:
            folder_name: 原始文件夹名称

        Returns:
            清理后的文件夹名称
        """
        return self._sanitize_filename(folder_name)

    def _sanitize_filename(self, filename: str) -> str:
        """
        清理文件名

        Args:
            filename: 原始文件名

        Returns:
            清理后的文件名
        """
        if not filename:
            return "untitled"

        # 替换无效字符
        invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
        replacement = self.config.get('file_organization.invalid_char_replacement', '_')

        import re
        filename = re.sub(invalid_chars, replacement, filename)

        # 移除前后空格和点
        filename = filename.strip('. ')

        # 处理连续的替换字符
        filename = re.sub(f'{re.escape(replacement)}+', replacement, filename)

        # 确保不为空
        if not filename:
            filename = "untitled"

        return filename

    def create_directory_structure(self, organized_notes: List[Tuple[Note, str]]) -> None:
        """
        创建目录结构

        Args:
            organized_notes: 组织后的笔记列表
        """
        # 确保根目录存在
        if not self.vault_path.exists():
            if self.config.get('output.create_vault_if_not_exists', True):
                self.vault_path.mkdir(parents=True, exist_ok=True)
            else:
                raise Exception(f"Vault directory does not exist: {self.vault_path}")

        # 创建附件目录
        attachment_dir = self.vault_path / self.attachment_folder
        attachment_dir.mkdir(exist_ok=True)
        self.created_dirs.add(str(attachment_dir))

        # 创建笔记目录
        for note, file_path in organized_notes:
            full_path = self.vault_path / file_path
            directory = full_path.parent

            if directory != self.vault_path and str(directory) not in self.created_dirs:
                directory.mkdir(parents=True, exist_ok=True)
                self.created_dirs.add(str(directory))

    def save_note(self, note: Note, file_path: str, content: str) -> str:
        """
        保存笔记文件

        Args:
            note: 笔记对象
            file_path: 文件路径
            content: Markdown内容

        Returns:
            实际保存的文件路径
        """
        full_path = self.vault_path / file_path

        # 备份现有文件
        if full_path.exists() and self.config.get('output.backup_existing', True):
            self._backup_file(full_path)

        # 保存文件
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # 设置文件时间戳
            self._set_file_timestamps(full_path, note)

            return str(full_path.relative_to(self.vault_path))

        except Exception as e:
            raise Exception(f"Failed to save note to {full_path}: {e}")

    def save_attachments(self, note: Note) -> Dict[str, str]:
        """
        保存附件文件

        Args:
            note: 笔记对象

        Returns:
            附件映射字典 {原始文件名: 保存的文件路径}
        """
        attachment_map = {}

        if not note.attachments:
            return attachment_map

        attachment_dir = self.vault_path / self.attachment_folder

        for i, attachment in enumerate(note.attachments):
            try:
                # 确定文件名
                filename = attachment.get('filename', f"attachment_{i}")
                filename = self._sanitize_filename(filename)

                # 确保文件名唯一
                attachment_path = self._get_unique_attachment_path(attachment_dir, filename)

                # 保存文件
                with open(attachment_path, 'wb') as f:
                    f.write(attachment['data'])

                # 记录映射
                relative_path = attachment_path.relative_to(self.vault_path)
                attachment_map[attachment.get('filename', filename)] = str(relative_path)

            except Exception as e:
                print(f"Warning: Failed to save attachment {attachment.get('filename', 'unknown')}: {e}")

        return attachment_map

    def _get_unique_attachment_path(self, directory: Path, filename: str) -> Path:
        """
        获取唯一附件路径

        Args:
            directory: 目录路径
            filename: 文件名

        Returns:
            唯一文件路径
        """
        base_path = directory / filename

        if not base_path.exists():
            return base_path

        # 分离文件名和扩展名
        name = base_path.stem
        suffix = base_path.suffix

        counter = 1
        while True:
            new_filename = f"{name}_{counter}{suffix}"
            new_path = directory / new_filename
            if not new_path.exists():
                return new_path
            counter += 1

    def _backup_file(self, file_path: Path) -> None:
        """
        备份现有文件

        Args:
            file_path: 文件路径
        """
        if not file_path.exists():
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{file_path.stem}_{timestamp}_backup{file_path.suffix}"
        backup_path = file_path.parent / backup_name

        try:
            shutil.copy2(file_path, backup_path)
        except Exception as e:
            print(f"Warning: Failed to backup file {file_path}: {e}")

    def _set_file_timestamps(self, file_path: Path, note: Note) -> None:
        """
        设置文件时间戳

        Args:
            file_path: 文件路径
            note: 笔记对象
        """
        try:
            # 设置创建时间和修改时间
            if note.created:
                created_timestamp = note.created.timestamp()
                os.utime(file_path, (created_timestamp, created_timestamp))

            if note.updated:
                updated_timestamp = note.updated.timestamp()
                os.utime(file_path, (file_path.stat().st_atime, updated_timestamp))

        except Exception as e:
            print(f"Warning: Failed to set timestamps for {file_path}: {e}")

    def create_index_file(self, organized_notes: List[Tuple[Note, str]], notebook_name: str) -> None:
        """
        创建索引文件

        Args:
            organized_notes: 组织后的笔记列表
            notebook_name: 笔记本名称
        """
        try:
            index_content = self._generate_index_content(organized_notes, notebook_name)
            index_path = self.vault_path / f"{self._sanitize_filename(notebook_name)}_Index.md"

            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(index_content)

        except Exception as e:
            print(f"Warning: Failed to create index file: {e}")

    def _generate_index_content(self, organized_notes: List[Tuple[Note, str]], notebook_name: str) -> str:
        """
        生成索引内容

        Args:
            organized_notes: 组织后的笔记列表
            notebook_name: 笔记本名称

        Returns:
            索引内容
        """
        lines = [
            f"# {notebook_name} - 笔记索引",
            "",
            f"导入时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"笔记总数: {len(organized_notes)}",
            "",
            "## 笔记列表",
            ""
        ]

        # 按文件夹分组
        folders = {}
        for note, file_path in organized_notes:
            folder = os.path.dirname(file_path) or "根目录"
            if folder not in folders:
                folders[folder] = []
            folders[folder].append((note, file_path))

        # 生成目录结构
        for folder, notes in sorted(folders.items()):
            if folder != "根目录":
                lines.append(f"### {folder}")
            else:
                lines.append(f"### 根目录")

            for note, file_path in sorted(notes, key=lambda x: x[0].title or ""):
                title = note.title or "无标题"
                link = f"[[{os.path.splitext(os.path.basename(file_path))[0]}]]"

                # 添加标签信息
                tags_info = ""
                if note.tags:
                    tags_info = f" #{' #'.join(note.tags)}"

                lines.append(f"- {link} - {title}{tags_info}")

            lines.append("")

        return "\n".join(lines)

    def get_statistics(self, organized_notes: List[Tuple[Note, str]]) -> Dict[str, Any]:
        """
        获取统计信息

        Args:
            organized_notes: 组织后的笔记列表

        Returns:
            统计信息字典
        """
        total_notes = len(organized_notes)
        total_attachments = sum(len(note.attachments) for note, _ in organized_notes)

        # 按文件夹统计
        folder_stats = {}
        for note, file_path in organized_notes:
            folder = os.path.dirname(file_path) or "根目录"
            if folder not in folder_stats:
                folder_stats[folder] = 0
            folder_stats[folder] += 1

        # 按标签统计
        tag_stats = {}
        for note, _ in organized_notes:
            for tag in note.tags:
                tag_stats[tag] = tag_stats.get(tag, 0) + 1

        return {
            'total_notes': total_notes,
            'total_attachments': total_attachments,
            'folders': folder_stats,
            'tags': tag_stats,
            'created_directories': len(self.created_dirs)
        }


if __name__ == "__main__":
    # 测试文件组织器
    config = {
        'output': {
            'obsidian_vault': './test_vault',
            'create_vault_if_not_exists': True
        },
        'file_organization': {
            'organize_by_notebook': True,
            'handle_duplicates': 'rename'
        },
        'conversion': {
            'image_folder': 'attachments'
        }
    }

    organizer = FileOrganizer(config)
    print("File Organizer initialized successfully")