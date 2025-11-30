#!/usr/bin/env python3
"""
配置管理模块 - 印象笔记到Obsidian同步工具
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

class Config:
    """配置管理类"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置

        Args:
            config_path: 配置文件路径，如果为None则使用默认配置
        """
        self.config_data = self._load_default_config()

        if config_path and os.path.exists(config_path):
            self._load_config_file(config_path)

    def _load_default_config(self) -> Dict[str, Any]:
        """加载默认配置"""
        return {
            'input': {
                'enex_files': [],  # ENEX文件路径列表
                'input_directory': '',  # 输入目录
                'encoding': 'utf-8'  # 文件编码
            },
            'output': {
                'obsidian_vault': '',  # Obsidian库路径
                'create_vault_if_not_exists': True,  # 如果库不存在则创建
                'backup_existing': True,  # 备份现有文件
                'overwrite_existing': False  # 是否覆盖现有文件
            },
            'conversion': {
                'preserve_html_tags': False,  # 是否保留HTML标签
                'convert_tables': True,  # 是否转换表格
                'convert_links': True,  # 是否转换链接
                'extract_images': True,  # 是否提取图片
                'image_folder': 'attachments',  # 图片存储文件夹
                'max_filename_length': 100,  # 最大文件名长度
                'clean_html': True,  # 是否清理HTML
                'markdown_extensions': ['.md']  # Markdown文件扩展名
            },
            'metadata': {
                'include_created_date': True,  # 包含创建日期
                'include_modified_date': True,  # 包含修改日期
                'include_tags': True,  # 包含标签
                'include_notebook': True,  # 包含笔记本信息
                'include_source': True,  # 包含来源信息
                'date_format': '%Y-%m-%d %H:%M:%S',  # 日期格式
                'frontmatter_style': 'yaml'  # 前言样式(yaml/json)
            },
            'file_organization': {
                'organize_by_notebook': True,  # 按笔记本组织
                'organize_by_tags': False,  # 按标签组织
                'organize_by_date': False,  # 按日期组织
                'date_folder_format': '%Y/%m',  # 日期文件夹格式
                'handle_duplicates': 'rename',  # 处理重复文件(rename/skip/overwrite)
                'invalid_char_replacement': '_',  # 无效字符替换
                'max_folder_depth': 10  # 最大文件夹深度
            },
            'logging': {
                'level': 'INFO',  # 日志级别
                'file': 'evernote2obsidian.log',  # 日志文件
                'console': True,  # 是否输出到控制台
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
            'sync': {
                'incremental': True,  # 增量同步
                'state_file': '.sync_state.json',  # 同步状态文件
                'check_modification_time': True,  # 检查修改时间
                'skip_unchanged': True  # 跳过未更改的文件
            },
            'advanced': {
                'parallel_processing': False,  # 并行处理
                'max_workers': 4,  # 最大工作进程数
                'chunk_size': 100,  # 处理块大小
                'memory_limit': '1GB',  # 内存限制
                'temp_directory': ''  # 临时目录
            }
        }

    def _load_config_file(self, config_path: str) -> None:
        """
        从文件加载配置

        Args:
            config_path: 配置文件路径
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = yaml.safe_load(f)
                if file_config:
                    self._merge_config(self.config_data, file_config)
        except Exception as e:
            print(f"Warning: Failed to load config file {config_path}: {e}")

    def _merge_config(self, default: Dict[str, Any], override: Dict[str, Any]) -> None:
        """
        合并配置

        Args:
            default: 默认配置
            override: 覆盖配置
        """
        for key, value in override.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                self._merge_config(default[key], value)
            else:
                default[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键，支持点号分隔的嵌套键(如 'input.encoding')
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config_data

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """
        设置配置值

        Args:
            key: 配置键，支持点号分隔的嵌套键
            value: 配置值
        """
        keys = key.split('.')
        target = self.config_data

        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]

        target[keys[-1]] = value

    def save(self, config_path: str) -> None:
        """
        保存配置到文件

        Args:
            config_path: 配置文件路径
        """
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config_data, f, default_flow_style=False,
                         allow_unicode=True, indent=2)
        except Exception as e:
            raise Exception(f"Failed to save config to {config_path}: {e}")

    def validate(self) -> bool:
        """
        验证配置

        Returns:
            是否有效
        """
        errors = []

        # 检查必要的路径配置
        if not self.get('input.enex_files') and not self.get('input.input_directory'):
            errors.append("Either input.enex_files or input.input_directory must be specified")

        if not self.get('output.obsidian_vault'):
            errors.append("output.obsidian_vault must be specified")

        # 检查文件路径是否存在
        input_dir = self.get('input.input_directory')
        if input_dir and not os.path.exists(input_dir):
            errors.append(f"Input directory does not exist: {input_dir}")

        for enex_file in self.get('input.enex_files', []):
            if not os.path.exists(enex_file):
                errors.append(f"ENEX file does not exist: {enex_file}")

        # 检查输出路径
        vault_path = self.get('output.obsidian_vault')
        if vault_path:
            vault_dir = os.path.dirname(vault_path) if os.path.isfile(vault_path) else vault_path
            if not os.path.exists(vault_dir) and not self.get('output.create_vault_if_not_exists'):
                errors.append(f"Output directory does not exist and create_vault_if_not_exists is False: {vault_dir}")

        if errors:
            print("Configuration validation errors:")
            for error in errors:
                print(f"  - {error}")
            return False

        return True

    def get_all(self) -> Dict[str, Any]:
        """
        获取所有配置

        Returns:
            完整配置字典
        """
        return self.config_data.copy()

    def update(self, updates: Dict[str, Any]) -> None:
        """
        批量更新配置

        Args:
            updates: 更新的配置字典
        """
        self._merge_config(self.config_data, updates)


def create_default_config(output_path: str) -> None:
    """
    创建默认配置文件

    Args:
        output_path: 输出路径
    """
    config = Config()
    config.save(output_path)
    print(f"Default configuration created at: {output_path}")


if __name__ == "__main__":
    # 创建示例配置文件
    example_config_path = "../config.yaml"
    create_default_config(example_config_path)
    print("Example configuration file created.")