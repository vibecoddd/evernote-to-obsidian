#!/usr/bin/env python3
"""
测试印象笔记导出功能
"""

import sys
import tempfile
from pathlib import Path

# 添加src目录到Python路径
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

from evernote_exporter import EvernoteExporter
import colorama

def test_export():
    """测试导出功能"""
    colorama.init(autoreset=True)

    print("🧪 测试印象笔记导出功能")
    print("=" * 50)

    # 创建测试配置
    config = {
        'evernote_backend': 'china',  # 默认中国版，可以改为'international'
        'temp_directory': str(Path(tempfile.gettempdir()) / 'evernote_test'),
        'remember_credentials': False
    }

    try:
        # 初始化导出器
        exporter = EvernoteExporter(config)

        print(f"📁 临时目录: {config['temp_directory']}")
        print(f"🌏 后端设置: {config['evernote_backend']}")

        # 检查依赖
        if not exporter.check_dependencies():
            print("❌ 依赖检查失败")
            return False

        print("\n⚠️ 注意: 以下步骤需要您的印象笔记账号密码")
        print("如果您不想继续，请按 Ctrl+C 退出")
        input("\n按回车键继续...")

        # 尝试导出
        enex_files = exporter.export_notes()

        if enex_files:
            print(f"\n🎉 导出成功！")
            print(f"📄 导出文件数: {len(enex_files)}")
            for file in enex_files:
                print(f"   - {file}")
        else:
            print("\n⚠️ 没有导出任何文件")

        return True

    except KeyboardInterrupt:
        print("\n👋 用户取消测试")
        return False

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        print("\n💡 常见解决方案:")
        print("1. 检查网络连接")
        print("2. 验证账号密码是否正确")
        print("3. 确认选择了正确的印象笔记版本（中国版/国际版）")
        print("4. 如果启用了两步验证，尝试使用应用密码")
        return False

if __name__ == "__main__":
    test_export()