#!/usr/bin/env python3
"""
调试Web迁移进度和导出问题
"""

import requests
import json
import time
import threading
from pathlib import Path

def test_web_api():
    """测试Web API接口"""
    print("🔍 调试Web迁移API")
    print("=" * 60)

    base_url = "http://127.0.0.1:5000"

    # 测试主页
    print("1️⃣ 测试主页访问...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ 主页访问成功")
        else:
            print(f"❌ 主页访问失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 主页访问异常: {e}")
        return False

    # 测试迁移页面
    print("\n2️⃣ 测试迁移页面...")
    try:
        response = requests.get(f"{base_url}/migrate")
        if response.status_code == 200:
            print("✅ 迁移页面访问成功")
        else:
            print(f"❌ 迁移页面访问失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 迁移页面异常: {e}")
        return False

    # 测试迁移API
    print("\n3️⃣ 测试迁移API...")
    migration_config = {
        'evernote_backend': 'china',
        'evernote_credentials': {
            'username': 'test@example.com',
            'password': 'testpass'
        },
        'output': {
            'obsidian_vault': '/tmp/debug_vault'
        }
    }

    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(
            f"{base_url}/api/start_migration",
            json=migration_config,
            headers=headers
        )

        print(f"HTTP状态码: {response.status_code}")
        print(f"响应内容: {response.text}")

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ 迁移任务启动成功")
                task_id = result.get('task_id')
                print(f"任务ID: {task_id}")

                # 监控任务状态
                print("\n4️⃣ 监控任务状态...")
                for i in range(10):
                    time.sleep(2)
                    status_response = requests.get(f"{base_url}/api/migration_status/{task_id}")
                    if status_response.status_code == 200:
                        status = status_response.json()
                        print(f"  状态检查 {i+1}: {status}")

                        if status.get('status') in ['completed', 'failed']:
                            break
                    else:
                        print(f"  状态检查失败: {status_response.status_code}")

                return True
            else:
                print(f"❌ 迁移任务启动失败: {result.get('error')}")
                return False
        else:
            print(f"❌ 迁移API请求失败: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 迁移API异常: {e}")
        return False

def test_evernote_export_directly():
    """直接测试evernote导出功能"""
    print("\n🔧 直接测试导出功能")
    print("=" * 30)

    import sys
    src_dir = Path(__file__).parent / 'src'
    sys.path.insert(0, str(src_dir))

    try:
        from evernote_exporter import EvernoteExporter

        config = {
            'temp_directory': '/tmp/debug_export_test',
            'evernote_backend': 'china',
            'evernote_credentials': {
                'username': 'test@example.com',
                'password': 'testpass'
            }
        }

        exporter = EvernoteExporter(config)

        print("📋 检查依赖...")
        if exporter.check_dependencies():
            print("✅ 依赖检查通过")
        else:
            print("❌ 依赖检查失败")
            return False

        print("\n📤 测试导出...")
        try:
            enex_files = exporter.export_notes()
            if enex_files:
                print(f"✅ 导出成功: {len(enex_files)} 个文件")
                for file in enex_files:
                    print(f"  📄 {file}")
            else:
                print("❌ 导出失败: 没有文件")
            return len(enex_files) > 0
        except Exception as e:
            print(f"❌ 导出异常: {e}")
            return False

    except Exception as e:
        print(f"❌ 导入模块异常: {e}")
        return False

def main():
    """主函数"""
    print("🐛 Web迁移调试工具")

    print("\n" + "="*60)
    print("测试1: Web API接口")
    print("="*60)
    api_success = test_web_api()

    print("\n" + "="*60)
    print("测试2: 直接导出功能")
    print("="*60)
    export_success = test_evernote_export_directly()

    print("\n" + "="*60)
    print("总结")
    print("="*60)
    print(f"Web API测试: {'✅ 成功' if api_success else '❌ 失败'}")
    print(f"导出功能测试: {'✅ 成功' if export_success else '❌ 失败'}")

    if not api_success:
        print("\n💡 Web API问题可能的原因:")
        print("   • Web服务器没有运行")
        print("   • 端口冲突或网络问题")
        print("   • 请求格式错误")

    if not export_success:
        print("\n💡 导出功能问题可能的原因:")
        print("   • evernote-backup依赖问题")
        print("   • 账号认证问题")
        print("   • 临时目录权限问题")

    return api_success and export_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)