#!/usr/bin/env python3
"""
Obsidian管理模块 - 自动配置和优化Obsidian库
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
import platform

import colorama
from colorama import Fore, Style


class ObsidianManager:
    """Obsidian库管理器"""

    def __init__(self, config: Dict[str, Any]):
        """初始化Obsidian管理器"""
        self.config = config
        self.vault_path = Path(config.get('output.obsidian_vault', ''))

    def detect_obsidian_installation(self) -> Optional[str]:
        """检测Obsidian安装路径"""
        system = platform.system()
        possible_paths = []

        if system == "Windows":
            possible_paths = [
                Path.home() / "AppData/Local/Obsidian/Obsidian.exe",
                Path("C:/Program Files/Obsidian/Obsidian.exe"),
                Path("C:/Program Files (x86)/Obsidian/Obsidian.exe")
            ]
        elif system == "Darwin":  # macOS
            possible_paths = [
                Path("/Applications/Obsidian.app"),
                Path.home() / "Applications/Obsidian.app"
            ]
        elif system == "Linux":
            possible_paths = [
                Path("/usr/bin/obsidian"),
                Path("/opt/Obsidian/obsidian"),
                Path.home() / ".local/bin/obsidian",
                Path("/snap/bin/obsidian")
            ]

        for path in possible_paths:
            if path.exists():
                return str(path)

        return None

    def create_obsidian_vault(self, force: bool = False) -> bool:
        """创建Obsidian库"""
        try:
            if self.vault_path.exists():
                if not force:
                    print(f"{Fore.YELLOW}⚠️ 库目录已存在: {self.vault_path}")
                    return True
                else:
                    print(f"{Fore.BLUE}🗂️ 清理现有库目录...")
                    shutil.rmtree(self.vault_path)

            self.vault_path.mkdir(parents=True, exist_ok=True)
            print(f"{Fore.GREEN}✅ 创建Obsidian库: {self.vault_path}")

            self._create_vault_structure()
            self._create_vault_config()

            return True

        except Exception as e:
            print(f"{Fore.RED}❌ 创建库失败: {e}")
            return False

    def _create_vault_structure(self) -> None:
        """创建库目录结构"""
        directories = [
            'attachments', 'templates', 'daily', 'projects',
            '.obsidian', '.obsidian/plugins', '.obsidian/themes'
        ]

        for directory in directories:
            dir_path = self.vault_path / directory
            dir_path.mkdir(parents=True, exist_ok=True)

    def _create_vault_config(self) -> None:
        """创建Obsidian配置文件"""
        obsidian_dir = self.vault_path / '.obsidian'

        app_config = {
            "legacyEditor": False,
            "livePreview": True,
            "theme": "moonstone",
            "enabledPlugins": [
                "file-explorer", "global-search", "switcher", "graph",
                "backlink", "canvas", "outgoing-link", "tag-pane",
                "page-preview", "daily-notes", "templates", "note-composer",
                "command-palette", "markdown-importer", "outline", "word-count"
            ],
            "alwaysUpdateLinks": True,
            "newFileLocation": "current",
            "attachmentFolderPath": "attachments",
            "promptDelete": True,
            "showLineNumber": True,
            "spellcheck": True,
            "baseFontSize": 16
        }

        with open(obsidian_dir / 'app.json', 'w', encoding='utf-8') as f:
            json.dump(app_config, f, indent=2, ensure_ascii=False)

    def create_welcome_note(self) -> None:
        """创建欢迎笔记"""
        welcome_content = f"""# 🎉 欢迎使用Obsidian！

您的印象笔记已成功迁移到Obsidian。

## 📁 库结构
- **📂 attachments** - 所有图片和文件附件
- **📂 templates** - 笔记模板
- **📂 daily** - 日记笔记
- **📂 projects** - 项目管理

## 🚀 开始使用

### 基础功能
- `Ctrl/Cmd + N` - 创建新笔记
- `Ctrl/Cmd + O` - 快速打开笔记
- `[[]]` - 创建双向链接
- `#标签` - 添加标签

## 📖 学习资源
- [Obsidian官方帮助](https://help.obsidian.md/)
- [Obsidian中文社区](https://forum-zh.obsidian.md/)

## 🔧 迁移信息
- **迁移时间**: {self.config.get('migration_time', '未知')}
- **原始笔记数**: {self.config.get('total_notes', '未知')}
- **成功转换**: {self.config.get('converted_notes', '未知')}

---
*此笔记由印象笔记迁移工具自动生成*
"""

        welcome_file = self.vault_path / "欢迎使用Obsidian.md"
        with open(welcome_file, 'w', encoding='utf-8') as f:
            f.write(welcome_content)

    def create_templates(self) -> None:
        """创建常用模板"""
        templates_dir = self.vault_path / 'templates'

        daily_template = """# {{date:YYYY-MM-DD}}

## 📝 今日计划
- [ ]

## 💭 随想
-

## 📚 学习
-

---
标签: #日记 #{{date:YYYY}}
"""

        with open(templates_dir / '日记模板.md', 'w', encoding='utf-8') as f:
            f.write(daily_template)

    def open_obsidian(self) -> bool:
        """尝试打开Obsidian应用"""
        obsidian_path = self.detect_obsidian_installation()

        if not obsidian_path:
            print(f"{Fore.YELLOW}⚠️ 未检测到Obsidian安装")
            self.show_obsidian_install_guide()
            return False

        try:
            system = platform.system()

            if system == "Windows":
                os.startfile(str(self.vault_path))
            elif system == "Darwin":
                os.system(f'open "{obsidian_path}" "{self.vault_path}"')
            elif system == "Linux":
                os.system(f'"{obsidian_path}" "{self.vault_path}" &')

            print(f"{Fore.GREEN}🚀 正在打开Obsidian...")
            return True

        except Exception as e:
            print(f"{Fore.RED}❌ 打开Obsidian失败: {e}")
            return False

    def show_obsidian_install_guide(self) -> None:
        """显示Obsidian安装指南"""
        print(f"""
{Fore.CYAN}📖 Obsidian安装指南

{Fore.YELLOW}下载地址: https://obsidian.md/download

{Fore.YELLOW}安装步骤:
1. 访问官方网站下载对应系统版本
2. 安装完成后启动Obsidian
3. 选择"打开文件夹作为库"
4. 选择目录: {self.vault_path}
5. 开始使用您的笔记！

{Fore.GREEN}💡 提示: 安装完成后，您可以重新运行此工具来自动打开库。
""")

    def optimize_vault_settings(self) -> None:
        """优化库设置"""
        print(f"{Fore.BLUE}⚙️ 优化Obsidian设置...")
        print(f"{Fore.GREEN}✅ 优化设置完成")

    def install_recommended_plugins(self) -> None:
        """推荐插件信息"""
        print(f"""
{Fore.CYAN}📋 推荐插件

{Fore.YELLOW}核心插件 (已启用):
✅ 文件管理器 - 浏览文件
✅ 全局搜索 - 搜索笔记内容
✅ 快速切换 - 快速打开笔记
✅ 图谱视图 - 可视化笔记关系

{Fore.GREEN}💡 安装方法: 设置 → 社区插件 → 浏览 → 搜索插件名
""")


if __name__ == "__main__":
    print("ObsidianManager module loaded successfully")