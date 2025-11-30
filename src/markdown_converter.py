#!/usr/bin/env python3
"""
Markdown转换器模块 - 印象笔记到Obsidian同步工具
"""

import html2text
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from enex_parser import Note


class MarkdownConverter:
    """HTML到Markdown转换器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化转换器

        Args:
            config: 配置字典
        """
        self.config = config
        self.h2t = self._setup_html2text()

    def _setup_html2text(self) -> html2text.HTML2Text:
        """
        设置html2text转换器

        Returns:
            配置好的html2text实例
        """
        h = html2text.HTML2Text()

        # 基础配置
        h.ignore_links = not self.config.get('conversion.convert_links', True)
        h.ignore_images = False
        h.ignore_tables = not self.config.get('conversion.convert_tables', True)
        h.body_width = 0  # 不限制行宽
        h.unicode_snob = True  # 使用Unicode字符
        h.escape_snob = True  # 转义特殊字符

        # 高级配置
        h.mark_code = True
        h.wrap_links = False
        h.single_line_break = False
        h.emphasis_mark = '*'
        h.strong_mark = '**'

        return h

    def convert_note(self, note: Note) -> str:
        """
        转换笔记为Markdown格式

        Args:
            note: 笔记对象

        Returns:
            Markdown格式的笔记内容
        """
        # 生成前言（frontmatter）
        frontmatter = self._generate_frontmatter(note)

        # 转换主要内容
        content = self._convert_content(note.content)

        # 后处理内容
        content = self._post_process_content(content)

        # 组合完整内容
        if frontmatter:
            return f"---\n{frontmatter}\n---\n\n{content}"
        else:
            return content

    def _generate_frontmatter(self, note: Note) -> str:
        """
        生成YAML前言

        Args:
            note: 笔记对象

        Returns:
            YAML前言字符串
        """
        if not any([
            self.config.get('metadata.include_created_date'),
            self.config.get('metadata.include_modified_date'),
            self.config.get('metadata.include_tags'),
            self.config.get('metadata.include_notebook'),
            self.config.get('metadata.include_source')
        ]):
            return ""

        frontmatter_lines = []
        date_format = self.config.get('metadata.date_format', '%Y-%m-%d %H:%M:%S')

        # 添加标题
        if note.title:
            frontmatter_lines.append(f'title: "{self._escape_yaml_string(note.title)}"')

        # 添加创建日期
        if self.config.get('metadata.include_created_date') and note.created:
            frontmatter_lines.append(f'created: "{note.created.strftime(date_format)}"')

        # 添加修改日期
        if self.config.get('metadata.include_modified_date') and note.updated:
            frontmatter_lines.append(f'updated: "{note.updated.strftime(date_format)}"')

        # 添加标签
        if self.config.get('metadata.include_tags') and note.tags:
            tags_str = ', '.join([f'"{tag}"' for tag in note.tags])
            frontmatter_lines.append(f'tags: [{tags_str}]')

        # 添加笔记本信息
        if self.config.get('metadata.include_notebook') and note.notebook:
            frontmatter_lines.append(f'notebook: "{self._escape_yaml_string(note.notebook)}"')

        # 添加来源信息
        if self.config.get('metadata.include_source'):
            frontmatter_lines.append(f'source: "{note.source}"')

        # 添加作者
        if note.author:
            frontmatter_lines.append(f'author: "{self._escape_yaml_string(note.author)}"')

        # 添加源URL
        if note.source_url:
            frontmatter_lines.append(f'source_url: "{note.source_url}"')

        # 添加附件信息
        if note.attachments:
            frontmatter_lines.append(f'attachments: {len(note.attachments)}')

        return '\n'.join(frontmatter_lines)

    def _escape_yaml_string(self, text: str) -> str:
        """
        转义YAML字符串

        Args:
            text: 原始文本

        Returns:
            转义后的文本
        """
        if not text:
            return ""

        # 转义双引号
        text = text.replace('"', '\\"')
        return text

    def _convert_content(self, content: str) -> str:
        """
        转换HTML内容为Markdown

        Args:
            content: HTML内容

        Returns:
            Markdown内容
        """
        if not content:
            return ""

        # 预处理HTML内容
        content = self._preprocess_html(content)

        # 转换为Markdown
        try:
            markdown_content = self.h2t.handle(content)
        except Exception as e:
            print(f"Warning: HTML to Markdown conversion failed: {e}")
            # 如果转换失败，返回清理后的纯文本
            markdown_content = self._extract_plain_text(content)

        return markdown_content

    def _preprocess_html(self, content: str) -> str:
        """
        预处理HTML内容

        Args:
            content: 原始HTML内容

        Returns:
            预处理后的HTML内容
        """
        if not content:
            return ""

        # 移除Evernote特有的标签和属性
        content = self._remove_evernote_tags(content)

        # 处理特殊字符
        content = self._normalize_characters(content)

        # 处理嵌套的HTML结构
        content = self._fix_nested_tags(content)

        # 清理无效的HTML
        if self.config.get('conversion.clean_html', True):
            content = self._clean_html(content)

        return content

    def _remove_evernote_tags(self, content: str) -> str:
        """
        移除Evernote特有的标签

        Args:
            content: HTML内容

        Returns:
            清理后的HTML内容
        """
        # 移除en-note根标签
        content = re.sub(r'<en-note[^>]*>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'</en-note>', '', content, flags=re.IGNORECASE)

        # 移除en-media标签（已在解析时处理）
        content = re.sub(r'<en-media[^>]*/?>', '[Media]', content, flags=re.IGNORECASE)

        # 移除en-todo标签并转换为Markdown复选框
        content = re.sub(r'<en-todo\s+checked="true"[^>]*/?>', '- [x] ', content, flags=re.IGNORECASE)
        content = re.sub(r'<en-todo[^>]*/?>', '- [ ] ', content, flags=re.IGNORECASE)

        # 移除Evernote特有的属性
        content = re.sub(r'\s+style="[^"]*"', '', content, flags=re.IGNORECASE)
        content = re.sub(r'\s+class="en-[^"]*"', '', content, flags=re.IGNORECASE)

        return content

    def _normalize_characters(self, content: str) -> str:
        """
        标准化字符

        Args:
            content: 内容

        Returns:
            标准化后的内容
        """
        # 替换特殊空格字符
        content = content.replace('\u00a0', ' ')  # 不间断空格
        content = content.replace('\u2008', ' ')  # 标点符号空格

        # 标准化换行符
        content = content.replace('\r\n', '\n').replace('\r', '\n')

        # 移除零宽度字符
        content = re.sub(r'[\u200b-\u200f\ufeff]', '', content)

        return content

    def _fix_nested_tags(self, content: str) -> str:
        """
        修复嵌套标签问题

        Args:
            content: HTML内容

        Returns:
            修复后的HTML内容
        """
        # 修复嵌套的div标签
        content = re.sub(r'<div[^>]*>\s*<div[^>]*>', '<div>', content, flags=re.IGNORECASE)
        content = re.sub(r'</div>\s*</div>', '</div>', content, flags=re.IGNORECASE)

        # 修复空的段落标签
        content = re.sub(r'<p[^>]*>\s*</p>', '', content, flags=re.IGNORECASE)

        return content

    def _clean_html(self, content: str) -> str:
        """
        清理HTML内容

        Args:
            content: HTML内容

        Returns:
            清理后的HTML内容
        """
        # 移除注释
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)

        # 移除空属性
        content = re.sub(r'\s+\w+=""', '', content)

        # 移除多余的空白字符
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'>\s+<', '><', content)

        return content.strip()

    def _extract_plain_text(self, content: str) -> str:
        """
        提取纯文本内容

        Args:
            content: HTML内容

        Returns:
            纯文本内容
        """
        # 移除所有HTML标签
        text = re.sub(r'<[^>]+>', '', content)

        # 解码HTML实体
        import html
        text = html.unescape(text)

        # 标准化空白字符
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def _post_process_content(self, content: str) -> str:
        """
        后处理Markdown内容

        Args:
            content: Markdown内容

        Returns:
            后处理后的内容
        """
        if not content:
            return ""

        # 修复链接格式
        content = self._fix_links(content)

        # 修复图片引用
        content = self._fix_images(content)

        # 修复表格格式
        content = self._fix_tables(content)

        # 修复代码块
        content = self._fix_code_blocks(content)

        # 清理多余的空行
        content = self._clean_empty_lines(content)

        # 修复列表格式
        content = self._fix_lists(content)

        return content

    def _fix_links(self, content: str) -> str:
        """
        修复链接格式

        Args:
            content: Markdown内容

        Returns:
            修复后的内容
        """
        # 修复破损的链接
        content = re.sub(r'\[([^\]]*)\]\(\)', r'\1', content)

        # 修复重复的链接文本
        content = re.sub(r'\[([^\]]+)\]\(\1\)', r'[\1](\1)', content)

        return content

    def _fix_images(self, content: str) -> str:
        """
        修复图片引用

        Args:
            content: Markdown内容

        Returns:
            修复后的内容
        """
        # 转换为Obsidian风格的图片引用
        image_folder = self.config.get('conversion.image_folder', 'attachments')

        def fix_image_path(match):
            alt_text = match.group(1) or 'image'
            filename = match.group(2)

            # 如果路径不是绝对路径，添加附件文件夹前缀
            if not filename.startswith(('http://', 'https://', '/')):
                filename = f"{image_folder}/{filename}"

            return f"![[{filename}]]"

        content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', fix_image_path, content)

        return content

    def _fix_tables(self, content: str) -> str:
        """
        修复表格格式

        Args:
            content: Markdown内容

        Returns:
            修复后的内容
        """
        # 确保表格前后有空行
        content = re.sub(r'([^\n])\n(\|.*\|)', r'\1\n\n\2', content)
        content = re.sub(r'(\|.*\|)\n([^\n|])', r'\1\n\n\2', content)

        return content

    def _fix_code_blocks(self, content: str) -> str:
        """
        修复代码块格式

        Args:
            content: Markdown内容

        Returns:
            修复后的内容
        """
        # 确保代码块前后有空行
        content = re.sub(r'([^\n])\n(```)', r'\1\n\n\2', content)
        content = re.sub(r'(```)\n([^\n])', r'\1\n\n\2', content)

        return content

    def _fix_lists(self, content: str) -> str:
        """
        修复列表格式

        Args:
            content: Markdown内容

        Returns:
            修复后的内容
        """
        # 修复列表项之间的空行
        content = re.sub(r'(\n[-*+]\s+[^\n]+)\n\n(\n[-*+]\s+)', r'\1\n\2', content)

        # 确保列表前后有空行
        content = re.sub(r'([^\n])\n([-*+]\s+)', r'\1\n\n\2', content)
        content = re.sub(r'([-*+]\s+[^\n]+)\n([^\n-*+\s])', r'\1\n\n\2', content)

        return content

    def _clean_empty_lines(self, content: str) -> str:
        """
        清理多余的空行

        Args:
            content: 内容

        Returns:
            清理后的内容
        """
        # 移除3个以上连续的空行
        content = re.sub(r'\n\s*\n\s*\n\s*\n+', '\n\n\n', content)

        # 移除开头和结尾的空行
        content = content.strip()

        return content

    def generate_filename(self, note: Note) -> str:
        """
        生成文件名

        Args:
            note: 笔记对象

        Returns:
            文件名
        """
        # 使用笔记标题作为基础
        filename = note.title or "Untitled Note"

        # 清理文件名中的无效字符
        filename = self._sanitize_filename(filename)

        # 限制文件名长度
        max_length = self.config.get('conversion.max_filename_length', 100)
        if len(filename) > max_length:
            filename = filename[:max_length].strip()

        # 添加扩展名
        extensions = self.config.get('conversion.markdown_extensions', ['.md'])
        extension = extensions[0] if extensions else '.md'

        return f"{filename}{extension}"

    def _sanitize_filename(self, filename: str) -> str:
        """
        清理文件名

        Args:
            filename: 原始文件名

        Returns:
            清理后的文件名
        """
        # 定义无效字符
        invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
        replacement = self.config.get('file_organization.invalid_char_replacement', '_')

        # 替换无效字符
        filename = re.sub(invalid_chars, replacement, filename)

        # 移除前后空格和点
        filename = filename.strip('. ')

        # 确保不为空
        if not filename:
            filename = "untitled"

        return filename


if __name__ == "__main__":
    # 测试转换器
    config = {
        'conversion': {
            'convert_links': True,
            'convert_tables': True,
            'clean_html': True,
            'max_filename_length': 100
        },
        'metadata': {
            'include_created_date': True,
            'include_tags': True
        }
    }

    converter = MarkdownConverter(config)
    print("Markdown Converter initialized successfully")