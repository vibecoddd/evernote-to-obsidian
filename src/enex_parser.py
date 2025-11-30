#!/usr/bin/env python3
"""
ENEX解析器模块 - 印象笔记到Obsidian同步工具
"""

import base64
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field


@dataclass
class Note:
    """笔记数据结构"""
    title: str
    content: str
    created: Optional[datetime] = None
    updated: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    notebook: Optional[str] = None
    source_url: Optional[str] = None
    author: Optional[str] = None
    source: str = "Evernote"
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Resource:
    """资源（附件）数据结构"""
    data: bytes
    mime_type: str
    filename: Optional[str] = None
    hash: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


class ENEXParser:
    """ENEX文件解析器"""

    def __init__(self):
        """初始化解析器"""
        self.namespaces = {
            'en': 'http://xml.evernote.com/pub/enml2.dtd'
        }

    def parse_file(self, enex_path: str) -> Tuple[List[Note], str]:
        """
        解析ENEX文件

        Args:
            enex_path: ENEX文件路径

        Returns:
            元组(笔记列表, 笔记本名称)
        """
        if not os.path.exists(enex_path):
            raise FileNotFoundError(f"ENEX file not found: {enex_path}")

        try:
            tree = ET.parse(enex_path)
            root = tree.getroot()

            # 获取笔记本名称
            notebook_name = self._extract_notebook_name(root)

            # 解析所有笔记
            notes = []
            for note_elem in root.findall('.//note'):
                note = self._parse_note(note_elem)
                note.notebook = notebook_name
                notes.append(note)

            return notes, notebook_name

        except ET.ParseError as e:
            raise ValueError(f"Failed to parse ENEX file {enex_path}: {e}")
        except Exception as e:
            raise Exception(f"Error processing ENEX file {enex_path}: {e}")

    def _extract_notebook_name(self, root: ET.Element) -> str:
        """
        提取笔记本名称

        Args:
            root: XML根元素

        Returns:
            笔记本名称
        """
        # 尝试从export-date属性获取
        notebook_elem = root.find('.//notebook')
        if notebook_elem is not None and notebook_elem.text:
            return self._clean_text(notebook_elem.text)

        # 如果没有找到，使用默认名称
        return "Default Notebook"

    def _parse_note(self, note_elem: ET.Element) -> Note:
        """
        解析单个笔记

        Args:
            note_elem: 笔记XML元素

        Returns:
            笔记对象
        """
        # 提取基本信息
        title = self._get_element_text(note_elem, 'title', 'Untitled Note')
        content = self._get_element_text(note_elem, 'content', '')

        # 提取时间信息
        created = self._parse_datetime(self._get_element_text(note_elem, 'created'))
        updated = self._parse_datetime(self._get_element_text(note_elem, 'updated'))

        # 提取标签
        tags = []
        for tag_elem in note_elem.findall('.//tag'):
            if tag_elem.text:
                tags.append(self._clean_text(tag_elem.text))

        # 提取其他属性
        source_url = self._get_element_text(note_elem, 'source-url')
        author = self._get_element_text(note_elem, 'author')

        # 提取笔记属性
        attributes = self._extract_note_attributes(note_elem)

        # 提取资源（附件）
        attachments = self._extract_resources(note_elem)

        return Note(
            title=self._clean_text(title),
            content=content,
            created=created,
            updated=updated,
            tags=tags,
            source_url=source_url,
            author=author,
            attachments=attachments,
            attributes=attributes
        )

    def _get_element_text(self, parent: ET.Element, tag_name: str, default: str = '') -> str:
        """
        获取子元素文本内容

        Args:
            parent: 父元素
            tag_name: 标签名
            default: 默认值

        Returns:
            元素文本内容
        """
        elem = parent.find(tag_name)
        return elem.text if elem is not None and elem.text else default

    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """
        解析日期时间字符串

        Args:
            date_str: 日期时间字符串

        Returns:
            datetime对象或None
        """
        if not date_str:
            return None

        # Evernote使用的时间格式通常是YYYYMMDDTHHmmssZ
        try:
            # 尝试解析标准格式
            if 'T' in date_str and date_str.endswith('Z'):
                return datetime.strptime(date_str, '%Y%m%dT%H%M%SZ')
            elif 'T' in date_str:
                # 处理带毫秒的格式
                date_str = re.sub(r'\.\d+Z?$', '', date_str)
                return datetime.strptime(date_str, '%Y%m%dT%H%M%S')
            else:
                # 尝试其他格式
                return datetime.strptime(date_str, '%Y%m%d')
        except ValueError:
            # 如果解析失败，返回None
            return None

    def _extract_note_attributes(self, note_elem: ET.Element) -> Dict[str, Any]:
        """
        提取笔记属性

        Args:
            note_elem: 笔记XML元素

        Returns:
            属性字典
        """
        attributes = {}

        # 提取note-attributes
        note_attrs = note_elem.find('note-attributes')
        if note_attrs is not None:
            for child in note_attrs:
                if child.text:
                    attributes[child.tag] = child.text

        return attributes

    def _extract_resources(self, note_elem: ET.Element) -> List[Dict[str, Any]]:
        """
        提取资源（附件）

        Args:
            note_elem: 笔记XML元素

        Returns:
            资源列表
        """
        resources = []

        for resource_elem in note_elem.findall('.//resource'):
            try:
                # 提取资源数据
                data_elem = resource_elem.find('data')
                if data_elem is None or not data_elem.text:
                    continue

                # 解码base64数据
                try:
                    resource_data = base64.b64decode(data_elem.text)
                except Exception:
                    continue

                # 提取MIME类型
                mime_elem = resource_elem.find('mime')
                mime_type = mime_elem.text if mime_elem is not None and mime_elem.text else 'application/octet-stream'

                # 提取文件名
                filename = None
                resource_attrs = resource_elem.find('resource-attributes')
                if resource_attrs is not None:
                    filename_elem = resource_attrs.find('filename')
                    if filename_elem is not None and filename_elem.text:
                        filename = filename_elem.text

                # 如果没有文件名，根据MIME类型生成
                if not filename:
                    extension = self._get_extension_from_mime(mime_type)
                    filename = f"attachment_{len(resources)}{extension}"

                # 提取其他属性
                width = height = None
                if resource_attrs is not None:
                    width_elem = resource_attrs.find('width')
                    height_elem = resource_attrs.find('height')
                    if width_elem is not None and width_elem.text:
                        try:
                            width = int(width_elem.text)
                        except ValueError:
                            pass
                    if height_elem is not None and height_elem.text:
                        try:
                            height = int(height_elem.text)
                        except ValueError:
                            pass

                # 计算哈希值（如果提供）
                hash_elem = resource_elem.find('data').get('encoding') if data_elem else None

                resources.append({
                    'data': resource_data,
                    'mime_type': mime_type,
                    'filename': filename,
                    'size': len(resource_data),
                    'width': width,
                    'height': height,
                    'hash': hash_elem
                })

            except Exception as e:
                print(f"Warning: Failed to extract resource: {e}")
                continue

        return resources

    def _get_extension_from_mime(self, mime_type: str) -> str:
        """
        根据MIME类型获取文件扩展名

        Args:
            mime_type: MIME类型

        Returns:
            文件扩展名
        """
        mime_extensions = {
            'image/jpeg': '.jpg',
            'image/jpg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/bmp': '.bmp',
            'image/svg+xml': '.svg',
            'application/pdf': '.pdf',
            'text/plain': '.txt',
            'text/html': '.html',
            'application/msword': '.doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/vnd.ms-excel': '.xls',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
            'application/zip': '.zip',
            'audio/mpeg': '.mp3',
            'audio/wav': '.wav',
            'video/mp4': '.mp4',
            'video/avi': '.avi'
        }
        return mime_extensions.get(mime_type, '.bin')

    def _clean_text(self, text: str) -> str:
        """
        清理文本内容

        Args:
            text: 原始文本

        Returns:
            清理后的文本
        """
        if not text:
            return ''

        # 移除前后空白字符
        text = text.strip()

        # 移除控制字符
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x84\x86-\x9f]', '', text)

        return text

    def extract_content_with_resources(self, note: Note) -> Tuple[str, Dict[str, str]]:
        """
        提取笔记内容并处理嵌入的资源引用

        Args:
            note: 笔记对象

        Returns:
            元组(处理后的内容, 资源映射字典)
        """
        content = note.content
        resource_map = {}

        # 如果没有资源，直接返回
        if not note.attachments:
            return content, resource_map

        # 创建资源映射
        for i, attachment in enumerate(note.attachments):
            # 生成资源占位符
            placeholder = f"[attachment_{i}]"
            filename = attachment.get('filename', f"attachment_{i}")
            resource_map[placeholder] = filename

        # 替换内容中的资源引用
        # Evernote使用<en-media>标签引用资源
        def replace_media_tag(match):
            hash_attr = match.group(1)
            # 尝试找到对应的资源
            for i, attachment in enumerate(note.attachments):
                if attachment.get('hash') == hash_attr:
                    return f"![{attachment.get('filename', 'attachment')}]({attachment.get('filename')})"
            return f"[Media: {hash_attr}]"

        # 替换en-media标签
        content = re.sub(r'<en-media[^>]*hash="([^"]*)"[^>]*/?>', replace_media_tag, content)

        return content, resource_map


if __name__ == "__main__":
    # 测试解析器
    parser = ENEXParser()
    print("ENEX Parser initialized successfully")