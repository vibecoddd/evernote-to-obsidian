# macOS Electron 客户端

macOS 桌面客户端由 Electron 承载 React/Vite 界面，并启动本地 Python Flask sidecar；不再使用 PyWebView。构建必须在 macOS 上进行：

```bash
npm install
python3 -m pip install -r requirements-desktop-build.txt
npm run package:mac
```

生成的 `.dmg` 位于 `release/`。请在 Apple Silicon 和 Intel macOS 上分别构建对应架构的发布物，或使用已验证的 universal 构建流程。

首次运行未签名的内部构建时，Gatekeeper 可能显示“无法验证开发者”。在确认来源后，前往“系统设置 → 隐私与安全性”选择“仍要打开”（或在 Finder 中按住 Control 点击应用后选择“打开”）。正式公开分发前必须使用 Apple Developer ID Application 证书签名，并提交 Apple notarization；详细流程、故障诊断和开发命令见 [ELECTRON_CLIENT.md](ELECTRON_CLIENT.md)。
