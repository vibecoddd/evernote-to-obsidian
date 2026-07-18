# macOS 客户端设计（历史背景）

> **状态：已由 Electron 设计取代。** 本文是 2026-07-18 早期 macOS-only 方案的背景记录，不是可执行设计或维护指南。

早期设计的目标是将 Flask 界面嵌入 macOS 本地窗口。该方案的 PyWebView 运行时和 macOS 专用打包链已经退役；当前桌面客户端采用 Electron + React renderer 与 Python sidecar，支持 macOS 和 Windows，且桌面用户不需要 PyWebView。

## 当前设计与命令

- 当前设计：[Electron 跨平台客户端设计](2026-07-18-electron-desktop-client-design.md)
- 当前计划：[Electron 跨平台客户端计划](../plans/2026-07-18-electron-desktop-client.md)
- 当前操作指南：[Electron 客户端指南](../../../ELECTRON_CLIENT.md)

```bash
npm install
npm run package:mac  # macOS .dmg
npm run package:win  # Windows NSIS 安装程序
```

当前架构由 Electron 在 `127.0.0.1` 动态端口启动 Python sidecar，使用 `/api/healthz` 健康检查，并在应用退出时关闭 sidecar。资源诊断、Windows 路径处理和 macOS 签名/公证要求以 `ELECTRON_CLIENT.md` 为准。

## 历史范围

这个设计说明只保留了早期技术决策的背景。它不定义现有客户端的源文件、测试、构建配置或发布步骤；所有此类工作应遵循 Electron 文档。
