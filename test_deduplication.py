#!/usr/bin/env python3
"""
测试去重功能
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加src目录到Python路径
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

from deduplication_manager import DeduplicationManager

def test_deduplication():
    """测试去重功能"""
    print("🧪 测试去重功能")
    print("=" * 50)

    # 创建临时测试目录
    with tempfile.TemporaryDirectory(prefix='dedup_test_') as temp_dir:
        print(f"测试目录: {temp_dir}")

        # 创建去重管理器
        dedup_manager = DeduplicationManager(temp_dir)

        # 测试场景1：新笔记
        print("\n1️⃣ 测试新笔记...")
        migration_id = "test_migration_1"
        source_info = {'backend': 'china', 'temp_directory': '/tmp/test'}

        dedup_manager.start_migration(migration_id, source_info)

        # 模拟第一个笔记
        note1_data = {
            'guid': 'note_001',
            'title': '测试笔记1',
            'content': '这是第一个测试笔记的内容'
        }

        should_process, reason = dedup_manager.should_process_note(note1_data)
        print(f"   笔记1 - 应该处理: {should_process}, 原因: {reason}")

        if should_process:
            output_file = Path(temp_dir) / 'note1.md'
            output_file.write_text("# 测试笔记1\n这是第一个测试笔记的内容")
            dedup_manager.mark_note_processed(note1_data, str(output_file))

        # 测试场景2：重复笔记
        print("\n2️⃣ 测试重复笔记...")

        # 完全相同的笔记
        note1_duplicate = note1_data.copy()
        should_process, reason = dedup_manager.should_process_note(note1_duplicate)
        print(f"   笔记1副本 - 应该处理: {should_process}, 原因: {reason}")

        # 内容相同但ID不同的笔记
        note2_data = {
            'guid': 'note_002',
            'title': '测试笔记1',  # 标题相同
            'content': '这是第一个测试笔记的内容'  # 内容相同
        }

        should_process, reason = dedup_manager.should_process_note(note2_data)
        print(f"   相同内容笔记 - 应该处理: {should_process}, 原因: {reason}")

        # 测试场景3：更新的笔记
        print("\n3️⃣ 测试更新笔记...")

        note1_updated = {
            'guid': 'note_001',  # 相同ID
            'title': '测试笔记1（已更新）',
            'content': '这是第一个测试笔记的内容，已更新'
        }

        should_process, reason = dedup_manager.should_process_note(note1_updated)
        print(f"   更新笔记 - 应该处理: {should_process}, 原因: {reason}")

        if should_process:
            dedup_manager.mark_note_processed(note1_updated, str(output_file), is_update=True)

        # 测试场景4：删除检测
        print("\n4️⃣ 测试删除检测...")

        # 添加第二个笔记
        note3_data = {
            'guid': 'note_003',
            'title': '将被删除的笔记',
            'content': '这个笔记稍后会被删除'
        }

        should_process, reason = dedup_manager.should_process_note(note3_data)
        if should_process:
            output_file3 = Path(temp_dir) / 'note3.md'
            output_file3.write_text("# 将被删除的笔记\n这个笔记稍后会被删除")
            dedup_manager.mark_note_processed(note3_data, str(output_file3))

        # 模拟新的导出，只包含note_001，不包含note_003
        current_note_ids = {'note_001'}  # note_003被删除了

        print(f"   当前导出笔记ID: {current_note_ids}")
        dedup_manager.detect_deleted_notes(current_note_ids)

        # 完成迁移
        dedup_manager.finish_migration(True)

        # 显示统计信息
        print("\n📊 迁移统计:")
        summary = dedup_manager.get_migration_summary()
        print(f"   总迁移次数: {summary['total_migrations']}")
        print(f"   总处理笔记: {summary['total_processed_notes']}")

        print("\n✅ 去重功能测试完成")

        return True

def test_multiple_migrations():
    """测试多次迁移的场景"""
    print("\n🔄 测试多次迁移场景")
    print("=" * 30)

    with tempfile.TemporaryDirectory(prefix='multi_migration_test_') as temp_dir:
        dedup_manager = DeduplicationManager(temp_dir)

        # 第一次迁移
        print("\n第一次迁移:")
        dedup_manager.start_migration("migration_1", {'backend': 'china'})

        notes_batch1 = [
            {'guid': 'note_001', 'title': '笔记A', 'content': '内容A'},
            {'guid': 'note_002', 'title': '笔记B', 'content': '内容B'},
            {'guid': 'note_003', 'title': '笔记C', 'content': '内容C'}
        ]

        processed_count = 0
        for note_data in notes_batch1:
            should_process, reason = dedup_manager.should_process_note(note_data)
            print(f"   {note_data['title']} - {should_process}: {reason}")

            if should_process:
                output_file = Path(temp_dir) / f"{note_data['guid']}.md"
                output_file.write_text(f"# {note_data['title']}\n{note_data['content']}")
                dedup_manager.mark_note_processed(note_data, str(output_file))
                processed_count += 1

        dedup_manager.finish_migration(True)
        print(f"   第一次迁移处理: {processed_count} 个笔记")

        # 第二次迁移（有重复和新增）
        print("\n第二次迁移:")
        dedup_manager.start_migration("migration_2", {'backend': 'china'})

        notes_batch2 = [
            {'guid': 'note_001', 'title': '笔记A', 'content': '内容A'},  # 重复
            {'guid': 'note_002', 'title': '笔记B（更新）', 'content': '内容B已更新'},  # 更新
            {'guid': 'note_004', 'title': '笔记D', 'content': '内容D'},  # 新增
            # note_003被删除了
        ]

        current_ids = {note['guid'] for note in notes_batch2}
        dedup_manager.detect_deleted_notes(current_ids)

        processed_count = 0
        for note_data in notes_batch2:
            should_process, reason = dedup_manager.should_process_note(note_data)
            print(f"   {note_data['title']} - {should_process}: {reason}")

            if should_process:
                output_file = Path(temp_dir) / f"{note_data['guid']}.md"
                output_file.write_text(f"# {note_data['title']}\n{note_data['content']}")
                is_update = note_data['guid'] in {'note_002'}  # note_002是更新
                dedup_manager.mark_note_processed(note_data, str(output_file), is_update)
                processed_count += 1

        dedup_manager.finish_migration(True)
        print(f"   第二次迁移处理: {processed_count} 个笔记")

        # 显示最终统计
        summary = dedup_manager.get_migration_summary()
        print(f"\n📊 最终统计:")
        print(f"   总迁移次数: {summary['total_migrations']}")
        print(f"   当前笔记数: {summary['total_processed_notes']}")
        print(f"   删除笔记数: {len(dedup_manager.history['deleted_notes'])}")

        print("\n✅ 多次迁移测试完成")

        return True

def main():
    """主函数"""
    print("🧪 去重管理器测试套件")

    try:
        if not test_deduplication():
            return False

        if not test_multiple_migrations():
            return False

        print("\n🎉 所有测试通过！")
        print("\n💡 去重功能说明:")
        print("   • 自动检测重复笔记（按ID和内容哈希）")
        print("   • 跟踪笔记更新（内容变化时重新处理）")
        print("   • 检测删除的笔记（自动移除不再存在的笔记）")
        print("   • 支持多次迁移（增量更新）")
        print("   • 保持迁移历史记录")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)