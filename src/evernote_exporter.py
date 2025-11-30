#!/usr/bin/env python3
"""
印象笔记导出模块 - 集成evernote-backup功能
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
import json
import time
from getpass import getpass

import click
from tqdm import tqdm
import colorama
from colorama import Fore, Style


class EvernoteExporter:
    """印象笔记导出器"""

    def __init__(self, config: Dict[str, Any]):
        """初始化导出器"""
        self.config = config
        self.temp_dir = config.get('temp_directory', '/tmp/evernote_export')
        self.backend = config.get('evernote_backend', 'china')

    def check_dependencies(self) -> bool:
        """检查并安装依赖"""
        print(f"{Fore.BLUE}🔍 检查依赖...")

        try:
            result = subprocess.run(['evernote-backup', '--version'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"{Fore.GREEN}✅ evernote-backup已安装")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        print(f"{Fore.YELLOW}📦 正在安装evernote-backup...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'evernote-backup'],
                         check=True, capture_output=True)
            print(f"{Fore.GREEN}✅ evernote-backup安装成功")
            return True
        except subprocess.CalledProcessError as e:
            print(f"{Fore.RED}❌ 安装失败: {e}")
            return False

    def get_credentials(self) -> tuple[str, str]:
        """获取用户凭据"""
        print(f"\n{Fore.CYAN}🔐 请输入印象笔记账号信息:")

        credentials_file = Path(self.temp_dir) / '.credentials'
        if credentials_file.exists() and self.config.get('remember_credentials', False):
            try:
                with open(credentials_file, 'r') as f:
                    creds = json.load(f)
                    username = creds.get('username')
                    if username:
                        use_saved = click.confirm(f"使用保存的账号 {username}?")
                        if use_saved:
                            return username, creds.get('password', '')
            except Exception:
                pass

        username = click.prompt("用户名/邮箱")
        password = getpass("密码: ")

        if click.confirm("是否保存账号信息？(密码不会保存)"):
            try:
                Path(self.temp_dir).mkdir(parents=True, exist_ok=True)
                with open(credentials_file, 'w') as f:
                    json.dump({'username': username}, f)
            except Exception:
                pass

        return username, password

    def export_notes(self) -> List[str]:
        """导出印象笔记"""
        print(f"\n{Fore.GREEN}🚀 开始导出印象笔记...")

        temp_path = Path(self.temp_dir)
        temp_path.mkdir(parents=True, exist_ok=True)

        username, password = self.get_credentials()

        try:
            print(f"{Fore.BLUE}📊 初始化数据库...")
            init_cmd = [
                'evernote-backup', 'init-db',
                '--backend', self.backend, '--force'
            ]

            with subprocess.Popen(init_cmd, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, cwd=self.temp_dir) as proc:
                stdout, stderr = proc.communicate(f"{username}\n{password}\n")

                if proc.returncode != 0:
                    raise Exception(f"初始化失败: {stderr}")

            print(f"{Fore.GREEN}✅ 数据库初始化成功")

            print(f"{Fore.BLUE}🔄 同步笔记数据...")
            sync_cmd = ['evernote-backup', 'sync']

            with subprocess.Popen(sync_cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True,
                                cwd=self.temp_dir) as proc:

                with tqdm(desc="同步进度", unit="notes") as pbar:
                    for line in proc.stdout:
                        line = line.strip()
                        if line:
                            if "Downloaded" in line or "notes" in line:
                                pbar.update(1)
                                pbar.set_postfix_str(line[:50])

                if proc.returncode != 0:
                    raise Exception("同步失败")

            print(f"{Fore.GREEN}✅ 笔记同步完成")

            print(f"{Fore.BLUE}📤 导出为ENEX格式...")
            export_dir = temp_path / 'enex_output'
            export_cmd = ['evernote-backup', 'export', str(export_dir)]

            result = subprocess.run(export_cmd, cwd=self.temp_dir,
                                  capture_output=True, text=True)

            if result.returncode != 0:
                raise Exception(f"导出失败: {result.stderr}")

            enex_files = list(export_dir.glob('*.enex'))

            if not enex_files:
                raise Exception("未找到导出的ENEX文件")

            print(f"{Fore.GREEN}✅ 导出完成，共 {len(enex_files)} 个文件")

            for file in enex_files:
                size_mb = file.stat().st_size / (1024 * 1024)
                print(f"  📄 {file.name} ({size_mb:.1f} MB)")

            return [str(f) for f in enex_files]

        except Exception as e:
            print(f"{Fore.RED}❌ 导出失败: {e}")
            print(f"\n{Fore.YELLOW}💡 备用方案:")
            print("1. 使用印象笔记客户端手动导出ENEX文件")
            print("2. 检查网络连接和账号密码")
            print("3. 查看详细错误信息进行故障排除")
            return []


if __name__ == "__main__":
    colorama.init(autoreset=True)
    print("EvernoteExporter module loaded successfully")