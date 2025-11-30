#!/usr/bin/env python3
"""
测试文件上传和转换流程
"""

import requests
import json
from pathlib import Path

def test_upload_flow():
    """测试完整的上传和转换流程"""
    print("🧪 测试文件上传和转换流程")
    print("=" * 50)

    # 测试服务器连接
    try:
        response = requests.get('http://localhost:5000/')
        print(f"✅ 服务器连接正常: {response.status_code}")
    except Exception as e:
        print(f"❌ 服务器连接失败: {e}")
        return False

    # 准备测试文件
    test_enex = "/tmp/test_note.enex"
    if not Path(test_enex).exists():
        print(f"❌ 测试文件不存在: {test_enex}")
        return False

    print(f"📄 使用测试文件: {test_enex}")

    # 上传ENEX文件
    try:
        with open(test_enex, 'rb') as f:
            files = {'enex_files': ('test_note.enex', f, 'application/xml')}

            print("📤 上传ENEX文件...")
            response = requests.post('http://localhost:5000/api/upload_enex', files=files)

            print(f"   响应状态: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(f"   上传结果: {result}")

                if result.get('success'):
                    print("✅ 文件上传成功")
                    upload_info = result
                else:
                    print(f"❌ 上传失败: {result.get('error')}")
                    return False
            else:
                print(f"❌ 上传请求失败: {response.text}")
                return False

    except Exception as e:
        print(f"❌ 上传过程出错: {e}")
        return False

    # 准备迁移配置
    config = {
        'evernote_backend': 'test',
        'evernote_credentials': {
            'username': 'test_upload',
            'password': 'test_upload'
        },
        'input': {
            'enex_files': upload_info['files'],
        },
        'output': {
            'obsidian_vault': '/tmp/test_upload_output'
        },
        'temp_directory': upload_info['temp_dir']
    }

    # 启动迁移
    try:
        print("\n🚀 启动迁移任务...")
        response = requests.post('http://localhost:5000/api/start_migration',
                               json=config,
                               headers={'Content-Type': 'application/json'})

        print(f"   响应状态: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            print(f"   任务ID: {task_id}")

            if task_id:
                # 等待任务完成
                import time
                print("⏳ 等待任务完成...")

                for i in range(30):  # 最多等待30秒
                    try:
                        status_response = requests.get(f'http://localhost:5000/api/migration_status/{task_id}')

                        if status_response.status_code == 200:
                            status = status_response.json()
                            print(f"   状态: {status.get('status', 'unknown')} - {status.get('message', '')}")

                            if status.get('status') in ['completed', 'failed']:
                                break

                        time.sleep(1)

                    except Exception as e:
                        print(f"   状态检查错误: {e}")
                        break

                # 检查结果
                output_dir = Path('/tmp/test_upload_output')
                if output_dir.exists():
                    md_files = list(output_dir.rglob('*.md'))
                    print(f"\n📊 转换结果:")
                    print(f"   输出目录: {output_dir}")
                    print(f"   MD文件数: {len(md_files)}")

                    for md_file in md_files:
                        size = md_file.stat().st_size
                        print(f"     📝 {md_file.name} ({size} bytes)")

                    if md_files:
                        print("✅ 上传和转换流程成功！")
                        return True
                    else:
                        print("⚠️ 没有生成MD文件")
                        return False
                else:
                    print("⚠️ 输出目录不存在")
                    return False
            else:
                print("❌ 没有获得任务ID")
                return False
        else:
            print(f"❌ 启动迁移失败: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 迁移过程出错: {e}")
        return False

if __name__ == "__main__":
    success = test_upload_flow()
    if success:
        print("\n🎉 测试完成：上传和转换功能正常工作！")
    else:
        print("\n❌ 测试失败：请检查服务器和配置")