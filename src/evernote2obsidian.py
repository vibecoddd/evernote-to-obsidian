#!/usr/bin/env python3
"""
印象笔记到Obsidian同步工具 - 主程序入口
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Optional, Tuple
import logging
import click
from tqdm import tqdm
import colorama
from colorama import Fore, Back, Style

# 添加源文件目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from enex_parser import ENEXParser, Note
from markdown_converter import MarkdownConverter
from file_organizer import FileOrganizer
from sync_manager import SyncManager


class EvernoteToObsidianConverter:
    """印象笔记到Obsidian转换器主类"""

    def __init__(self, config_path: Optional[str] = None,
                 config: Optional[Config] = None):
        """
        初始化转换器

        Args:
            config_path: 配置文件路径
            config: 已构造的配置对象；与config_path二选一
        """
        # 初始化colorama（用于彩色输出）
        colorama.init(autoreset=True)

        # 加载配置
        if config is not None and config_path is not None:
            raise ValueError("config_path and config cannot be used together")

        self.config = config if config is not None else Config(config_path)
        if not self.config.validate():
            raise ValueError("Configuration validation failed")

        # 设置日志
        self._setup_logging()

        # 初始化组件
        self.parser = ENEXParser()
        self.converter = MarkdownConverter(self.config.get_all())
        self.organizer = FileOrganizer(self.config.get_all())
        self.sync_manager = SyncManager(self.config.get_all())

        self.logger = logging.getLogger(__name__)

    def _setup_logging(self) -> None:
        """设置日志配置"""
        log_level = self.config.get('logging.level', 'INFO')
        log_format = self.config.get('logging.format',
                                   '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        log_file = self.config.get('logging.file', 'evernote2obsidian.log')
        console_output = self.config.get('logging.console', True)

        # 设置根日志记录器
        logging.basicConfig(
            level=getattr(logging, log_level),
            format=log_format
        )

        logger = logging.getLogger()
        logger.handlers.clear()

        # 文件处理器
        if log_file:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(logging.Formatter(log_format))
            logger.addHandler(file_handler)

        # 控制台处理器
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(log_format))
            logger.addHandler(console_handler)

    def run(self, preview: bool = False) -> Tuple[bool, dict]:
        """
        运行转换过程

        Args:
            preview: 是否为预览模式

        Returns:
            (是否成功, 统计信息)
        """
        try:
            self.logger.info("开始印象笔记到Obsidian转换")

            # 获取输入文件
            enex_files = self._get_input_files()
            if not enex_files:
                self.logger.error("没有找到ENEX文件")
                return False, {}

            self._print_header()
            print(f"{Fore.CYAN}发现 {len(enex_files)} 个ENEX文件")

            if preview:
                return self._run_preview(enex_files)
            else:
                return self._run_conversion(enex_files)

        except KeyboardInterrupt:
            self.logger.info("用户取消操作")
            print(f"{Fore.YELLOW}操作已取消")
            return False, {}
        except Exception as e:
            self.logger.error(f"转换失败: {e}")
            print(f"{Fore.RED}转换失败: {e}")
            return False, {}

    def _get_input_files(self) -> List[str]:
        """
        获取输入文件列表

        Returns:
            ENEX文件路径列表
        """
        enex_files = []

        # 从配置获取文件列表
        config_files = self.config.get('input.enex_files', [])
        for file_path in config_files:
            if os.path.exists(file_path) and file_path.endswith('.enex'):
                enex_files.append(file_path)

        # 从目录获取文件
        input_dir = self.config.get('input.input_directory')
        if input_dir and os.path.exists(input_dir):
            for file_path in Path(input_dir).glob('*.enex'):
                if str(file_path) not in enex_files:
                    enex_files.append(str(file_path))

        return sorted(enex_files)

    def _run_preview(self, enex_files: List[str]) -> Tuple[bool, dict]:
        """
        运行预览模式

        Args:
            enex_files: ENEX文件列表

        Returns:
            (是否成功, 统计信息)
        """
        print(f"{Fore.YELLOW}=== 预览模式 ===")

        total_notes = 0
        preview_info = {
            'files': [],
            'notebooks': {},
            'total_notes': 0,
            'total_attachments': 0
        }

        for enex_file in enex_files:
            try:
                print(f"{Fore.BLUE}分析文件: {os.path.basename(enex_file)}")
                notes, notebook_name = self.parser.parse_file(enex_file)

                file_info = {
                    'file': enex_file,
                    'notebook': notebook_name,
                    'note_count': len(notes),
                    'attachment_count': sum(len(note.attachments) for note in notes)
                }

                preview_info['files'].append(file_info)
                preview_info['notebooks'][notebook_name] = len(notes)
                preview_info['total_notes'] += len(notes)
                preview_info['total_attachments'] += file_info['attachment_count']

                print(f"  📔 笔记本: {notebook_name}")
                print(f"  📄 笔记数: {len(notes)}")
                print(f"  📎 附件数: {file_info['attachment_count']}")

            except Exception as e:
                print(f"{Fore.RED}  ❌ 分析失败: {e}")

        self._print_preview_summary(preview_info)
        return True, preview_info

    def _run_conversion(self, enex_files: List[str]) -> Tuple[bool, dict]:
        """
        运行实际转换

        Args:
            enex_files: ENEX文件列表

        Returns:
            (是否成功, 统计信息)
        """
        print(f"{Fore.GREEN}=== 开始转换 ===")

        total_notes = 0
        total_converted = 0
        total_skipped = 0
        processed_files = []

        # 总进度条
        with tqdm(total=len(enex_files), desc="处理文件",
                 bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} files") as pbar:

            for enex_file in enex_files:
                try:
                    # 检查是否需要处理此文件
                    if not self.sync_manager.should_process_file(enex_file):
                        self.logger.info(f"跳过未更改的文件: {enex_file}")
                        pbar.set_postfix({"状态": "跳过"})
                        pbar.update(1)
                        continue

                    self.logger.info(f"处理文件: {enex_file}")
                    pbar.set_postfix({"文件": os.path.basename(enex_file)})

                    # 解析ENEX文件
                    notes, notebook_name = self.parser.parse_file(enex_file)
                    total_notes += len(notes)

                    # 过滤需要同步的笔记
                    notes_to_sync = self.sync_manager.filter_notes_for_sync(notes)
                    skipped_count = len(notes) - len(notes_to_sync)
                    total_skipped += skipped_count

                    if not notes_to_sync:
                        self.logger.info(f"文件 {enex_file} 中的所有笔记都已同步，跳过")
                        self.sync_manager.mark_file_processed(enex_file)
                        pbar.update(1)
                        continue

                    # 转换笔记
                    converted_count = self._convert_notes(notes_to_sync, notebook_name,
                                                        pbar, len(notes_to_sync))
                    total_converted += converted_count

                    # 标记文件已处理
                    self.sync_manager.mark_file_processed(enex_file)
                    processed_files.append(enex_file)

                except Exception as e:
                    self.logger.error(f"处理文件 {enex_file} 失败: {e}")
                    print(f"{Fore.RED}❌ 文件处理失败: {os.path.basename(enex_file)}")

                pbar.update(1)

        # 完成同步
        self.sync_manager.finalize_sync(total_converted)

        # 生成统计信息
        statistics = {
            'total_files': len(enex_files),
            'processed_files': len(processed_files),
            'total_notes': total_notes,
            'converted_notes': total_converted,
            'skipped_notes': total_skipped
        }

        self._print_conversion_summary(statistics)

        # 生成同步报告
        if processed_files:
            report = self.sync_manager.create_sync_report(
                processed_files, total_notes, total_skipped)
            report_path = self.sync_manager.save_sync_report(report)
            if report_path:
                print(f"{Fore.CYAN}📊 同步报告已保存: {report_path}")

        return total_converted > 0, statistics

    def _convert_notes(self, notes: List[Note], notebook_name: str,
                      pbar: tqdm, total: int) -> int:
        """
        转换笔记列表

        Args:
            notes: 笔记列表
            notebook_name: 笔记本名称
            pbar: 进度条
            total: 总数

        Returns:
            转换的笔记数量
        """
        # 组织笔记文件结构
        organized_notes = self.organizer.organize_notes(notes, notebook_name)

        # 创建目录结构
        self.organizer.create_directory_structure(organized_notes)

        converted_count = 0

        # 转换每个笔记
        for note, file_path in organized_notes:
            try:
                # 转换为Markdown
                markdown_content = self.converter.convert_note(note)

                # 保存笔记
                actual_path = self.organizer.save_note(note, file_path, markdown_content)

                # 保存附件
                if note.attachments:
                    self.organizer.save_attachments(note)

                # 标记笔记已处理
                self.sync_manager.mark_note_processed(note, actual_path)

                converted_count += 1
                self.logger.debug(f"转换完成: {note.title}")

            except Exception as e:
                self.logger.error(f"转换笔记失败 {note.title}: {e}")

        # 创建索引文件
        if organized_notes:
            self.organizer.create_index_file(organized_notes, notebook_name)

        return converted_count

    def _print_header(self) -> None:
        """打印程序头部信息"""
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}🔄 印象笔记到Obsidian同步工具")
        print(f"{Fore.CYAN}{'='*60}")

    def _print_preview_summary(self, info: dict) -> None:
        """
        打印预览摘要

        Args:
            info: 预览信息
        """
        print(f"\n{Fore.YELLOW}=== 预览摘要 ===")
        print(f"📁 文件总数: {len(info['files'])}")
        print(f"📔 笔记本数: {len(info['notebooks'])}")
        print(f"📄 笔记总数: {info['total_notes']}")
        print(f"📎 附件总数: {info['total_attachments']}")

        print(f"\n{Fore.BLUE}笔记本分布:")
        for notebook, count in info['notebooks'].items():
            print(f"  📔 {notebook}: {count} 篇笔记")

    def _print_conversion_summary(self, stats: dict) -> None:
        """
        打印转换摘要

        Args:
            stats: 统计信息
        """
        print(f"\n{Fore.GREEN}=== 转换完成 ===")
        print(f"📁 处理文件: {stats['processed_files']}/{stats['total_files']}")
        print(f"✅ 转换笔记: {stats['converted_notes']}")
        print(f"⏭️ 跳过笔记: {stats['skipped_notes']}")
        print(f"📊 总计笔记: {stats['total_notes']}")

        if stats['converted_notes'] > 0:
            print(f"\n{Fore.CYAN}🎉 转换成功! 请在Obsidian中查看您的笔记。")
        elif stats['skipped_notes'] > 0:
            print(f"\n{Fore.YELLOW}ℹ️ 所有笔记都已同步，无需更新。")


# CLI命令行界面
@click.command()
@click.option('--config', '-c', type=click.Path(exists=True),
              help='配置文件路径')
@click.option('--input', '-i', type=click.Path(),
              help='输入ENEX文件或目录路径')
@click.option('--output', '-o', type=click.Path(),
              help='输出Obsidian库路径')
@click.option('--preview', '-p', is_flag=True,
              help='预览模式，只显示将要处理的内容')
@click.option('--reset', is_flag=True,
              help='重置同步状态')
@click.option('--verbose', '-v', is_flag=True,
              help='详细输出')
def main(config, input, output, preview, reset, verbose):
    """
    印象笔记到Obsidian同步工具

    将印象笔记的ENEX文件转换为Obsidian兼容的Markdown格式，
    保持原有的文件夹结构和附件。
    """
    try:
        # 创建配置对象
        converter_config = Config(config)

        # 应用命令行参数
        if input:
            if os.path.isfile(input):
                converter_config.set('input.enex_files', [input])
            else:
                converter_config.set('input.input_directory', input)

        if output:
            converter_config.set('output.obsidian_vault', output)

        if verbose:
            converter_config.set('logging.level', 'DEBUG')

        # 创建转换器
        converter = EvernoteToObsidianConverter(config=converter_config)

        # 重置同步状态
        if reset:
            converter.sync_manager.reset_sync_state()
            print(f"{Fore.GREEN}✅ 同步状态已重置")
            return

        # 运行转换
        success, stats = converter.run(preview=preview)

        if success:
            sys.exit(0)
        else:
            sys.exit(1)

    except Exception as e:
        print(f"{Fore.RED}❌ 程序错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
