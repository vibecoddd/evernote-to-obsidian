#!/usr/bin/env python3
"""
同步失败调试工具 - 专门诊断evernote-backup sync阶段问题
"""

import subprocess
import tempfile
import os
import time
from pathlib import Path
import json

class SyncFailureDebugger:
    """同步失败调试器"""

    def __init__(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix='evernote_sync_debug_'))
        print(f"📁 调试目录: {self.test_dir}")

    def test_sync_with_dummy_credentials(self):
        """使用虚拟凭据测试同步过程"""
        print("🧪 测试同步过程（使用虚拟凭据）")
        print("=" * 50)

        try:
            # 步骤1: 尝试init-db看具体错误
            print("1. 测试init-db阶段...")
            init_cmd = [
                'evernote-backup', 'init-db',
                '--backend', 'china',
                '--user', 'test@example.com',
                '--password', 'dummy_password'
            ]

            result = subprocess.run(
                init_cmd,
                cwd=self.test_dir,
                capture_output=True,
                text=True,
                timeout=30
            )

            print(f"   返回码: {result.returncode}")
            if result.stdout:
                print(f"   输出: {result.stdout[:200]}...")
            if result.stderr:
                print(f"   错误: {result.stderr[:200]}...")

            # 分析具体错误类型
            if result.stderr:
                if "authentication" in result.stderr.lower():
                    print("   🎯 诊断: 认证失败（预期的，使用虚拟凭据）")
                elif "network" in result.stderr.lower():
                    print("   🎯 诊断: 网络连接问题")
                elif "proxy" in result.stderr.lower():
                    print("   🎯 诊断: 代理配置问题")
                elif "ssl" in result.stderr.lower():
                    print("   🎯 诊断: SSL证书问题")
                elif "timeout" in result.stderr.lower():
                    print("   🎯 诊断: 连接超时")
                else:
                    print("   🎯 诊断: 其他类型错误")

        except subprocess.TimeoutExpired:
            print("   ❌ 命令超时（可能是网络问题）")
        except Exception as e:
            print(f"   ❌ 测试失败: {e}")

    def test_proxy_settings(self):
        """测试代理设置对同步的影响"""
        print("\n🌐 测试代理设置")
        print("=" * 30)

        # 检查当前代理设置
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
        current_proxies = {}

        for var in proxy_vars:
            value = os.environ.get(var)
            if value:
                current_proxies[var] = value
                print(f"当前代理: {var}={value}")

        if current_proxies:
            print("\n💡 建议:")
            print("1. 尝试暂时禁用代理:")
            print("   export HTTP_PROXY=")
            print("   export HTTPS_PROXY=")
            print("   export http_proxy=")
            print("   export https_proxy=")

            print("\n2. 或配置evernote-backup使用代理:")
            print("   可能需要在evernote-backup中手动配置代理")

            # 测试无代理连接
            print("\n🧪 测试无代理连接...")
            try:
                env_no_proxy = os.environ.copy()
                for var in proxy_vars:
                    env_no_proxy.pop(var, None)

                test_cmd = ['evernote-backup', '--help']
                result = subprocess.run(
                    test_cmd,
                    env=env_no_proxy,
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode == 0:
                    print("   ✅ 无代理环境下evernote-backup可正常运行")
                else:
                    print("   ❌ 无代理环境下仍有问题")

            except Exception as e:
                print(f"   ❌ 无代理测试失败: {e}")

    def analyze_sync_requirements(self):
        """分析同步的具体要求"""
        print("\n📋 同步要求分析")
        print("=" * 30)

        requirements = [
            ("网络连接", "需要稳定的互联网连接"),
            ("认证凭据", "有效的印象笔记账号密码"),
            ("API访问", "印象笔记API服务可访问"),
            ("数据库", "本地SQLite数据库正常"),
            ("权限", "读写本地文件的权限"),
            ("防火墙", "防火墙允许HTTPS连接")
        ]

        for req, desc in requirements:
            print(f"• {req}: {desc}")

    def generate_solutions(self):
        """生成针对性解决方案"""
        print("\n💡 同步失败解决方案")
        print("=" * 30)

        solutions = [
            {
                "问题": "认证失败",
                "解决方案": [
                    "确认账号密码正确",
                    "检查是否启用了两步验证（需要应用密码）",
                    "确认选择了正确的后端（china/international）"
                ]
            },
            {
                "问题": "网络连接问题",
                "解决方案": [
                    "检查网络连接是否正常",
                    "尝试关闭代理设置",
                    "使用--use-system-ssl-ca参数",
                    "增加网络重试次数: --network-retry-count 100"
                ]
            },
            {
                "问题": "代理问题",
                "解决方案": [
                    "临时禁用代理: unset HTTP_PROXY HTTPS_PROXY",
                    "配置evernote-backup支持代理",
                    "使用直连网络测试"
                ]
            },
            {
                "问题": "API限制",
                "解决方案": [
                    "降低并发数: --max-download-workers 2",
                    "减少chunk大小: --max-chunk-results 50",
                    "等待一段时间后重试"
                ]
            }
        ]

        for sol in solutions:
            print(f"\n🎯 {sol['问题']}:")
            for i, solution in enumerate(sol['解决方案'], 1):
                print(f"   {i}. {solution}")

    def create_enhanced_command(self):
        """创建增强版同步命令"""
        print("\n🚀 建议的增强同步命令")
        print("=" * 40)

        cmd_parts = [
            'evernote-backup sync',
            '--max-download-workers 2',  # 降低并发
            '--max-chunk-results 50',    # 减少chunk大小
            '--network-retry-count 100', # 增加重试次数
            '--use-system-ssl-ca',       # 使用系统CA
            '-v'  # 详细输出（如果支持）
        ]

        print("推荐同步命令:")
        print(" ".join(cmd_parts))

        print("\n如果仍然失败，尝试:")
        print("1. 先执行: unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy")
        print("2. 然后运行上述命令")

    def cleanup(self):
        """清理测试目录"""
        import shutil
        try:
            shutil.rmtree(self.test_dir)
            print(f"\n🧹 已清理测试目录: {self.test_dir}")
        except Exception as e:
            print(f"清理失败: {e}")

def main():
    """主函数"""
    debugger = SyncFailureDebugger()

    try:
        debugger.test_sync_with_dummy_credentials()
        debugger.test_proxy_settings()
        debugger.analyze_sync_requirements()
        debugger.generate_solutions()
        debugger.create_enhanced_command()
    finally:
        debugger.cleanup()

if __name__ == "__main__":
    main()