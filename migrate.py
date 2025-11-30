#!/usr/bin/env python3
"""
印象笔记到Obsidian一键迁移工具 - 主入口文件
"""

import os
import sys
from pathlib import Path

# 添加src目录到Python路径
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

try:
    from unified_migrator import main
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保已安装所有依赖:")
    print("pip install -r requirements.txt")
    sys.exit(1)

if __name__ == "__main__":
    main()