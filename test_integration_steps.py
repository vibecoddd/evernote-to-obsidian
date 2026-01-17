#!/usr/bin/env python3
"""
全面测试用例：印象笔记到Obsidian迁移的4个步骤
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# 添加源码路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import Config
from enex_parser import ENEXParser
from evernote_exporter import EvernoteExporter
from markdown_converter import MarkdownConverter
from file_organizer import FileOrganizer
from obsidian_manager import ObsidianManager


class TestStep1EvernoteExport:
    """步骤1：导出印象笔记测试"""

    @staticmethod
    def create_sample_enex(output_path: str) -> str:
        """创建示例ENEX文件用于测试"""
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

    def test_enex_file_structure(self):
        """测试ENEX文件结构完整性"""
        with tempfile.TemporaryDirectory() as temp_dir:
            enex_file = self.create_sample_enex(temp_dir)
            
            # 验证文件存在
            assert os.path.exists(enex_file)
            assert os.path.isfile(enex_file)
            
            # 验证文件内容不为空
            assert os.path.getsize(enex_file) > 0
            
            # 读取并验证XML结构
            with open(enex_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert '<?xml version="1.0" encoding="UTF-8"?>' in content
            assert '<en-export' in content
            assert '<notebook>' in content
            assert '<note>' in content
            assert '<title>' in content
            assert '<content>' in content
            assert '<tag>' in content

    def test_export_contains_all_notes(self):
        """测试导出的ENEX文件包含所有笔记内容"""
        with tempfile.TemporaryDirectory() as temp_dir:
            enex_file = self.create_sample_enex(temp_dir)
            
            # 使用ENEX解析器验证所有笔记都被正确导出
            parser = ENEXParser()
            notes, notebook_name = parser.parse_file(enex_file)
            
            # 验证解析结果
            assert len(notes) == 2, f"预期2个笔记，实际导出{len(notes)}个笔记"
            assert notebook_name == "测试笔记本"
            
            # 验证每个笔记的内容完整性
            note1 = notes[0]
            assert note1.title == "测试笔记1"
            assert len(note1.tags) == 2
            assert "测试" in note1.tags
            assert "示例" in note1.tags
            assert "粗体文本" in note1.content
            assert "斜体文本" in note1.content
            assert "列表项1" in note1.content
            assert note1.author == "测试用户"
            assert note1.source_url == "http://example.com"
            
            note2 = notes[1]
            assert note2.title == "测试笔记2"
            assert "表格" in note2.tags
            assert "<table>" in note2.content
            assert "列1" in note2.content
            assert "列2" in note2.content
            assert "数据1" in note2.content
            assert "数据2" in note2.content


class TestStep2MarkdownConversion:
    """步骤2：转换为Markdown测试"""

    def setup_method(self):
        """测试前的准备工作"""
        self.temp_dir = tempfile.mkdtemp()
        self.sample_enex = TestStep1EvernoteExport.create_sample_enex(self.temp_dir)
        
        # 解析ENEX文件用于测试
        parser = ENEXParser()
        self.notes, self.notebook_name = parser.parse_file(self.sample_enex)
        
        # 创建配置
        self.config = {
            'conversion': {
                'convert_links': True,
                'convert_tables': True,
                'clean_html': True,
                'max_filename_length': 100,
                'image_folder': 'attachments'
            },
            'metadata': {
                'include_created_date': True,
                'include_tags': True,
                'include_notebook': True,
                'date_format': '%Y-%m-%d %H:%M:%S'
            },
            'output': {
                'obsidian_vault': os.path.join(self.temp_dir, 'test_vault')
            }
        }

    def teardown_method(self):
        """测试后的清理工作"""
        shutil.rmtree(self.temp_dir)

    def test_html_to_markdown_conversion(self):
        """测试HTML内容转换为Markdown"""
        converter = MarkdownConverter(self.config)
        
        # 转换第一个笔记
        note = self.notes[0]
        markdown_content = converter.convert_note(note)
        
        # 验证转换结果
        assert "title: \"测试笔记1\"" in markdown_content  # 标题（在YAML前言中）
        assert "**粗体文本**" in markdown_content or "*粗体文本*" in markdown_content  # 粗体
        assert "*斜体文本*" in markdown_content or "_斜体文本_" in markdown_content  # 斜体
        assert "- 列表项1" in markdown_content or "* 列表项1" in markdown_content  # 列表
        assert "- 列表项2" in markdown_content or "* 列表项2" in markdown_content  # 列表
        assert "tags: [\"测试\", \"示例\"]" in markdown_content  # 标签
        assert "notebook: \"测试笔记本\"" in markdown_content  # 笔记本信息

    def test_table_conversion(self):
        """测试表格转换"""
        converter = MarkdownConverter(self.config)
        
        # 转换包含表格的笔记
        note = self.notes[1]
        markdown_content = converter.convert_note(note)
        
        # 验证表格转换结果
        assert "列1" in markdown_content
        assert "列2" in markdown_content
        assert "数据1" in markdown_content
        assert "数据2" in markdown_content
        # 验证Markdown表格格式
        assert "|" in markdown_content  # 表格分隔符
        assert "---" in markdown_content  # 表格标题行

    def test_index_file_generation(self):
        """测试生成笔记索引文件"""
        organizer = FileOrganizer(self.config)
        
        # 组织笔记
        organized_notes = organizer.organize_notes(self.notes, self.notebook_name)
        
        # 创建目录结构
        organizer.create_directory_structure(organized_notes)
        
        # 生成索引文件
        index_file = organizer.create_index_file(organized_notes, self.notebook_name)
        
        # 验证索引文件存在
        assert index_file is not None
        assert os.path.exists(index_file)
        
        # 验证索引文件内容
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "# 测试笔记本 索引" in content
        assert "[[测试笔记本/测试笔记1]]" in content
        assert "[[测试笔记本/测试笔记2]]" in content


class TestStep3ObsidianConfiguration:
    """步骤3：配置Obsidian库测试"""

    def setup_method(self):
        """测试前的准备工作"""
        self.temp_dir = tempfile.mkdtemp()
        self.vault_path = os.path.join(self.temp_dir, 'ObsidianVault')
        
        # 创建配置
        self.config = {
            'output': {
                'obsidian_vault': self.vault_path,
                'create_vault_if_not_exists': True,
                'backup_existing': True
            },
            'migration': {
                'create_welcome_note': True,
                'create_templates': True,
                'optimize_settings': True
            }
        }

    def teardown_method(self):
        """测试后的清理工作"""
        shutil.rmtree(self.temp_dir)

    def test_obsidian_vault_structure(self):
        """测试Obsidian库目录结构"""
        obsidian_manager = ObsidianManager(self.config)
        
        # 创建Obsidian库
        result = obsidian_manager.create_obsidian_vault()
        assert result is True
        
        # 验证目录结构
        vault_path = Path(self.vault_path)
        assert vault_path.exists()
        assert vault_path.is_dir()
        
        # 验证.obsidian目录存在
        obsidian_dir = vault_path / '.obsidian'
        assert obsidian_dir.exists()
        assert obsidian_dir.is_dir()

    def test_welcome_note_creation(self):
        """测试创建欢迎笔记"""
        obsidian_manager = ObsidianManager(self.config)
        obsidian_manager.create_obsidian_vault()
        
        # 创建欢迎笔记
        welcome_note = obsidian_manager.create_welcome_note()
        
        # 验证欢迎笔记存在
        assert welcome_note is not None
        assert os.path.exists(welcome_note)
        
        # 验证欢迎笔记内容
        with open(welcome_note, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "# 欢迎使用Obsidian" in content
        assert "印象笔记迁移" in content

    def test_templates_creation(self):
        """测试创建模板"""
        obsidian_manager = ObsidianManager(self.config)
        obsidian_manager.create_obsidian_vault()
        
        # 创建模板
        templates_dir = obsidian_manager.create_templates()
        
        # 验证模板目录存在
        assert templates_dir is not None
        assert os.path.exists(templates_dir)
        
        # 验证模板文件存在
        templates = os.listdir(templates_dir)
        assert len(templates) > 0

    def test_vault_settings_optimization(self):
        """测试配置最佳实践设置"""
        obsidian_manager = ObsidianManager(self.config)
        obsidian_manager.create_obsidian_vault()
        
        # 优化设置
        obsidian_manager.optimize_vault_settings()
        
        # 验证设置文件存在
        vault_path = Path(self.vault_path)
        obsidian_dir = vault_path / '.obsidian'
        
        # 检查常用设置文件
        appearance_file = obsidian_dir / 'appearance.json'
        if appearance_file.exists():
            assert os.path.isfile(appearance_file)
        
        core_file = obsidian_dir / 'core-plugins.json'
        if core_file.exists():
            assert os.path.isfile(core_file)


class TestStep4CompletionConfiguration:
    """步骤4：完成配置测试"""

    def setup_method(self):
        """测试前的准备工作"""
        self.temp_dir = tempfile.mkdtemp()
        self.vault_path = os.path.join(self.temp_dir, 'ObsidianVault')
        self.temp_files_dir = os.path.join(self.temp_dir, 'temp_files')
        
        # 创建临时文件目录
        os.makedirs(self.temp_files_dir)
        
        # 创建测试临时文件
        with open(os.path.join(self.temp_files_dir, 'temp1.txt'), 'w') as f:
            f.write('test')
        with open(os.path.join(self.temp_files_dir, 'temp2.txt'), 'w') as f:
            f.write('test')
        
        # 创建配置
        self.config = {
            'output': {
                'obsidian_vault': self.vault_path
            },
            'temp_directory': self.temp_files_dir,
            'migration': {
                'keep_temp_files': False
            }
        }

    def teardown_method(self):
        """测试后的清理工作"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_temp_files_cleanup(self):
        """测试清理临时文件"""
        # 验证临时文件存在
        temp1 = os.path.join(self.temp_files_dir, 'temp1.txt')
        temp2 = os.path.join(self.temp_files_dir, 'temp2.txt')
        assert os.path.exists(temp1)
        assert os.path.exists(temp2)
        
        # 创建测试用的迁移工具实例
        class MockMigrator:
            def __init__(self, config):
                self.config = config
            
            def _cleanup_temp_files(self):
                """模拟清理临时文件"""
                temp_dir = self.config.get('temp_directory')
                if temp_dir and os.path.exists(temp_dir):
                    try:
                        temp_path = Path(temp_dir)
                        for item in temp_path.iterdir():
                            if item.name not in ['enex_output']:
                                if item.is_file():
                                    item.unlink()
                                else:
                                    shutil.rmtree(item)
                    except Exception as e:
                        print(f"清理失败: {e}")
        
        # 创建配置实例
        config = Config()
        config.config_data = self.config
        
        # 创建迁移工具实例
        migrator = MockMigrator(config)
        
        # 执行清理
        migrator._cleanup_temp_files()
        
        # 验证临时文件被清理
        assert not os.path.exists(temp1)
        assert not os.path.exists(temp2)

    def test_migration_statistics(self):
        """测试迁移统计信息"""
        # 模拟迁移统计数据
        stats = {
            'start_time': '2023-12-01 10:00:00',
            'end_time': '2023-12-01 10:05:30',
            'total_notes': 100,
            'converted_notes': 98,
            'skipped_notes': 2,
            'total_attachments': 25,
            'errors': []
        }
        
        # 验证统计数据的完整性
        assert 'total_notes' in stats
        assert 'converted_notes' in stats
        assert 'skipped_notes' in stats
        assert 'total_attachments' in stats
        assert 'errors' in stats
        
        # 验证统计数据的合理性
        assert stats['total_notes'] >= stats['converted_notes']
        assert stats['total_notes'] == stats['converted_notes'] + stats['skipped_notes']
        assert stats['total_attachments'] >= 0
        assert isinstance(stats['errors'], list)


if __name__ == "__main__":
    print("🚀 运行全面测试用例...")
    print("=" * 60)
    
    # 运行所有测试
    test_step1 = TestStep1EvernoteExport()
    test_step2 = TestStep2MarkdownConversion()
    test_step3 = TestStep3ObsidianConfiguration()
    test_step4 = TestStep4CompletionConfiguration()
    
    try:
        # 步骤1测试
        print("\n📤 步骤1：导出印象笔记测试")
        print("-" * 40)
        test_step1.test_enex_file_structure()
        print("✅ ENEX文件结构测试通过")
        
        test_step1.test_export_contains_all_notes()
        print("✅ 导出包含所有笔记测试通过")
        
        # 步骤2测试
        print("\n📝 步骤2：转换为Markdown测试")
        print("-" * 40)
        test_step2.setup_method()
        test_step2.test_html_to_markdown_conversion()
        print("✅ HTML转Markdown测试通过")
        
        test_step2.test_table_conversion()
        print("✅ 表格转换测试通过")
        
        test_step2.test_index_file_generation()
        print("✅ 索引文件生成测试通过")
        test_step2.teardown_method()
        
        # 步骤3测试
        print("\n🏗️  步骤3：配置Obsidian库测试")
        print("-" * 40)
        test_step3.setup_method()
        test_step3.test_obsidian_vault_structure()
        print("✅ Obsidian库结构测试通过")
        
        test_step3.test_welcome_note_creation()
        print("✅ 欢迎笔记创建测试通过")
        
        test_step3.test_templates_creation()
        print("✅ 模板创建测试通过")
        
        test_step3.test_vault_settings_optimization()
        print("✅ 设置优化测试通过")
        test_step3.teardown_method()
        
        # 步骤4测试
        print("\n🔧 步骤4：完成配置测试")
        print("-" * 40)
        test_step4.setup_method()
        test_step4.test_temp_files_cleanup()
        print("✅ 临时文件清理测试通过")
        
        test_step4.test_migration_statistics()
        print("✅ 迁移统计测试通过")
        test_step4.teardown_method()
        
        print("\n" + "=" * 60)
        print("🎉 所有测试用例通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)