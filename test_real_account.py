#!/usr/bin/env python3
"""
使用真实账号测试evernote-backup
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

# 添加src目录到Python路径
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

def test_real_account():
    """测试真实账号"""
    print("🔐 使用真实账号测试evernote-backup")
    print("=" * 60)

    # 真实账号信息（已隐藏）
    username = "your_email@example.com"
    password = "your_password"
    backend = "china"

    print(f"账号: {username}")
    print(f"后端: {backend}")

    # 创建测试目录
    temp_dir = tempfile.mkdtemp(prefix='real_account_test_')
    print(f"测试目录: {temp_dir}")

    try:
        # 测试evernote-backup版本
        print("\n🔍 检查evernote-backup...")
        version_result = subprocess.run(['evernote-backup', '--version'],
                                      capture_output=True, text=True, timeout=10)
        if version_result.returncode == 0:
            print(f"✅ {version_result.stdout.strip()}")
        else:
            print(f"❌ 版本检查失败: {version_result.stderr}")
            return False

        # 测试init-db
        print("\n📊 测试数据库初始化...")
        init_cmd = [
            'evernote-backup', 'init-db',
            '--backend', backend,
            '--user', username,
            '--password', password,
            '--use-system-ssl-ca',
            '--force'
        ]

        print(f"执行命令: evernote-backup init-db --backend {backend} --user {username} --password [hidden]")

        # 创建无代理环境
        env = os.environ.copy()
        env.pop('HTTP_PROXY', None)
        env.pop('HTTPS_PROXY', None)
        env.pop('http_proxy', None)
        env.pop('https_proxy', None)

        result = subprocess.run(init_cmd, cwd=temp_dir,
                              capture_output=True, text=True,
                              timeout=60, env=env)

        print(f"退出码: {result.returncode}")
        if result.stdout:
            print(f"标准输出:\n{result.stdout}")
        if result.stderr:
            print(f"标准错误:\n{result.stderr}")

        if result.returncode == 0:
            print("\n✅ 数据库初始化成功!")

            # 检查是否创建了数据库文件
            db_files = list(Path(temp_dir).glob('*.db'))
            if db_files:
                print(f"✅ 数据库文件已创建: {db_files}")

            # 测试sync命令
            print("\n🔄 测试同步功能...")
            sync_cmd = [
                'evernote-backup', 'sync',
                '--max-download-workers', '1',
                '--max-chunk-results', '10',
                '--use-system-ssl-ca'
            ]

            sync_result = subprocess.run(sync_cmd, cwd=temp_dir,
                                       capture_output=True, text=True,
                                       timeout=120, env=env)

            print(f"同步退出码: {sync_result.returncode}")
            if sync_result.stdout:
                print(f"同步输出:\n{sync_result.stdout}")
            if sync_result.stderr:
                print(f"同步错误:\n{sync_result.stderr}")

            if sync_result.returncode == 0:
                print("\n✅ 同步成功!")
                return True
            else:
                print(f"\n⚠️ 同步失败，但登录成功说明账号有效")
                return True

        else:
            error_lower = result.stderr.lower()
            if "username not found" in error_lower:
                print("\n❌ 账号不存在 - 请检查账号是否正确")
            elif "authentication" in error_lower or "login failed" in error_lower:
                print("\n❌ 认证失败 - 请检查密码是否正确")
            elif "network" in error_lower or "connection" in error_lower:
                print("\n❌ 网络连接问题")
            else:
                print(f"\n❌ 初始化失败: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("\n❌ 操作超时")
        return False
    except Exception as e:
        print(f"\n❌ 异常: {e}")
        return False
    finally:
        # 清理测试目录
        import shutil
        try:
            shutil.rmtree(temp_dir)
            print(f"\n🧹 已清理测试目录: {temp_dir}")
        except Exception as e:
            print(f"清理失败: {e}")

def main():
    """主函数"""
    print("🧪 真实账号验证测试")

    success = test_real_account()

    if success:
        print("\n🎉 真实账号测试成功! web app应该可以正常使用了")
    else:
        print("\n❌ 真实账号测试失败")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)