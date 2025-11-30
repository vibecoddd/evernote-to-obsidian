#!/usr/bin/env python3
"""
基本功能测试脚本
"""

import os
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

# 添加源码路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import Config
from enex_parser import ENEXParser, Note
from markdown_converter import MarkdownConverter
from file_organizer import FileOrganizer
from sync_manager import SyncManager


def create_sample_enex(output_path: str) -> str:
    """
    创建示例ENEX文件

    Args:
        output_path: 输出路径

    Returns:
        ENEX文件路径
    """
    enex_content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-export SYSTEM "http://xml.evernote.com/pub/evernote-export3.dtd">
<en-export export-date="20231201T120000Z" application="Evernote" version="10.50.16">
<notebook>
<name>测试笔记本</name>
<note>
<title>测试笔记1</title>
<content><![CDATA[<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note>
<div>这是一个测试笔记的内容。</div>
<div><br/></div>
<div><b>粗体文本</b></div>
<div><i>斜体文本</i></div>
<div><br/></div>
<ul>
<li>列表项1</li>
<li>列表项2</li>
</ul>
<div><br/></div>
<en-todo checked="false"/>待办事项1<br/>
<en-todo checked="true"/>已完成事项<br/>
</en-note>]]></content>
<created>20231201T100000Z</created>
<updated>20231201T110000Z</updated>
<tag>测试</tag>
<tag>示例</tag>
<note-attributes>
<source-url>http://example.com</source-url>
<author>测试用户</author>
</note-attributes>
</note>
<note>
<title>测试笔记2</title>
<content><![CDATA[<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note>
<div>第二个测试笔记。</div>
<div><br/></div>
<table>
<tr>
<td>列1</td>
<td>列2</td>
</tr>
<tr>
<td>数据1</td>
<td>数据2</td>
</tr>
</table>
</en-note>]]></content>
<created>20231201T120000Z</created>
<updated>20231201T130000Z</updated>
<tag>表格</tag>
</note>
</notebook>
</en-export>'''

    enex_file = os.path.join(output_path, "test_notebook.enex")
    with open(enex_file, 'w', encoding='utf-8') as f:
        f.write(enex_content)

    return enex_file


def test_enex_parser():
    """测试ENEX解析器"""
    print("🔍 测试ENEX解析器...")

    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建测试ENEX文件
        enex_file = create_sample_enex(temp_dir)

        # 测试解析
        parser = ENEXParser()
        notes, notebook_name = parser.parse_file(enex_file)

        # 验证结果
        assert len(notes) == 2, f"Expected 2 notes, got {len(notes)}"
        assert notebook_name == "测试笔记本", f"Expected '测试笔记本', got '{notebook_name}'"

        note1 = notes[0]
        assert note1.title == "测试笔记1"
        assert len(note1.tags) == 2
        assert "测试" in note1.tags
        assert note1.author == "测试用户"

        print("✅ ENEX解析器测试通过")


def test_markdown_converter():
    """测试Markdown转换器"""
    print("📝 测试Markdown转换器...")

    # 创建配置
    config = {
        'conversion': {
            'convert_links': True,
            'convert_tables': True,
            'clean_html': True,
            'max_filename_length': 100
        },
        'metadata': {
            'include_created_date': True,
            'include_tags': True,
            'include_notebook': True,
            'date_format': '%Y-%m-%d %H:%M:%S'
        }
    }

    converter = MarkdownConverter(config)

    # 创建测试笔记
    from datetime import datetime
    note = Note(
        title="测试笔记",
        content="<div>这是<b>粗体</b>和<i>斜体</i>文本</div>",
        tags=["标签1", "标签2"],
        notebook="测试笔记本",
        created=datetime.now(),
        updated=datetime.now()
    )

    # 转换为Markdown
    markdown = converter.convert_note(note)

    # 验证结果
    assert "title:" in markdown
    assert "tags:" in markdown
    assert "**粗体**" in markdown or "*粗体*" in markdown
    assert "*斜体*" in markdown or "_斜体_" in markdown

    print("✅ Markdown转换器测试通过")


def test_file_organizer():
    """测试文件组织器"""
    print("📁 测试文件组织器...")

    with tempfile.TemporaryDirectory() as temp_dir:
        config = {
            'output': {
                'obsidian_vault': temp_dir,
                'create_vault_if_not_exists': True
            },
            'file_organization': {
                'organize_by_notebook': True,
                'handle_duplicates': 'rename'
            },
            'conversion': {
                'image_folder': 'attachments',
                'max_filename_length': 100
            }
        }

        organizer = FileOrganizer(config)

        # 创建测试笔记
        from datetime import datetime
        notes = [
            Note(title="笔记1", content="内容1", notebook="测试笔记本"),
            Note(title="笔记2", content="内容2", notebook="测试笔记本")
        ]

        # 组织笔记
        organized = organizer.organize_notes(notes, "测试笔记本")

        # 创建目录结构
        organizer.create_directory_structure(organized)

        # 验证结果
        assert len(organized) == 2
        vault_path = Path(temp_dir)
        assert (vault_path / "测试笔记本").exists()
        assert (vault_path / "attachments").exists()

        print("✅ 文件组织器测试通过")


def test_config():
    """测试配置管理"""
    print("⚙️ 测试配置管理...")

    # 创建默认配置
    config = Config()

    # 测试基本功能
    assert config.get('logging.level') == 'INFO'
    config.set('logging.level', 'DEBUG')
    assert config.get('logging.level') == 'DEBUG'

    # 测试嵌套键
    config.set('test.nested.value', 'test_value')
    assert config.get('test.nested.value') == 'test_value'

    print("✅ 配置管理测试通过")


def test_integration():
    """集成测试"""
    print("🔗 运行集成测试...")

    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建测试ENEX文件
        enex_file = create_sample_enex(temp_dir)

        # 设置输出目录
        vault_dir = os.path.join(temp_dir, "test_vault")

        # 创建配置
        config_data = {
            'input': {
                'enex_files': [enex_file]
            },
            'output': {
                'obsidian_vault': vault_dir,
                'create_vault_if_not_exists': True
            },
            'conversion': {
                'convert_tables': True,
                'extract_images': True,
                'image_folder': 'attachments'
            },
            'metadata': {
                'include_created_date': True,
                'include_tags': True,
                'include_notebook': True
            },
            'file_organization': {
                'organize_by_notebook': True
            },
            'sync': {
                'incremental': False
            }
        }

        config = Config()
        config.config_data = config_data

        # 初始化组件
        parser = ENEXParser()
        converter = MarkdownConverter(config.get_all())
        organizer = FileOrganizer(config.get_all())

        # 执行转换流程
        notes, notebook_name = parser.parse_file(enex_file)
        organized_notes = organizer.organize_notes(notes, notebook_name)
        organizer.create_directory_structure(organized_notes)

        # 转换并保存笔记
        for note, file_path in organized_notes:
            markdown_content = converter.convert_note(note)
            organizer.save_note(note, file_path, markdown_content)

        # 创建索引
        organizer.create_index_file(organized_notes, notebook_name)

        # 验证结果
        vault_path = Path(vault_dir)
        notebook_dir = vault_path / "测试笔记本"

        assert vault_path.exists()
        assert notebook_dir.exists()
        assert (vault_path / "attachments").exists()

        # 检查Markdown文件
        md_files = list(notebook_dir.glob("*.md"))
        assert len(md_files) >= 2  # 至少有2个笔记文件

        # 检查索引文件
        index_files = list(vault_path.glob("*Index.md"))
        assert len(index_files) >= 1

        print("✅ 集成测试通过")


def main():
    """主测试函数"""
    print("🚀 开始基本功能测试")
    print("=" * 50)

    try:
        test_config()
        test_enex_parser()
        test_markdown_converter()
        test_file_organizer()
        test_integration()

        print("=" * 50)
        print("🎉 所有测试通过！")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()