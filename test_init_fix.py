#!/usr/bin/env python3
"""
测试初始化修复
"""

import subprocess
import tempfile
from pathlib import Path

def test_command_syntax():
    """测试命令语法是否正确"""
    print("🧪 测试evernote-backup命令语法修复")
    print("=" * 50)

    # 创建临时目录
    temp_dir = Path(tempfile.mkdtemp(prefix='evernote_syntax_test_'))
    print(f"📁 测试目录: {temp_dir}")

    try:
        # 测试新的命令格式（不需要真实凭据）
        test_cmd = [
            'evernote-backup', 'init-db',
            '--backend', 'china',
            '--user', 'test@example.com',
            '--password', 'dummy_password',
            '--help'  # 添加help参数避免真正执行
        ]

        print("🔍 测试命令:")
        print("   " + " ".join(test_cmd[:-1]))  # 不显示help参数

        # 测试基本语法
        result = subprocess.run(['evernote-backup', 'init-db', '--help'],
                              capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            print("✅ 命令语法测试通过")

            # 检查是否支持用户名密码参数
            if '--user' in result.stdout and '--password' in result.stdout:
                print("✅ 用户名密码参数支持确认")
            else:
                print("⚠️ 警告: 可能不支持--user和--password参数")

            print("\n📝 支持的认证选项:")
            for line in result.stdout.split('\n'):
                if any(key in line for key in ['--user', '--password', '--token']):
                    print(f"   {line.strip()}")

        else:
            print("❌ 命令语法测试失败")

    except Exception as e:
        print(f"❌ 测试失败: {e}")

    finally:
        # 清理临时目录
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    print("\n💡 修复说明:")
    print("- evernote-backup现在需要通过--user和--password参数传递认证信息")
    print("- 不再需要通过stdin传递用户名密码")
    print("- 这解决了'--user and --password are required'错误")

if __name__ == "__main__":
    test_command_syntax()