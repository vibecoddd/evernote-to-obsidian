#!/usr/bin/env python3
"""
一键式印象笔记到Obsidian迁移工具
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import tempfile
import shutil

import click
from tqdm import tqdm
import colorama
from colorama import Fore, Style

from config import Config
from evernote_exporter import EvernoteExporter
from enex_parser import ENEXParser
from markdown_converter import MarkdownConverter
from file_organizer import FileOrganizer
from sync_manager import SyncManager
from obsidian_manager import ObsidianManager


class UnifiedMigrator:
    """一键式迁移工具"""

    def __init__(self):
        """初始化迁移工具"""
        colorama.init(autoreset=True)
        self.config = None
        self.stats = {
            'start_time': None,
            'end_time': None,
            'total_notes': 0,
            'converted_notes': 0,
            'skipped_notes': 0,
            'total_attachments': 0,
            'errors': []
        }

    def show_welcome(self) -> None:
        """显示欢迎信息"""
        welcome_text = f"""
{Fore.CYAN}{'='*70}
{Fore.CYAN}🚀 印象笔记到Obsidian一键迁移工具
{Fore.CYAN}{'='*70}

{Fore.GREEN}✨ 功能特性:
{Fore.WHITE} 🔄 自动导出印象笔记数据
{Fore.WHITE} 🎯 智能转换为Markdown格式
{Fore.WHITE} 📁 完整保留文件夹结构
{Fore.WHITE} 📎 处理所有图片和附件
{Fore.WHITE} 🏗️ 自动配置Obsidian库
{Fore.WHITE} 🚀 一键启动Obsidian

{Fore.YELLOW}⚠️  使用前准备:
{Fore.WHITE} 📝 确保印象笔记账号密码正确
{Fore.WHITE} 🌐 保证网络连接稳定
{Fore.WHITE} 💾 确保有足够的磁盘空间

{Fore.CYAN}{'='*70}
"""
        print(welcome_text)

    def setup_wizard(self) -> bool:
        """配置向导"""
        print(f"{Fore.BLUE}🛠️  配置向导")
        print("-" * 50)

        try:
            # 1. 选择印象笔记版本
            print(f"\n{Fore.YELLOW}1. 选择印象笔记版本:")
            print("1) 印象笔记中国版 (yinxiang.com)")
            print("2) Evernote国际版 (evernote.com)")

            while True:
                choice = click.prompt("请选择", type=int, default=1)
                if choice in [1, 2]:
                    break
                print(f"{Fore.RED}请输入1或2")

            backend = "china" if choice == 1 else "international"

            # 2. 设置输出路径
            print(f"\n{Fore.YELLOW}2. 设置Obsidian库路径:")
            default_vault = str(Path.home() / "Documents" / "ObsidianVault")
            vault_path = click.prompt("Obsidian库路径", default=default_vault)
            vault_path = Path(vault_path).expanduser().resolve()

            # 3. 高级选项
            print(f"\n{Fore.YELLOW}3. 高级选项:")
            auto_open = click.confirm("完成后自动打开Obsidian?", default=True)
            keep_temp = click.confirm("保留临时文件(用于调试)?", default=False)

            # 4. 创建配置
            config_data = {
                'evernote_backend': backend,
                'temp_directory': str(Path(tempfile.gettempdir()) / 'evernote_migration'),
                'remember_credentials': True,
                'input': {
                    'enex_files': [],
                    'input_directory': '',
                    'encoding': 'utf-8'
                },
                'output': {
                    'obsidian_vault': str(vault_path),
                    'create_vault_if_not_exists': True,
                    'backup_existing': True,
                    'overwrite_existing': False
                },
                'conversion': {
                    'preserve_html_tags': False,
                    'convert_tables': True,
                    'convert_links': True,
                    'extract_images': True,
                    'image_folder': 'attachments',
                    'max_filename_length': 100,
                    'clean_html': True,
                    'markdown_extensions': ['.md']
                },
                'metadata': {
                    'include_created_date': True,
                    'include_modified_date': True,
                    'include_tags': True,
                    'include_notebook': True,
                    'include_source': True,
                    'date_format': '%Y-%m-%d %H:%M:%S'
                },
                'file_organization': {
                    'organize_by_notebook': True,
                    'organize_by_tags': False,
                    'organize_by_date': False,
                    'handle_duplicates': 'rename',
                    'invalid_char_replacement': '_'
                },
                'sync': {
                    'incremental': False,
                    'skip_unchanged': True
                },
                'logging': {
                    'level': 'INFO',
                    'console': True
                },
                'migration': {
                    'auto_open_obsidian': auto_open,
                    'keep_temp_files': keep_temp,
                    'create_welcome_note': True,
                    'create_templates': True,
                    'optimize_settings': True
                }
            }

            self.config = Config()
            self.config.config_data = config_data

            print(f"\n{Fore.GREEN}✅ 配置完成")
            print(f"   印象笔记版本: {backend}")
            print(f"   输出库路径: {vault_path}")
            print(f"   自动打开: {'是' if auto_open else '否'}")

            return True

        except (KeyboardInterrupt, click.Abort):
            print(f"\n{Fore.YELLOW}⚠️ 用户取消配置")
            return False
        except Exception as e:
            print(f"\n{Fore.RED}❌ 配置失败: {e}")
            return False

    def run_migration(self) -> bool:
        """运行完整迁移流程"""
        try:
            self.stats['start_time'] = datetime.now()

            print(f"\n{Fore.GREEN}🚀 开始迁移流程...")
            print("=" * 60)

            if not self._step_export_evernote():
                return False

            if not self._step_convert_to_markdown():
                return False

            if not self._step_setup_obsidian():
                return False

            if not self._step_post_process():
                return False

            self.stats['end_time'] = datetime.now()
            self._show_completion_summary()

            return True

        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}⚠️ 用户取消迁移")
            return False
        except Exception as e:
            print(f"\n{Fore.RED}❌ 迁移失败: {e}")
            self.stats['errors'].append(str(e))
            return False

    def _step_export_evernote(self) -> bool:
        """步骤1：导出印象笔记"""
        print(f"\n{Fore.BLUE}📤 步骤 1/4: 导出印象笔记数据")
        print("-" * 40)

        try:
            exporter = EvernoteExporter(self.config.get_all())

            if not exporter.check_dependencies():
                return False

            enex_files = exporter.export_notes()

            if not enex_files:
                print(f"{Fore.RED}❌ 没有导出任何文件")
                return False

            self.config.set('input.enex_files', enex_files)

            print(f"{Fore.GREEN}✅ 导出完成，共 {len(enex_files)} 个文件")
            return True

        except Exception as e:
            print(f"{Fore.RED}❌ 导出失败: {e}")
            self.stats['errors'].append(f"导出失败: {e}")
            return False

    def _step_convert_to_markdown(self) -> bool:
        """步骤2：转换为Markdown"""
        print(f"\n{Fore.BLUE}📝 步骤 2/4: 转换为Markdown格式")
        print("-" * 40)

        try:
            parser = ENEXParser()
            converter = MarkdownConverter(self.config.get_all())
            organizer = FileOrganizer(self.config.get_all())

            enex_files = self.config.get('input.enex_files', [])
            total_notes = 0
            converted_notes = 0

            with tqdm(total=len(enex_files), desc="处理文件") as pbar:
                for enex_file in enex_files:
                    try:
                        notes, notebook_name = parser.parse_file(enex_file)
                        total_notes += len(notes)

                        organized_notes = organizer.organize_notes(notes, notebook_name)
                        organizer.create_directory_structure(organized_notes)

                        for note, file_path in organized_notes:
                            try:
                                markdown_content = converter.convert_note(note)
                                organizer.save_note(note, file_path, markdown_content)

                                if note.attachments:
                                    organizer.save_attachments(note)
                                    self.stats['total_attachments'] += len(note.attachments)

                                converted_notes += 1

                            except Exception as e:
                                print(f"{Fore.YELLOW}⚠️ 跳过笔记 {note.title}: {e}")
                                self.stats['skipped_notes'] += 1

                        organizer.create_index_file(organized_notes, notebook_name)

                    except Exception as e:
                        print(f"{Fore.YELLOW}⚠️ 跳过文件 {enex_file}: {e}")

                    pbar.update(1)

            self.stats['total_notes'] = total_notes
            self.stats['converted_notes'] = converted_notes

            print(f"{Fore.GREEN}✅ 转换完成:")
            print(f"   📄 总笔记数: {total_notes}")
            print(f"   ✅ 成功转换: {converted_notes}")
            print(f"   📎 附件数量: {self.stats['total_attachments']}")

            return converted_notes > 0

        except Exception as e:
            print(f"{Fore.RED}❌ 转换失败: {e}")
            self.stats['errors'].append(f"转换失败: {e}")
            return False

    def _step_setup_obsidian(self) -> bool:
        """步骤3：设置Obsidian库"""
        print(f"\n{Fore.BLUE}🏗️  步骤 3/4: 设置Obsidian库")
        print("-" * 40)

        try:
            self.config.set('migration_time', self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S'))
            self.config.set('total_notes', self.stats['total_notes'])
            self.config.set('converted_notes', self.stats['converted_notes'])

            obsidian_manager = ObsidianManager(self.config.get_all())

            if not obsidian_manager.create_obsidian_vault():
                return False

            if self.config.get('migration.create_welcome_note', True):
                obsidian_manager.create_welcome_note()
                print(f"{Fore.GREEN}   ✅ 创建欢迎笔记")

            if self.config.get('migration.create_templates', True):
                obsidian_manager.create_templates()
                print(f"{Fore.GREEN}   ✅ 创建常用模板")

            if self.config.get('migration.optimize_settings', True):
                obsidian_manager.optimize_vault_settings()
                print(f"{Fore.GREEN}   ✅ 优化库设置")

            obsidian_manager.install_recommended_plugins()

            print(f"{Fore.GREEN}✅ Obsidian库设置完成")
            return True

        except Exception as e:
            print(f"{Fore.RED}❌ 库设置失败: {e}")
            self.stats['errors'].append(f"库设置失败: {e}")
            return False

    def _step_post_process(self) -> bool:
        """步骤4：后处理"""
        print(f"\n{Fore.BLUE}🔧 步骤 4/4: 完成后处理")
        print("-" * 40)

        try:
            if not self.config.get('migration.keep_temp_files', False):
                self._cleanup_temp_files()
                print(f"{Fore.GREEN}   ✅ 清理临时文件")

            if self.config.get('migration.auto_open_obsidian', True):
                obsidian_manager = ObsidianManager(self.config.get_all())
                if obsidian_manager.open_obsidian():
                    print(f"{Fore.GREEN}   ✅ 启动Obsidian")
                else:
                    obsidian_manager.show_obsidian_install_guide()

            print(f"{Fore.GREEN}✅ 后处理完成")
            return True

        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ 后处理警告: {e}")
            return True

    def _cleanup_temp_files(self) -> None:
        """清理临时文件"""
        temp_dir = self.config.get('temp_directory')
        if temp_dir and Path(temp_dir).exists():
            try:
                temp_path = Path(temp_dir)
                for item in temp_path.iterdir():
                    if item.name not in ['enex_output']:
                        if item.is_file():
                            item.unlink()
                        else:
                            shutil.rmtree(item)
            except Exception as e:
                print(f"{Fore.YELLOW}   ⚠️ 清理失败: {e}")

    def _show_completion_summary(self) -> None:
        """显示完成摘要"""
        duration = self.stats['end_time'] - self.stats['start_time']
        vault_path = self.config.get('output.obsidian_vault')

        summary = f"""
{Fore.GREEN}{'='*60}
{Fore.GREEN}🎉 迁移完成！
{Fore.GREEN}{'='*60}

{Fore.CYAN}📊 统计信息:
{Fore.WHITE} ⏱️  总耗时: {duration}
{Fore.WHITE} 📄 总笔记数: {self.stats['total_notes']}
{Fore.WHITE} ✅ 成功转换: {self.stats['converted_notes']}
{Fore.WHITE} ⏭️  跳过笔记: {self.stats['skipped_notes']}
{Fore.WHITE} 📎 附件数量: {self.stats['total_attachments']}

{Fore.CYAN}📁 输出位置:
{Fore.WHITE} {vault_path}

{Fore.CYAN}🚀 下一步:
{Fore.WHITE} 1. 在Obsidian中打开您的库
{Fore.WHITE} 2. 浏览转换后的笔记
{Fore.WHITE} 3. 根据需要安装推荐插件
{Fore.WHITE} 4. 开始您的知识管理之旅！

{Fore.GREEN}感谢使用印象笔记迁移工具！
{Fore.GREEN}{'='*60}
"""
        print(summary)


@click.command()
@click.option('--config', '-c', type=click.Path(exists=True), help='使用指定配置文件')
@click.option('--wizard', '-w', is_flag=True, default=True, help='启动配置向导（默认）')
@click.option('--auto', '-a', is_flag=True, help='使用默认设置自动运行')
def main(config, wizard, auto):
    """一键式印象笔记到Obsidian迁移工具"""
    migrator = UnifiedMigrator()

    try:
        migrator.show_welcome()

        if config:
            migrator.config = Config(config)
            print(f"{Fore.GREEN}✅ 加载配置文件: {config}")
        elif auto:
            migrator.config = Config()
            print(f"{Fore.BLUE}🔄 使用默认配置")
        else:
            if not migrator.setup_wizard():
                print(f"{Fore.YELLOW}👋 退出程序")
                sys.exit(0)

        if not auto:
            if not click.confirm("\n确认开始迁移?"):
                print(f"{Fore.YELLOW}👋 用户取消操作")
                sys.exit(0)

        success = migrator.run_migration()

        if success:
            print(f"\n{Fore.GREEN}🎉 迁移成功完成！")
            sys.exit(0)
        else:
            print(f"\n{Fore.RED}❌ 迁移失败")
            sys.exit(1)

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️ 用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}❌ 程序错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()