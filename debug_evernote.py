#!/usr/bin/env python3
"""
印象笔记导出调试工具
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

def test_evernote_backup():
    """测试evernote-backup功能"""
    print("🔍 测试evernote-backup功能...")

    # 1. 检查版本
    try:
        result = subprocess.run(['evernote-backup', '--version'],
                              capture_output=True, text=True, timeout=10)
        print(f"✅ evernote-backup版本: {result.stdout.strip()}")
    except Exception as e:
        print(f"❌ 版本检查失败: {e}")
        return False

    # 2. 检查帮助命令
    try:
        result = subprocess.run(['evernote-backup', '--help'],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ 帮助命令正常")
        else:
            print("⚠️ 帮助命令异常")
    except Exception as e:
        print(f"❌ 帮助命令失败: {e}")

    return True

def test_init_db_simulation():
    """测试数据库初始化（模拟）"""
    print("\n🔍 测试数据库初始化...")

    # 创建临时目录
    temp_dir = Path(tempfile.mkdtemp(prefix='evernote_test_'))
    print(f"📁 测试目录: {temp_dir}")

    try:
        # 切换到临时目录
        os.chdir(temp_dir)

        # 测试init-db命令的基本语法
        result = subprocess.run(['evernote-backup', 'init-db', '--help'],
                              capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            print("✅ init-db命令语法正常")
            print("📝 可用选项:")
            for line in result.stdout.split('\n'):
                if '--backend' in line or '--force' in line:
                    print(f"   {line.strip()}")
        else:
            print("❌ init-db命令语法异常")
            print(f"错误: {result.stderr}")

    except Exception as e:
        print(f"❌ 初始化测试失败: {e}")
    finally:
        # 清理临时目录
        os.chdir('/root/vibecoding/evernote-to-obsidian')
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

def analyze_common_issues():
    """分析常见问题"""
    print("\n🔍 分析常见初始化失败原因...")

    issues = [
        "1. 网络连接问题 - 无法连接到印象笔记服务器",
        "2. 账号密码错误 - 用户名或密码不正确",
        "3. 账号类型选择错误 - 中国版vs国际版混淆",
        "4. 两步验证 - 账号启用了两步验证但未正确处理",
        "5. API限制 - 印象笔记API调用限制",
        "6. 权限问题 - 临时目录写入权限",
        "7. 依赖版本冲突 - Python包版本不兼容"
    ]

    for issue in issues:
        print(f"   {issue}")

def provide_solutions():
    """提供解决方案"""
    print("\n💡 解决方案建议:")

    solutions = [
        "1. 检查网络: 确保能正常访问印象笔记网站",
        "2. 验证账号: 先在浏览器中登录确认账号密码正确",
        "3. 选择正确后端: 中国用户选择'china'，其他选择'international'",
        "4. 处理两步验证: 如启用了2FA，可能需要应用密码",
        "5. 重试机制: 网络不稳定时可以多次尝试",
        "6. 检查权限: 确保有临时目录的读写权限",
        "7. 更新依赖: 升级到最新版本的evernote-backup"
    ]

    for solution in solutions:
        print(f"   {solution}")

def main():
    """主函数"""
    print("🚀 印象笔记导出调试工具")
    print("=" * 50)

    # 测试基础功能
    if not test_evernote_backup():
        print("❌ 基础测试失败，请检查evernote-backup安装")
        return

    # 测试初始化
    test_init_db_simulation()

    # 分析问题
    analyze_common_issues()

    # 提供解决方案
    provide_solutions()

    print("\n" + "=" * 50)
    print("🔧 手动测试建议:")
    print("1. 运行: evernote-backup init-db --backend china")
    print("2. 输入您的印象笔记账号和密码")
    print("3. 查看具体的错误信息")
    print("4. 根据错误信息采用相应解决方案")

if __name__ == "__main__":
    main()