#!/usr/bin/env python3
"""
模拟Web界面的完整迁移流程
"""

import os
import sys
from pathlib import Path
import tempfile
import json
import pytest

# 添加src目录到Python路径
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

def run_web_integration():
    """测试完整的Web迁移流程"""
    print("🌐 测试Web界面完整迁移流程")
    print("=" * 60)

    try:
        from evernote_exporter import EvernoteExporter
        from config import Config

        # 创建配置（与web界面相同）
        config_data = {
            'evernote_backend': 'china',
            'evernote_credentials': {
                'username': 'your_email@example.com',
                'password': 'your_password'
            },
            'output': {
                'obsidian_vault': '/tmp/test_vault_integration'
            },
            'temp_directory': '/tmp/web_evernote_test'
        }

        print(f"账号: {config_data['evernote_credentials']['username']}")
        print(f"后端: {config_data['evernote_backend']}")
        print(f"输出目录: {config_data['output']['obsidian_vault']}")

        # 创建配置对象
        config = Config()
        config.config_data = config_data

        print("\n1️⃣  测试依赖检查...")
        exporter = EvernoteExporter(config_data)

        if not exporter.check_dependencies():
            print("❌ 依赖检查失败")
            return False

        print("✅ 依赖检查通过")

        print("\n2️⃣  测试导出流程...")
        enex_files = exporter.export_notes()

        if not enex_files:
            print("❌ 导出失败")
            return False

        print(f"✅ 导出成功! 共 {len(enex_files)} 个ENEX文件:")
        for i, file_path in enumerate(enex_files, 1):
            file_size = Path(file_path).stat().st_size / (1024 * 1024)  # MB
            print(f"   {i}. {Path(file_path).name} ({file_size:.1f} MB)")

        print("\n3️⃣  测试文件完整性...")
        total_size = 0
        for file_path in enex_files:
            if not Path(file_path).exists():
                print(f"❌ 文件不存在: {file_path}")
                return False

            size = Path(file_path).stat().st_size
            total_size += size

            if size < 100:  # 文件太小可能有问题
                print(f"⚠️  文件可能有问题: {file_path} ({size} bytes)")

        print(f"✅ 文件完整性检查通过，总大小: {total_size / (1024 * 1024):.1f} MB")

        print("\n4️⃣  验证ENEX文件内容...")
        sample_file = enex_files[0]
        try:
            with open(sample_file, 'r', encoding='utf-8') as f:
                content = f.read(1000)  # 读取前1000字符
                if '<?xml' in content and 'en-export' in content:
                    print("✅ ENEX文件格式正确")
                else:
                    print("⚠️  ENEX文件格式可能有问题")
        except Exception as e:
            print(f"⚠️  读取ENEX文件时出错: {e}")

        return True

    except Exception as e:
        print(f"❌ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_web_integration():
    pytest.skip("requires a real Evernote account and network access; run this module directly")

def main():
    """主函数"""
    print("🧪 Web集成测试")

    success = run_web_integration()

    if success:
        print("\n🎉 Web集成测试成功!")
        print("\n✅ 确认事项:")
        print("   • evernote-backup 正常工作")
        print("   • 真实账号认证成功")
        print("   • 能够导出ENEX文件")
        print("   • Web界面应该完全可用")
        print("\n💡 现在您可以通过Web界面 http://0.0.0.0:5000 进行完整迁移")
    else:
        print("\n❌ Web集成测试失败")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
