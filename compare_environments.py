#!/usr/bin/env python3
"""
对比命令行和Web环境下evernote-backup的执行差异
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

def print_environment():
    """打印当前环境信息"""
    print("=" * 60)
    print("环境信息:")
    print("=" * 60)

    print(f"Python版本: {sys.version}")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"Python路径: {sys.executable}")
    print(f"PATH: {os.environ.get('PATH', '未设置')[:200]}...")

    print("\n环境变量:")
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
    for var in proxy_vars:
        value = os.environ.get(var)
        print(f"  {var}: {value if value else '未设置'}")

    print(f"\nPYTHONPATH: {os.environ.get('PYTHONPATH', '未设置')}")
    print(f"HOME: {os.environ.get('HOME', '未设置')}")
    print(f"USER: {os.environ.get('USER', '未设置')}")

def test_evernote_backup():
    """测试evernote-backup命令"""
    print("\n" + "=" * 60)
    print("evernote-backup测试:")
    print("=" * 60)

    # 测试版本命令
    try:
        result = subprocess.run(['evernote-backup', '--version'],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ 版本检查成功: {result.stdout.strip()}")
        else:
            print(f"❌ 版本检查失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 版本检查异常: {e}")
        return False

    # 测试帮助命令
    try:
        result = subprocess.run(['evernote-backup', '--help'],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ 帮助命令成功")
        else:
            print(f"❌ 帮助命令失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 帮助命令异常: {e}")
        return False

    return True

def test_init_db_with_fake_account():
    """使用假账号测试init-db（应该返回特定错误）"""
    print("\n" + "=" * 60)
    print("init-db测试（使用假账号）:")
    print("=" * 60)

    temp_dir = tempfile.mkdtemp(prefix='env_test_')
    print(f"测试目录: {temp_dir}")

    try:
        cmd = [
            'evernote-backup', 'init-db',
            '--backend', 'china',
            '--user', 'test@example.com',
            '--password', 'testpass'
        ]

        print(f"执行命令: {' '.join(cmd)}")
        print(f"工作目录: {temp_dir}")

        # 创建无代理环境
        env = os.environ.copy()
        env.pop('HTTP_PROXY', None)
        env.pop('HTTPS_PROXY', None)
        env.pop('http_proxy', None)
        env.pop('https_proxy', None)

        result = subprocess.run(cmd, cwd=temp_dir, capture_output=True,
                              text=True, timeout=30, env=env)

        print(f"退出码: {result.returncode}")
        print(f"标准输出: {result.stdout[:500]}")
        print(f"标准错误: {result.stderr[:500]}")

        if result.returncode != 0:
            if "username not found" in result.stderr.lower():
                print("✅ 正确返回'用户不存在'错误")
                return True
            elif "authentication" in result.stderr.lower():
                print("✅ 正确返回'认证失败'错误")
                return True
            else:
                print("⚠️ 返回其他错误（可能也是正常的）")
                return True
        else:
            print("❌ 不应该成功（使用假账号）")
            return False

    except subprocess.TimeoutExpired:
        print("❌ 超时")
        return False
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False
    finally:
        # 清理
        import shutil
        try:
            shutil.rmtree(temp_dir)
        except:
            pass

def main():
    """主函数"""
    print("🔍 evernote-backup环境对比测试")
    print(f"执行模式: {'Web环境' if 'flask' in sys.modules else '命令行环境'}")

    print_environment()

    if not test_evernote_backup():
        print("\n❌ evernote-backup基础测试失败")
        return False

    if not test_init_db_with_fake_account():
        print("\n❌ init-db测试失败")
        return False

    print("\n✅ 所有测试通过!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)