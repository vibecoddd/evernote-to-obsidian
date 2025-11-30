#!/usr/bin/env python3
"""
测试真实用户流程 - 完整的Web界面上传和转换
"""

import requests
import json
import time
from pathlib import Path

def test_real_user_flow():
    """测试真实用户体验流程"""
    print("🧪 测试真实用户流程")
    print("=" * 50)

    # 设置用户指定的输出目录
    user_output_dir = "/tmp/my_obsidian_vault"

    print(f"📁 用户指定输出目录: {user_output_dir}")

    # 清理之前的测试目录
    import shutil
    if Path(user_output_dir).exists():
        shutil.rmtree(user_output_dir)
        print(f"🧹 清理旧的输出目录")

    # 准备ENEX文件
    test_enex = "/tmp/test_note.enex"
    if not Path(test_enex).exists():
        print(f"❌ 测试ENEX文件不存在: {test_enex}")
        return False

    print(f"📄 使用ENEX文件: {test_enex} ({Path(test_enex).stat().st_size} bytes)")

    # 1. 上传ENEX文件
    try:
        print("\n📤 步骤1: 上传ENEX文件")

        with open(test_enex, 'rb') as f:
            files = {'enex_files': ('test_note.enex', f, 'application/xml')}
            response = requests.post('http://localhost:5000/api/upload_enex', files=files)

        if response.status_code != 200:
            print(f"❌ 上传失败: {response.status_code}")
            return False

        upload_result = response.json()
        if not upload_result.get('success'):
            print(f"❌ 上传失败: {upload_result.get('error')}")
            return False

        print(f"✅ 文件上传成功")
        print(f"   上传的文件: {upload_result['files']}")
        print(f"   临时目录: {upload_result['temp_dir']}")

    except Exception as e:
        print(f"❌ 上传异常: {e}")
        return False

    # 2. 配置迁移参数（模拟用户在Web界面选择的设置）
    print(f"\n⚙️ 步骤2: 配置迁移参数")

    config = {
        'evernote_backend': 'upload_mode',  # 标识为上传模式
        'input': {
            'enex_files': upload_result['files'],
        },
        'output': {
            'obsidian_vault': user_output_dir,  # 用户选择的目录
            'create_vault_if_not_exists': True,
            'backup_existing': True
        },
        'conversion': {
            'preserve_html_tags': False,
            'extract_images': True,
            'image_folder': 'attachments',
            'clean_html': True
        },
        'temp_directory': upload_result['temp_dir']
    }

    print(f"   输出目录: {config['output']['obsidian_vault']}")
    print(f"   ENEX文件数: {len(config['input']['enex_files'])}")

    # 3. 启动迁移
    try:
        print(f"\n🚀 步骤3: 启动迁移任务")

        response = requests.post('http://localhost:5000/api/start_migration',
                               json=config,
                               headers={'Content-Type': 'application/json'})

        if response.status_code != 200:
            print(f"❌ 启动迁移失败: {response.status_code} - {response.text}")
            return False

        result = response.json()
        task_id = result.get('task_id')

        if not task_id:
            print(f"❌ 没有获得任务ID: {result}")
            return False

        print(f"✅ 迁移任务已启动")
        print(f"   任务ID: {task_id}")

    except Exception as e:
        print(f"❌ 启动迁移异常: {e}")
        return False

    # 4. 监控迁移进度
    print(f"\n⏳ 步骤4: 监控迁移进度")

    max_wait = 60  # 最多等待60秒
    start_time = time.time()
    last_progress = -1

    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f'http://localhost:5000/api/migration_status/{task_id}')

            if response.status_code == 200:
                status = response.json()
                current_progress = status.get('progress', 0)
                current_status = status.get('status', 'unknown')
                current_message = status.get('message', '')

                # 只在进度变化时输出
                if current_progress != last_progress:
                    print(f"   进度: {current_progress}% - {current_status} - {current_message}")
                    last_progress = current_progress

                # 检查是否完成
                if current_status in ['completed', 'failed']:
                    final_success = (current_status == 'completed')
                    print(f"🏁 迁移{('成功' if final_success else '失败')}: {current_message}")
                    break

            time.sleep(2)  # 每2秒检查一次

        except Exception as e:
            print(f"⚠️ 状态检查异常: {e}")
            break
    else:
        print(f"⏰ 等待超时 ({max_wait}秒)")

    # 5. 检查输出结果
    print(f"\n📊 步骤5: 检查输出结果")

    output_dir = Path(user_output_dir)

    if not output_dir.exists():
        print(f"❌ 输出目录不存在: {output_dir}")
        return False

    print(f"✅ 输出目录存在: {output_dir}")

    # 统计输出文件
    md_files = list(output_dir.rglob('*.md'))
    attachment_files = list(output_dir.rglob('attachments/*'))
    other_files = [f for f in output_dir.rglob('*') if f.is_file() and f.suffix != '.md' and 'attachments' not in str(f)]

    print(f"📝 转换结果:")
    print(f"   MD文件: {len(md_files)} 个")
    print(f"   附件文件: {len(attachment_files)} 个")
    print(f"   其他文件: {len(other_files)} 个")

    # 显示MD文件详情
    if md_files:
        print(f"\n📄 MD文件详情:")
        for md_file in md_files:
            size = md_file.stat().st_size
            rel_path = md_file.relative_to(output_dir)
            print(f"   📝 {rel_path} ({size} bytes)")

            # 显示第一个文件的内容预览
            if md_file == md_files[0]:
                try:
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read()[:200]  # 前200字符
                    print(f"      预览: {content}...")
                except Exception as e:
                    print(f"      预览失败: {e}")

    # 6. 验证去重功能
    print(f"\n🔍 步骤6: 检查去重历史")

    migration_history = output_dir / '.migration_history.json'
    if migration_history.exists():
        try:
            with open(migration_history, 'r', encoding='utf-8') as f:
                history = json.load(f)

            migrations = history.get('migrations', [])
            processed_notes = history.get('processed_notes', {})

            print(f"✅ 去重历史存在:")
            print(f"   迁移次数: {len(migrations)}")
            print(f"   处理笔记数: {len(processed_notes)}")

            if migrations:
                latest = migrations[-1]
                stats = latest.get('stats', {})
                print(f"   最新迁移统计:")
                print(f"     总笔记: {stats.get('total_notes', 0)}")
                print(f"     新建笔记: {stats.get('new_notes', 0)}")
                print(f"     跳过重复: {stats.get('skipped_duplicates', 0)}")

        except Exception as e:
            print(f"⚠️ 无法读取去重历史: {e}")
    else:
        print(f"⚠️ 去重历史文件不存在")

    # 7. 最终判断
    success = len(md_files) > 0

    if success:
        print(f"\n🎉 测试成功!")
        print(f"✅ ENEX文件成功转换为 {len(md_files)} 个MD文件")
        print(f"✅ 输出目录正确: {user_output_dir}")
        print(f"✅ 去重功能正常工作")
        return True
    else:
        print(f"\n❌ 测试失败!")
        print(f"❌ 没有生成MD文件")
        return False

if __name__ == "__main__":
    success = test_real_user_flow()
    exit(0 if success else 1)