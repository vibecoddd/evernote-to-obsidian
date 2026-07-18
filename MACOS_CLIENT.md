# macOS 客户端

macOS 客户端复用现有 Flask 迁移界面，但以独立 `.app` 窗口运行。用户双击应用后，不需要手动启动 Python、Flask 或浏览器；应用会在本机 `127.0.0.1` 的动态端口启动迁移服务，并在窗口中打开界面。

## 使用已构建的应用

构建产物位于：

```text
dist/印象笔记迁移工具.app
```

首次打开时，如果 macOS 提示应用来自未验证的开发者，请在“系统设置 → 隐私与安全性”中允许打开。正式对外分发前，应使用 Apple Developer 证书签名并完成 notarization；本项目的构建脚本不包含发布者证书。

应用只在本机 loopback 地址上提供临时 Web 服务，不接受局域网访问。迁移时，账号认证和笔记数据仍由现有本地迁移逻辑处理。

## 在 macOS 上构建

构建必须在 macOS 上进行，并使用与目标机器一致的架构构建（Apple Silicon 使用 arm64，Intel Mac 使用 x86_64）：

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-macos-build.txt
.venv/bin/python scripts/build_macos_app.py
open "dist/印象笔记迁移工具.app"
```

构建脚本会：

- 检查当前系统是否为 macOS；
- 使用当前虚拟环境中的 PyInstaller；
- 收集 `templates/`、`static/`、`src/` 和 Python 运行时；
- 生成 `dist/印象笔记迁移工具.app`。

`build/` 和 `dist/` 已被 Git 忽略，不会进入提交。若要发布 Intel 与 Apple Silicon 两种版本，需要分别在对应架构的 macOS 环境构建，或在发布流程中使用经过验证的 universal2 构建环境。

## 本地开发运行

安装桌面依赖后，可以直接运行桌面入口：

```bash
.venv/bin/python macos_app.py
```

这需要有 macOS 图形会话。没有图形会话时，请使用现有 Web 模式进行功能调试：

```bash
.venv/bin/python web_app.py
```

## 验证与故障排除

运行客户端入口和打包相关检查：

```bash
.venv/bin/python -m py_compile macos_app.py
.venv/bin/pytest -q test_macos_app.py test_macos_packaging.py
test -d "dist/印象笔记迁移工具.app"
```

常见问题：

- `PyWebView is not installed`：执行 `.venv/bin/pip install -r requirements-macos-build.txt`。
- `The macOS desktop client must be run on macOS`：桌面入口和 `.app` 构建不能在 Linux/Windows 上执行。
- `Embedded Web service did not become ready`：查看终端输出，确认本机没有安全软件阻止应用启动；应用使用动态端口，不需要释放或手动占用 5000 端口。
- 窗口内样式或图标不完整：确认构建没有跳过 `templates/`、`static/`，并重新执行构建命令。

