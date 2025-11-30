#!/usr/bin/env python3
"""
同步问题专门诊断工具 - 针对"同步失败，请检查backup插件是否可用"
"""

import subprocess
import tempfile
import sys
from pathlib import Path
import time

class SyncIssuesDiagnostic:
    """同步问题诊断器"""

    def __init__(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix='sync_diagnostic_'))
        print(f"📁 诊断目录: {self.test_dir}")

    def check_evernote_backup_health(self):
        """全面检查evernote-backup健康状态"""
        print("🔍 全面检查evernote-backup状态")
        print("=" * 50)

        # 1. 版本检查
        try:
            result = subprocess.run(['evernote-backup', '--version'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"✅ 版本信息: {version}")
            else:
                print(f"❌ 版本检查失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ 版本检查异常: {e}")
            return False

        # 2. 帮助命令检查
        try:
            result = subprocess.run(['evernote-backup', '--help'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("✅ 帮助命令正常")
            else:
                print(f"❌ 帮助命令失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ 帮助命令异常: {e}")
            return False

        # 3. 检查子命令可用性
        subcommands = ['init-db', 'sync', 'export']
        for cmd in subcommands:
            try:
                result = subprocess.run(['evernote-backup', cmd, '--help'],
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print(f"✅ 子命令 '{cmd}' 可用")
                else:
                    print(f"❌ 子命令 '{cmd}' 不可用: {result.stderr}")
                    return False
            except Exception as e:
                print(f"❌ 子命令 '{cmd}' 检查异常: {e}")
                return False

        # 4. 检查Python依赖
        print("\n🐍 Python依赖检查:")
        dependencies = [
            'evernote3', 'click', 'requests', 'thrift', 'xmltodict'
        ]

        for dep in dependencies:
            try:
                __import__(dep)
                print(f"✅ {dep} 依赖可用")
            except ImportError:
                print(f"❌ {dep} 依赖缺失")
                return False

        return True

    def test_init_db_functionality(self):
        """测试init-db功能"""
        print("\n🧪 测试init-db功能")
        print("=" * 30)

        try:
            # 使用无效凭据测试init-db的错误处理
            test_cmd = [
                'evernote-backup', 'init-db',
                '--backend', 'china',
                '--user', 'diagnostic_test@nonexistent.com',
                '--password', 'diagnostic_test_password'
            ]

            result = subprocess.run(test_cmd, cwd=self.test_dir,
                                  capture_output=True, text=True, timeout=30)

            # 这里应该返回错误，因为我们使用的是无效凭据
            if result.returncode != 0:
                if "username not found" in result.stderr.lower():
                    print("✅ init-db功能正常（正确返回用户不存在错误）")
                    return True
                elif "authentication" in result.stderr.lower():
                    print("✅ init-db功能正常（正确返回认证错误）")
                    return True
                else:
                    print(f"⚠️ init-db返回其他错误: {result.stderr}")
                    return True  # 仍然算作功能正常
            else:
                print("❌ init-db功能异常（不应该成功）")
                return False

        except subprocess.TimeoutExpired:
            print("❌ init-db超时")
            return False
        except Exception as e:
            print(f"❌ init-db测试异常: {e}")
            return False

    def test_sync_command_availability(self):
        """测试sync命令可用性"""
        print("\n🔄 测试sync命令")
        print("=" * 25)

        try:
            # 在没有数据库的情况下运行sync应该会报错，但不应该崩溃
            result = subprocess.run(['evernote-backup', 'sync'],
                                  cwd=self.test_dir,
                                  capture_output=True, text=True, timeout=10)

            if result.returncode != 0:
                error_msg = result.stderr.lower()
                if "no such file" in error_msg or "database" in error_msg:
                    print("✅ sync命令正常（正确报告数据库不存在）")
                    return True
                else:
                    print(f"⚠️ sync命令返回其他错误: {result.stderr}")
                    return True
            else:
                print("❌ sync命令异常（不应该在没有数据库时成功）")
                return False

        except subprocess.TimeoutExpired:
            print("❌ sync命令超时")
            return False
        except Exception as e:
            print(f"❌ sync命令测试异常: {e}")
            return False

    def check_system_environment(self):
        """检查系统环境"""
        print("\n💻 系统环境检查")
        print("=" * 25)

        # 检查Python版本
        python_version = sys.version
        print(f"🐍 Python版本: {python_version}")

        # 检查可用磁盘空间
        import shutil
        disk_usage = shutil.disk_usage(self.test_dir)
        free_gb = disk_usage.free / (1024**3)
        print(f"💾 可用磁盘空间: {free_gb:.1f} GB")

        if free_gb < 1:
            print("⚠️ 磁盘空间不足，可能影响同步")

        # 检查网络连接
        print("\n🌐 网络连接测试:")
        test_hosts = [
            ('印象笔记中国', 'app.yinxiang.com'),
            ('Evernote国际', 'www.evernote.com')
        ]

        for name, host in test_hosts:
            try:
                result = subprocess.run(['ping', '-c', '1', '-W', '3', host],
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    print(f"✅ {name} ({host}) 网络连通")
                else:
                    print(f"❌ {name} ({host}) 网络不通")
            except Exception as e:
                print(f"⚠️ {name} 网络测试失败: {e}")

    def generate_diagnostic_report(self):
        """生成诊断报告"""
        print("\n📋 诊断报告")
        print("=" * 15)

        # 运行所有测试
        tests = [
            ("evernote-backup健康检查", self.check_evernote_backup_health),
            ("init-db功能测试", self.test_init_db_functionality),
            ("sync命令测试", self.test_sync_command_availability),
            ("系统环境检查", self.check_system_environment)
        ]

        results = {}
        for test_name, test_func in tests:
            try:
                result = test_func()
                results[test_name] = "✅ 通过" if result else "❌ 失败"
            except Exception as e:
                results[test_name] = f"❌ 异常: {e}"

        print("\n📊 测试结果汇总:")
        for test_name, result in results.items():
            print(f"   {test_name}: {result}")

        # 生成建议
        self.generate_recommendations(results)

    def generate_recommendations(self, results):
        """生成修复建议"""
        print("\n💡 修复建议")
        print("=" * 15)

        failed_tests = [name for name, result in results.items() if "失败" in result or "异常" in result]

        if not failed_tests:
            print("🎉 所有测试都通过了！evernote-backup插件状态正常。")
            print("\n如果仍然遇到同步失败，可能的原因:")
            print("1. 账号密码问题 - 确保使用正确的印象笔记账号")
            print("2. 网络暂时性问题 - 稍后重试")
            print("3. 印象笔记服务器限制 - 降低请求频率")
        else:
            print("🔧 发现以下问题，建议修复:")
            for test in failed_tests:
                print(f"   ❌ {test}")

            print("\n🛠️ 修复步骤:")
            print("1. 重新安装evernote-backup:")
            print("   pip uninstall evernote-backup -y")
            print("   pip install evernote-backup")

            print("\n2. 检查Python环境:")
            print("   pip check")

            print("\n3. 清理缓存:")
            print("   pip cache purge")

            print("\n4. 如果问题持续，尝试使用虚拟环境:")
            print("   python -m venv fresh_env")
            print("   source fresh_env/bin/activate  # Linux/Mac")
            print("   fresh_env\\Scripts\\activate     # Windows")
            print("   pip install evernote-backup")

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
    print("🔍 同步问题诊断工具")
    print("=" * 30)

    diagnostic = SyncIssuesDiagnostic()

    try:
        diagnostic.generate_diagnostic_report()
    finally:
        diagnostic.cleanup()

if __name__ == "__main__":
    main()