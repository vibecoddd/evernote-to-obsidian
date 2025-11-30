#!/usr/bin/env python3
"""
测试ENEX到MD转换流程
"""

import sys
from pathlib import Path

# 添加src目录到Python路径
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

from enex_parser import ENEXParser
from markdown_converter import MarkdownConverter
from file_organizer import FileOrganizer
from deduplication_manager import DeduplicationManager

def test_conversion():
    """测试完整转换流程"""
    print("🧪 测试ENEX到MD转换流程")
    print("=" * 50)

    # 配置
    output_dir = "/tmp/test_conversion_output"
    enex_file = "/tmp/test_note.enex"

    config = {
        'output': {
            'obsidian_vault': output_dir,
            'note_format': 'md',
            'organize_by': 'notebook'
        },
        'conversion': {
            'preserve_html': False,
            'extract_attachments': True,
            'create_index': True
        }
    }

    try:
        print(f"📁 输出目录: {output_dir}")
        print(f"📄 输入文件: {enex_file}")

        # 1. 初始化组件
        print("\n1️⃣ 初始化组件...")
        parser = ENEXParser()
        converter = MarkdownConverter(config)
        organizer = FileOrganizer(config)
        dedup_manager = DeduplicationManager(output_dir)

        # 2. 开始迁移
        migration_id = "test_migration_conversion"
        source_info = {'backend': 'test', 'file': enex_file}
        dedup_manager.start_migration(migration_id, source_info)

        # 3. 解析ENEX文件
        print("\n2️⃣ 解析ENEX文件...")
        notes, notebook_name = parser.parse_file(enex_file)
        print(f"   笔记本: {notebook_name}")
        print(f"   笔记数: {len(notes)}")

        # 4. 组织笔记结构
        print("\n3️⃣ 组织笔记结构...")
        organized_notes = organizer.organize_notes(notes, notebook_name)
        organizer.create_directory_structure(organized_notes)

        print(f"   组织后笔记数: {len(organized_notes)}")

        # 5. 转换和保存笔记
        print("\n4️⃣ 转换和保存笔记...")
        converted_count = 0
        skipped_count = 0

        current_note_ids = set()

        for note, file_path in organized_notes:
            try:
                print(f"   处理: {note.title}")

                # 检查是否应该处理这个笔记
                note_data = {
                    'guid': note.guid,
                    'title': note.title,
                    'content': note.content
                }

                should_process, reason = dedup_manager.should_process_note(note_data)
                print(f"     去重检查: {should_process} - {reason}")

                if should_process:
                    # 转换为Markdown
                    markdown_content = converter.convert_note(note)

                    # 保存笔记
                    organizer.save_note(note, file_path, markdown_content)

                    # 保存附件
                    if note.attachments:
                        organizer.save_attachments(note)
                        print(f"     附件数: {len(note.attachments)}")

                    # 标记为已处理
                    dedup_manager.mark_note_processed(note_data, str(file_path))
                    converted_count += 1

                    print(f"     ✅ 转换完成: {Path(file_path).name}")

                else:
                    dedup_manager.mark_note_skipped(note_data, reason)
                    skipped_count += 1
                    print(f"     ⏭️ 跳过")

                # 记录笔记ID
                if note.guid:
                    current_note_ids.add(note.guid)

            except Exception as e:
                print(f"     ❌ 转换失败: {e}")
                skipped_count += 1

        # 6. 检测删除的笔记
        print("\n5️⃣ 检测删除的笔记...")
        dedup_manager.detect_deleted_notes(current_note_ids)

        # 7. 创建索引文件
        print("\n6️⃣ 创建索引文件...")
        organizer.create_index_file(organized_notes, notebook_name)

        # 8. 完成迁移
        dedup_manager.finish_migration(True)

        # 9. 显示结果
        print("\n📊 转换结果:")
        print(f"   总笔记数: {len(notes)}")
        print(f"   转换成功: {converted_count}")
        print(f"   跳过笔记: {skipped_count}")

        # 检查输出文件
        output_path = Path(output_dir)
        if output_path.exists():
            md_files = list(output_path.rglob('*.md'))
            print(f"   输出文件: {len(md_files)} 个")

            for md_file in md_files:
                size = md_file.stat().st_size
                print(f"     📝 {md_file.name} ({size} bytes)")

            # 显示目录结构
            print(f"\n📁 目录结构:")
            for item in output_path.rglob('*'):
                if item.is_file():
                    rel_path = item.relative_to(output_path)
                    print(f"     {rel_path}")

        return converted_count > 0

    except Exception as e:
        print(f"❌ 转换测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_conversion()
    sys.exit(0 if success else 1)