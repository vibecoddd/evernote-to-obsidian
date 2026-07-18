# macOS 客户端（历史实施计划）

> **状态：已由 Electron 跨平台客户端取代。** 本文保留为早期 macOS/PyWebView 方案的设计历史，不能作为当前实现、测试或打包指南。

早期计划曾描述一个仅 macOS 的 PyWebView + PyInstaller 客户端。该运行时及其专用入口、测试和构建配置均已退役；当前桌面客户端不需要 PyWebView。

## 当前实施入口

- 当前实施计划：[Electron 跨平台客户端计划](2026-07-18-electron-desktop-client.md)
- 当前设计：[Electron 跨平台客户端设计](../specs/2026-07-18-electron-desktop-client-design.md)
- 开发、打包和故障排除：[Electron 客户端指南](../../../ELECTRON_CLIENT.md)

以下命令仅为指向当前 Electron 工作流的快速参考；完整、规范的开发、打包和故障排除说明以 `ELECTRON_CLIENT.md` 为准。

> **前提：** 在运行下列 `npm install` 或 macOS 打包命令前，必须先安装并使用 **Node.js >=22.12.0**。npm 的 engine 警告不足以阻止不受支持的 Node 版本继续安装或构建，因此不能把警告当作兼容性检查；发布打包必须使用 Node 22.12+。

```bash
npm install
npm run package:mac  # 生成 macOS .dmg
npm run package:win  # 生成 Windows NSIS 安装程序
```

Electron 主进程在 `127.0.0.1` 的动态端口启动 Python sidecar，等待 `/api/healthz` 后显示窗口，并在退出时停止 sidecar。有关资源缺失、Windows 路径、签名和公证的说明，以 `ELECTRON_CLIENT.md` 为准。

## 保留原因

本文只记录当时的 macOS-only 方案为何曾选择嵌入式 WebView；它不反映当前支持的文件、命令或发布流程。需要实现或维护桌面客户端时，请使用上述 Electron 文档。
