#!/usr/bin/env python3
"""
快速开始示例脚本
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加源码路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from evernote2obsidian import EvernoteToObsidianConverter
from config import Config


def create_demo_enex(output_dir: str) -> str:
    """
    创建演示用的ENEX文件

    Args:
        output_dir: 输出目录

    Returns:
        ENEX文件路径
    """
    enex_content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-export SYSTEM "http://xml.evernote.com/pub/evernote-export3.dtd">
<en-export export-date="20231201T120000Z" application="Evernote" version="10.50.16">
<notebook>
<name>我的知识库</name>
<note>
<title>Obsidian使用指南</title>
<content><![CDATA[<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note>
<h1>Obsidian快速入门</h1>
<div><br/></div>
<div><b>什么是Obsidian？</b></div>
<div>Obsidian是一个基于Markdown的知识管理工具，具有以下特点：</div>
<div><br/></div>
<ul>
<li>双向链接</li>
<li>图形化知识网络</li>
<li>插件生态</li>
<li>本地存储</li>
</ul>
<div><br/></div>
<div><b>核心功能：</b></div>
<ol>
<li>笔记编写</li>
<li>链接建立</li>
<li>标签管理</li>
<li>搜索功能</li>
</ol>
<div><br/></div>
<en-todo checked="false"/>学习Markdown语法<br/>
<en-todo checked="true"/>安装Obsidian<br/>
<en-todo checked="false"/>创建第一个笔记<br/>
<div><br/></div>
<div>更多信息请访问：<a href="https://obsidian.md">官方网站</a></div>
</en-note>]]></content>
<created>20231201T100000Z</created>
<updated>20231201T110000Z</updated>
<tag>工具</tag>
<tag>知识管理</tag>
<tag>Obsidian</tag>
<note-attributes>
<author>知识管理专家</author>
<source-url>https://obsidian.md</source-url>
</note-attributes>
</note>
<note>
<title>Markdown语法速查</title>
<content><![CDATA[<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note>
<h1>Markdown基础语法</h1>
<div><br/></div>
<h2>文本格式</h2>
<div><b>粗体</b>：**文本** 或 __文本__</div>
<div><i>斜体</i>：*文本* 或 _文本_</div>
<div><strike>删除线</strike>：~~文本~~</div>
<div><br/></div>
<h2>标题</h2>
<div># 一级标题</div>
<div>## 二级标题</div>
<div>### 三级标题</div>
<div><br/></div>
<h2>列表</h2>
<div><b>无序列表：</b></div>
<ul>
<li>项目1</li>
<li>项目2</li>
<li>项目3</li>
</ul>
<div><br/></div>
<div><b>有序列表：</b></div>
<ol>
<li>第一项</li>
<li>第二项</li>
<li>第三项</li>
</ol>
<div><br/></div>
<h2>表格</h2>
<table>
<tr>
<th>语法</th>
<th>效果</th>
</tr>
<tr>
<td>**粗体**</td>
<td>粗体文本</td>
</tr>
<tr>
<td>*斜体*</td>
<td>斜体文本</td>
</tr>
<tr>
<td>[链接](url)</td>
<td>超链接</td>
</tr>
</table>
<div><br/></div>
<h2>代码</h2>
<div>行内代码：`code`</div>
<div><br/></div>
<div>代码块：</div>
<div>```</div>
<div>function hello() {</div>
<div>  console.log("Hello World!");</div>
<div>}</div>
<div>```</div>
</en-note>]]></content>
<created>20231201T120000Z</created>
<updated>20231201T125000Z</updated>
<tag>Markdown</tag>
<tag>语法</tag>
<tag>参考</tag>
</note>
<note>
<title>项目管理模板</title>
<content><![CDATA[<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note>
<h1>项目管理模板</h1>
<div><br/></div>
<h2>项目概述</h2>
<div><b>项目名称：</b>印象笔记迁移项目</div>
<div><b>项目目标：</b>将所有印象笔记内容迁移到Obsidian</div>
<div><b>开始日期：</b>2023年12月1日</div>
<div><b>预计完成：</b>2023年12月15日</div>
<div><br/></div>
<h2>任务清单</h2>
<h3>第一阶段：准备工作</h3>
<en-todo checked="true"/>导出印象笔记数据<br/>
<en-todo checked="true"/>安装同步工具<br/>
<en-todo checked="false"/>配置同步参数<br/>
<div><br/></div>
<h3>第二阶段：数据迁移</h3>
<en-todo checked="false"/>运行预览模式<br/>
<en-todo checked="false"/>执行数据转换<br/>
<en-todo checked="false"/>验证转换结果<br/>
<div><br/></div>
<h3>第三阶段：优化整理</h3>
<en-todo checked="false"/>整理文件夹结构<br/>
<en-todo checked="false"/>检查链接完整性<br/>
<en-todo checked="false"/>添加标签分类<br/>
<en-todo checked="false"/>创建索引文件<br/>
<div><br/></div>
<h2>注意事项</h2>
<ul>
<li>备份原始数据</li>
<li>分批次处理大量数据</li>
<li>定期检查转换质量</li>
<li>保持文件命名规范</li>
</ul>
<div><br/></div>
<h2>资源链接</h2>
<div><a href="https://github.com/example/evernote2obsidian">工具地址</a></div>
<div><a href="https://obsidian.md">Obsidian官网</a></div>
<div><a href="https://help.obsidian.md">使用文档</a></div>
</en-note>]]></content>
<created>20231201T130000Z</created>
<updated>20231201T135000Z</updated>
<tag>项目管理</tag>
<tag>模板</tag>
<tag>迁移</tag>
</note>
</notebook>
</en-export>'''

    enex_file = os.path.join(output_dir, "demo_knowledge_base.enex")
    with open(enex_file, 'w', encoding='utf-8') as f:
        f.write(enex_content)

    return enex_file


def run_demo():
    """运行演示"""
    print("🚀 印象笔记到Obsidian同步工具 - 快速演示")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 使用临时目录: {temp_dir}")

        # 1. 创建演示ENEX文件
        print("1. 创建演示ENEX文件...")
        enex_file = create_demo_enex(temp_dir)
        print(f"   ✅ 创建演示文件: {os.path.basename(enex_file)}")

        # 2. 设置输出目录
        vault_dir = os.path.join(temp_dir, "DemoObsidianVault")
        print(f"2. 设置输出库: {vault_dir}")

        # 3. 创建配置
        print("3. 创建配置...")
        config = Config()
        config.set('input.enex_files', [enex_file])
        config.set('output.obsidian_vault', vault_dir)
        config.set('output.create_vault_if_not_exists', True)
        config.set('logging.level', 'INFO')
        config.set('logging.console', True)

        # 4. 运行预览模式
        print("\n4. 运行预览模式...")
        print("-" * 40)
        try:
            converter = EvernoteToObsidianConverter()
            converter.config = config

            success, preview_info = converter.run(preview=True)
            if not success:
                print("❌ 预览失败")
                return False

        except Exception as e:
            print(f"❌ 预览过程出错: {e}")
            return False

        # 5. 询问是否继续转换
        print("\n" + "-" * 40)
        user_input = input("是否继续执行转换? (y/N): ").strip().lower()

        if user_input not in ['y', 'yes', '是']:
            print("🛑 用户取消转换")
            return True

        # 6. 执行实际转换
        print("\n5. 执行实际转换...")
        print("-" * 40)
        try:
            success, stats = converter.run(preview=False)
            if not success:
                print("❌ 转换失败")
                return False

        except Exception as e:
            print(f"❌ 转换过程出错: {e}")
            return False

        # 7. 显示结果
        print("\n6. 转换完成！")
        print("-" * 40)

        vault_path = Path(vault_dir)
        if vault_path.exists():
            print(f"📂 Obsidian库路径: {vault_dir}")
            print("\n📋 生成的文件结构:")

            # 显示目录结构
            def show_tree(path, prefix="", max_depth=3, current_depth=0):
                if current_depth > max_depth:
                    return

                items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
                for i, item in enumerate(items):
                    is_last = i == len(items) - 1
                    current_prefix = "└── " if is_last else "├── "
                    print(f"{prefix}{current_prefix}{item.name}")

                    if item.is_dir() and current_depth < max_depth:
                        next_prefix = prefix + ("    " if is_last else "│   ")
                        show_tree(item, next_prefix, max_depth, current_depth + 1)

            show_tree(vault_path)

            # 显示示例文件内容
            md_files = list(vault_path.rglob("*.md"))
            if md_files and not any("Index" in f.name for f in md_files[:1]):
                print(f"\n📄 示例文件内容 ({md_files[0].name}):")
                print("-" * 30)
                try:
                    with open(md_files[0], 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 显示前20行
                        lines = content.split('\n')[:20]
                        print('\n'.join(lines))
                        if len(content.split('\n')) > 20:
                            print("...")
                except Exception as e:
                    print(f"无法读取文件: {e}")

        print("\n🎉 演示完成！")
        print("\n💡 下一步:")
        print("   1. 将生成的文件复制到您的实际Obsidian库中")
        print("   2. 在Obsidian中打开查看效果")
        print("   3. 根据需要调整配置后处理您的真实数据")

        return True


def show_real_usage():
    """显示实际使用方法"""
    print("\n" + "=" * 60)
    print("📚 实际使用方法")
    print("=" * 60)

    print("\n1️⃣ 准备ENEX文件:")
    print("   - 从印象笔记导出ENEX格式文件")
    print("   - 或使用evernote-backup工具")

    print("\n2️⃣ 配置工具:")
    print("   - 编辑config.yaml文件")
    print("   - 设置输入文件路径和输出库路径")

    print("\n3️⃣ 运行转换:")
    print("   # 预览模式")
    print("   python src/evernote2obsidian.py --config config.yaml --preview")
    print()
    print("   # 执行转换")
    print("   python src/evernote2obsidian.py --config config.yaml")

    print("\n4️⃣ 命令行快速使用:")
    print("   python src/evernote2obsidian.py \\")
    print("     --input /path/to/enex/files \\")
    print("     --output /path/to/obsidian/vault")

    print("\n5️⃣ 其他选项:")
    print("   --verbose      # 详细输出")
    print("   --reset        # 重置同步状态")
    print("   --help         # 显示帮助")


def main():
    """主函数"""
    try:
        success = run_demo()
        if success:
            show_real_usage()
        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n\n🛑 演示已被用户取消")
        return 1
    except Exception as e:
        print(f"\n❌ 演示过程出现错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)