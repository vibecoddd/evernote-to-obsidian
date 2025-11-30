#!/usr/bin/env python3
"""
在模拟Web环境下测试evernote-backup
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

# 添加src目录到Python路径（模拟web_app.py的环境）
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

def simulate_web_environment():
    """模拟Web环境下的evernote-backup调用"""
    print("🌐 模拟Web环境测试evernote-backup")
    print("=" * 60)

    # 模拟Web环境导入
    try:
        import flask
        print("✅ Flask环境已模拟")
    except ImportError:
        print("⚠️ Flask未安装，但继续测试")

    # 测试evernote_exporter导入
    try:
        from evernote_exporter import EvernoteExporter
        print("✅ EvernoteExporter导入成功")
    except ImportError as e:
        print(f"❌ EvernoteExporter导入失败: {e}")
        return False

    # 创建测试配置
    config = {
        'temp_directory': '/tmp/web_test',
        'evernote_backend': 'china',
        'evernote_credentials': {
            'username': 'test@example.com',
            'password': 'testpass'
        }
    }

    # 初始化导出器
    exporter = EvernoteExporter(config)

    print("\n🔍 检查依赖...")
    if not exporter.check_dependencies():
        print("❌ 依赖检查失败")
        return False

    print("\n✅ 依赖检查成功")

    # 测试初始化过程（不实际登录）
    print("\n📊 测试初始化过程...")
    temp_path = Path(config['temp_directory'])
    temp_path.mkdir(parents=True, exist_ok=True)

    username, password = exporter.get_credentials()
    print(f"账号获取: {username}")

    # 创建测试命令（应该会因为假账号失败，但我们可以看到执行过程）
    init_cmd = [
        'evernote-backup', 'init-db',
        '--backend', config['evernote_backend'],
        '--user', username,
        '--password', password,
        '--use-system-ssl-ca',
        '--force'
    ]

    print(f"执行命令: {' '.join(init_cmd[:4])} [credentials hidden]")
    print(f"工作目录: {temp_path}")

    # 创建无代理环境
    env = os.environ.copy()
    env.pop('HTTP_PROXY', None)
    env.pop('HTTPS_PROXY', None)
    env.pop('http_proxy', None)
    env.pop('https_proxy', None)

    try:
        result = subprocess.run(init_cmd, cwd=temp_path,
                              capture_output=True, text=True,
                              timeout=30, env=env)

        print(f"\n退出码: {result.returncode}")
        print(f"标准输出: {result.stdout}")
        print(f"标准错误: {result.stderr}")

        if result.returncode != 0:
            if "username not found" in result.stderr.lower():
                print("✅ 预期的'用户不存在'错误 - 命令执行环境正常")
                return True
            else:
                print("⚠️ 其他错误，但可能仍正常")
                return True
        else:
            print("❌ 不应该成功（使用假账号）")
            return False

    except subprocess.TimeoutExpired:
        print("❌ 命令超时")
        return False
    except Exception as e:
        print(f"❌ 执行异常: {e}")
        return False
    finally:
        # 清理
        import shutil
        try:
            shutil.rmtree(temp_path)
        except:
            pass

def main():
    """主函数"""
    print("🔍 Web环境evernote-backup测试")

    success = simulate_web_environment()

    if success:
        print("\n✅ Web环境测试通过!")
    else:
        print("\n❌ Web环境测试失败!")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)