# macOS 客户端设计

## 背景

项目当前提供 Python CLI 和 Flask Web 界面。macOS 用户需要安装 Python、安装依赖、启动本地服务并手动打开浏览器，使用门槛较高。本次增加一个可双击启动的 macOS 桌面客户端，复用现有迁移能力和页面，避免维护第二套迁移业务逻辑。

## 目标与非目标

### 目标

- 在 macOS 上双击 `.app` 后直接显示迁移界面。
- 客户端自动启动本地 Flask 服务，绑定到 `127.0.0.1` 的动态空闲端口。
- 复用现有账号导出、ENEX 上传、Markdown 转换、Obsidian 库配置、进度和结果页面。
- 客户端退出时不留下后台 Web 服务进程。
- 使用 PyInstaller 打包 Python 运行时、项目代码、模板、静态资源和现有依赖，用户无需预装 Python。
- 提供可重复执行的 macOS 构建入口和使用文档。

### 非目标

- 不重写为 SwiftUI 原生界面。
- 不引入 Tauri 或 Electron。
- 不在本次工作中实现 Apple Developer 签名或 notarization；签名需要发布者自己的证书和账号。
- 不改变已有迁移算法和 Web API 的业务语义。

## 方案选择

### 方案 A：SwiftUI 原生客户端

优点是 macOS 原生体验最好；缺点是需要重新实现已有表单、上传、Socket.IO 进度和结果页面，并增加 Swift/Python 跨进程接口，工作量和维护成本最高。

### 方案 B：Tauri/Electron 桌面壳

优点是桌面窗口和分发能力成熟；缺点是要增加 Rust 或 Node 构建链，并额外处理 Python 后端启动、资源路径和子进程生命周期。

### 方案 C：PyWebView + PyInstaller

优点是最大化复用现有 Flask 页面和 Python 逻辑，客户端入口可以保持很小；缺点是 WebView 行为仍由 macOS WebKit 决定，且构建必须在目标 macOS 架构上执行。由于当前项目已经是 Python + Flask，本项目采用方案 C。

## 架构

新增桌面入口模块负责四件事：计算打包前后都有效的资源根目录、获取动态本地端口、在守护线程中启动 `WebMigrator`、等待首页可访问后创建 PyWebView 窗口。窗口关闭后主线程结束，守护线程随进程退出，不保留独立服务进程。

服务仍通过现有 `WebMigrator` 提供页面和 API。桌面入口不直接调用迁移器，因此 Web 模式和 macOS 模式共享同一条业务链路。PyInstaller spec 显式收集 `templates/`、`static/` 和 `src/`，并声明 Flask-SocketIO、eventlet、PyWebView 等运行时依赖。

资源路径使用统一 helper：开发环境指向仓库根目录，PyInstaller 环境指向 `sys._MEIPASS` 或可执行文件旁的资源目录。服务启动只监听 loopback，不接受局域网访问。

## 启动与退出流程

1. `macos_app.py` 调用 `freeze_support()`，确定资源根目录。
2. 通过临时 TCP socket 获取 `127.0.0.1` 动态端口。
3. 创建 `WebMigrator`，在 daemon 线程调用 `run(host="127.0.0.1", port=<动态端口>)`。
4. 轮询首页直到返回 HTTP 200；超时则关闭客户端并显示可诊断错误。
5. 创建固定标题、最小尺寸和可调整大小的 PyWebView 窗口，加载本地 URL。
6. WebView 返回后主进程退出，后台 daemon 服务线程随进程结束。

## 错误处理

- PyWebView 未安装或当前平台不是 macOS 时，入口输出明确的安装/构建提示并以非零状态退出。
- 本地服务在启动超时、端口失效或返回非 200 时，入口输出错误原因和日志位置。
- 应用不向外网暴露 Flask 服务；迁移所需的 Evernote 网络连接仍由现有导出器按用户操作发起。
- 业务错误继续由现有页面显示，不在桌面层重复实现。

## 打包与交付

- `requirements.txt` 增加桌面运行依赖；构建工具单独放入开发/构建说明，避免普通 Web 用户必须安装打包器。
- 新增 PyInstaller spec 和 macOS 构建脚本，输出 `dist/印象笔记迁移工具.app`。
- 构建脚本在非 macOS 环境明确拒绝执行，并允许通过环境变量覆盖 Python、应用名称和输出目录。
- 文档补充开发运行、构建、产物位置、最低 macOS 版本假设和签名说明。

## 测试与验收

桌面入口使用可注入的端口选择、服务启动和健康检查函数，以便不创建真实 GUI 也能测试：

- 动态端口选择只绑定 loopback，并返回可连接端口。
- 健康检查会重试，成功响应 200 后返回；超过截止时间返回明确异常。
- 开发资源根目录和 PyInstaller 资源根目录解析正确。
- 入口将 WebMigrator 绑定到动态端口，而不是固定的 5000。
- 现有非网络单元测试继续运行；真实账号/网络测试按仓库现状单独执行。
- 在 macOS ARM64 当前环境执行 PyInstaller 构建，验证 `.app` 存在、Info.plist 可读取、资源已收集，并启动应用做首页 HTTP 冒烟检查；没有 GUI 会话时记录该项为环境限制。

