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

        # 检查版本信息
        try:
            # 使用Python模块方式调用，避免PATH问题
            evernote_backup_cmd = [sys.executable, '-m', 'evernote_backup']
            
            result = subprocess.run(evernote_backup_cmd + ['--version'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"{Fore.GREEN}✅ evernote-backup已安装: {version}")

                # 进一步验证功能完整性
                help_result = subprocess.run(evernote_backup_cmd + ['--help'],
                                           capture_output=True, text=True, timeout=10)
                if help_result.returncode == 0:
                    print(f"{Fore.GREEN}✅ evernote-backup功能验证通过")

                    # 验证关键依赖（evernote-backup使用自己的evernote-plus包）
                    try:
                        import evernote.edam.type.ttypes
                        print(f"{Fore.GREEN}✅ evernote依赖可用")
                    except ImportError:
                        print(f"{Fore.RED}❌ evernote依赖缺失，evernote-backup无法正常工作")

                    return True
                else:
                    print(f"{Fore.RED}❌ evernote-backup功能异常")
                    return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(f"{Fore.YELLOW}⚠️ evernote-backup未找到或超时")
        except Exception as e:
            print(f"{Fore.RED}❌ 检查evernote-backup时出错: {e}")

        print(f"{Fore.YELLOW}📦 正在安装evernote-backup...")
        try:
            # 使用更详细的安装过程
            install_result = subprocess.run([
                sys.executable, '-m', 'pip', 'install',
                '--upgrade', 'evernote-backup'
            ], capture_output=True, text=True, timeout=120)

            if install_result.returncode == 0:
                print(f"{Fore.GREEN}✅ evernote-backup安装成功")

                # 重新验证安装
                verify_result = subprocess.run(['evernote-backup', '--version'],
                                             capture_output=True, text=True, timeout=10)
                if verify_result.returncode == 0:
                    print(f"{Fore.GREEN}✅ 安装验证通过: {verify_result.stdout.strip()}")
                    return True
                else:
                    print(f"{Fore.RED}❌ 安装验证失败")
                    return False
            else:
                print(f"{Fore.RED}❌ 安装失败:")
                print(f"   标准输出: {install_result.stdout}")
                print(f"   错误输出: {install_result.stderr}")
                return False

        except subprocess.CalledProcessError as e:
            print(f"{Fore.RED}❌ 安装过程出错: {e}")
            return False
        except subprocess.TimeoutExpired:
            print(f"{Fore.RED}❌ 安装超时，可能是网络问题")
            return False
        except Exception as e:
            print(f"{Fore.RED}❌ 安装时发生意外错误: {e}")
            return False

    def get_credentials(self) -> tuple[str, str]:
        """获取用户凭据"""
        # 首先检查配置中是否有凭据（用于Web界面）
        evernote_creds = self.config.get('evernote_credentials')
        if evernote_creds:
            username = evernote_creds.get('username')
            password = evernote_creds.get('password')
            if username and password:
                print(f"{Fore.CYAN}🔐 使用配置中的账号: {username}")
                return username, password

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
            print(f"{Fore.BLUE}🗑️  清空旧数据库...")
            # 删除旧的数据库文件，确保每次导出都是全新的
            db_files = list(temp_path.glob('*.db'))
            for db_file in db_files:
                try:
                    db_file.unlink()
                    print(f"{Fore.GREEN}   ✅ 删除旧数据库文件: {db_file.name}")
                except Exception as e:
                    print(f"{Fore.YELLOW}   ⚠️  删除旧数据库文件 {db_file.name} 时出错: {e}")
            
            print(f"{Fore.BLUE}📊 初始化数据库...")
            print(f"{Fore.CYAN}   后端: {self.backend}")
            print(f"{Fore.CYAN}   用户: {username}")

            init_cmd = [
                sys.executable, '-m', 'evernote_backup', 'init-db',
                '--backend', self.backend,
                '--user', username,
                '--password', password,
                '--use-system-ssl-ca',  # 使用系统SSL证书
                '--force'
            ]

            try:
                # 创建无代理环境
                env = os.environ.copy()
                env.pop('HTTP_PROXY', None)
                env.pop('HTTPS_PROXY', None)
                env.pop('http_proxy', None)
                env.pop('https_proxy', None)

                print(f"{Fore.CYAN}   🌐 使用直连网络（跳过代理）")

                with subprocess.Popen(init_cmd,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    text=True, cwd=self.temp_dir, env=env) as proc:

                    # 等待命令完成
                    stdout, stderr = proc.communicate(timeout=60)

                    print(f"{Fore.CYAN}   初始化命令输出: {stdout[:200]}...")

                    if proc.returncode != 0:
                        error_msg = f"初始化失败 (退出码: {proc.returncode})"
                        if stderr:
                            error_msg += f"\n错误详情: {stderr}"

                        # 分析具体错误类型并提供解决方案
                        stderr_lower = stderr.lower()
                        if "username not found" in stderr_lower or "user not found" in stderr_lower:
                            error_msg += "\n\n🎯 账号不存在错误："
                            error_msg += f"\n   输入的账号: {username}"
                            error_msg += "\n   建议检查:"
                            error_msg += "\n   ✓ 账号邮箱地址是否正确"
                            error_msg += "\n   ✓ 是否选择了正确的印象笔记版本（中国版/国际版）"
                            error_msg += "\n   ✓ 账号是否已激活"
                        elif "authentication" in stderr_lower or "login failed" in stderr_lower:
                            error_msg += "\n\n🔐 认证失败："
                            error_msg += "\n   ✓ 密码是否正确"
                            error_msg += "\n   ✓ 如果启用了两步验证，请使用应用专用密码"
                            error_msg += "\n   ✓ 检查账号是否被锁定"
                        elif "network" in stderr_lower or "connection" in stderr_lower:
                            error_msg += "\n\n🌐 网络连接问题："
                            error_msg += "\n   ✓ 检查网络连接"
                            error_msg += "\n   ✓ 尝试禁用代理: unset HTTP_PROXY HTTPS_PROXY"
                            error_msg += "\n   ✓ 检查防火墙设置"
                        else:
                            error_msg += "\n\n💡 通用解决方案："
                            error_msg += "\n   ✓ 确认账号密码正确"
                            error_msg += "\n   ✓ 检查印象笔记版本选择"
                            error_msg += "\n   ✓ 尝试手动登录印象笔记客户端验证账号"

                        raise Exception(error_msg)

            except subprocess.TimeoutExpired:
                raise Exception("初始化超时，可能是网络连接问题或印象笔记服务器响应慢")

            print(f"{Fore.GREEN}✅ 数据库初始化成功")

            print(f"{Fore.BLUE}🔄 同步笔记数据...")
            sync_cmd = [
                sys.executable, '-m', 'evernote_backup', 'sync',
                '--max-download-workers', '2',      # 降低并发数
                '--max-chunk-results', '50',        # 减少chunk大小
                '--network-retry-count', '100',     # 增加重试次数
                '--use-system-ssl-ca'               # 使用系统SSL证书
            ]

            with subprocess.Popen(sync_cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True,
                                cwd=self.temp_dir, env=env) as proc:

                sync_output = []
                with tqdm(desc="同步进度", unit="notes") as pbar:
                    for line in proc.stdout:
                        line = line.strip()
                        sync_output.append(line)
                        print(f"📋 同步日志: {line}")

                        if line:
                            if "Downloaded" in line or "notes" in line:
                                pbar.update(1)
                                pbar.set_postfix_str(line[:50])

                # 等待进程完成并获取返回码
                proc.wait()

                if proc.returncode != 0:
                    sync_error_output = "\n".join(sync_output[-10:])  # 获取最后10行输出
                    error_msg = "同步失败"

                    # 分析同步失败的具体原因
                    sync_error_lower = sync_error_output.lower()
                    if "connection" in sync_error_lower or "network" in sync_error_lower:
                        error_msg += "\n\n🌐 网络连接问题："
                        error_msg += "\n   ✓ 检查网络连接是否稳定"
                        error_msg += "\n   ✓ 尝试禁用代理设置"
                        error_msg += "\n   ✓ 检查防火墙设置"
                    elif "timeout" in sync_error_lower:
                        error_msg += "\n\n⏱️ 连接超时："
                        error_msg += "\n   ✓ 网络连接可能不稳定"
                        error_msg += "\n   ✓ 印象笔记服务器可能繁忙，请稍后重试"
                    elif "authentication" in sync_error_lower or "token" in sync_error_lower:
                        error_msg += "\n\n🔐 认证问题："
                        error_msg += "\n   ✓ 登录会话可能已过期，请重新尝试"
                        error_msg += "\n   ✓ 检查账号是否被锁定"
                    elif "rate limit" in sync_error_lower or "too many requests" in sync_error_lower:
                        error_msg += "\n\n🚦 API限制："
                        error_msg += "\n   ✓ 请求过于频繁，请等待5-10分钟后重试"
                        error_msg += "\n   ✓ 或尝试降低并发设置"
                    else:
                        error_msg += "\n\n🔧 evernote-backup插件问题："
                        error_msg += "\n   ✓ 检查插件是否正确安装: pip show evernote-backup"
                        error_msg += "\n   ✓ 尝试重新安装: pip install --upgrade evernote-backup"
                        error_msg += "\n   ✓ 检查插件版本兼容性"

                    error_msg += f"\n\n📋 详细错误输出:\n{sync_error_output}"
                    raise Exception(error_msg)

            print(f"{Fore.GREEN}✅ 笔记同步完成")

            print(f"{Fore.BLUE}📤 导出为ENEX格式...")
            export_dir = temp_path / 'enex_output'
            export_dir.mkdir(parents=True, exist_ok=True)
            export_cmd = [sys.executable, '-m', 'evernote_backup', 'export', str(export_dir)]

            print(f"{Fore.CYAN}   导出命令: {' '.join(export_cmd)}")
            print(f"{Fore.CYAN}   导出目录: {export_dir}")
            print(f"{Fore.CYAN}   工作目录: {self.temp_dir}")

            result = subprocess.run(export_cmd, cwd=self.temp_dir,
                                  capture_output=True, text=True, env=env)

            print(f"{Fore.CYAN}   导出退出码: {result.returncode}")
            if result.stdout:
                print(f"{Fore.CYAN}   导出输出: {result.stdout}")
            if result.stderr:
                print(f"{Fore.CYAN}   导出错误: {result.stderr}")

            if result.returncode != 0:
                raise Exception(f"导出失败: {result.stderr}")

            enex_files = list(export_dir.glob('*.enex'))
            print(f"{Fore.CYAN}   找到ENEX文件: {len(enex_files)}个")

            if not enex_files:
                # 检查导出目录内容
                all_files = list(export_dir.iterdir())
                print(f"{Fore.YELLOW}   导出目录内容: {[f.name for f in all_files]}")
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