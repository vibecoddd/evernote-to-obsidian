#!/usr/bin/env python3
"""
Web界面启动脚本
"""

import sys
import argparse
from web_app import WebMigrator

def main():
    parser = argparse.ArgumentParser(description='启动印象笔记迁移工具Web界面')
    parser.add_argument('--host', default='127.0.0.1', help='监听地址 (默认: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5000, help='监听端口 (默认: 5000)')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--public', action='store_true', help='允许外部访问 (设置host为0.0.0.0)')

    args = parser.parse_args()

    if args.public:
        args.host = '0.0.0.0'
        print("⚠️  警告: 启用外部访问模式，请确保网络安全!")

    print(f"""
🌐 印象笔记到Obsidian迁移工具 - Web界面
{'='*50}
📡 监听地址: {args.host}
🔌 监听端口: {args.port}
🌍 访问地址: http://{'localhost' if args.host == '127.0.0.1' else args.host}:{args.port}
🔧 调试模式: {'开启' if args.debug else '关闭'}
{'='*50}
""")

    try:
        web_migrator = WebMigrator()
        web_migrator.run(host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        print("\n👋 用户停止服务")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()