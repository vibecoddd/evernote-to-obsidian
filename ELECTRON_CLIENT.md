# Electron 桌面客户端

桌面客户端使用 Electron 主进程承载 React/Vite renderer，并将迁移 API 作为 Python Flask sidecar 运行。它替代了旧的 PyWebView 客户端，桌面用户不需要 PyWebView；`web_app.py`、`templates/`、`static/` 和迁移源代码仍是 Web 模式与 sidecar 共用的运行时资源。

## 重要：Node.js 运行时前提

必须先安装并使用 **Node.js >=22.12.0**（`package.json` 也声明了此下限）。npm 的 engine 警告不足以阻止不受支持的 Node 版本继续安装或构建，因此不能把警告当作兼容性检查。发布打包必须使用 Node 22.12+；请用 `node --version` 确认运行时版本。在干净 checkout 中运行 `npm install`、`npm run build` 或启动 Electron 前都必须满足这一前提。

## 本地开发

从仓库根目录安装 Node 依赖和 Python 依赖：

```bash
cd /path/to/evernote-to-obsidian
npm install
python3 -m pip install -r requirements.txt
```

从干净 checkout 启动桌面客户端时，先构建 renderer 和 Electron 主进程，再从同一仓库根目录启动 Electron：

```bash
npm run build:renderer && npm run build:electron
npx electron .
```

`package.json` 的 Electron 入口是构建产物 `dist-electron/main.js`；主进程会加载构建产物 `dist/renderer/index.html`。因此 `npm run dev:renderer` 只启动 Vite renderer 开发服务器，不能单独用于启动此桌面客户端；Electron 尚未实现加载 Vite URL 的 HMR 工作流。

开发模式下 Electron 会使用 `PYTHON` 环境变量指定的 Python；未设置时使用 `python3`，并从启动 Electron 的仓库根目录运行 `backend_app.py`。请不要在其他目录执行 `npx electron .`，否则 sidecar 找不到该入口及其 Web 运行时资源。构建和打包还需要 PyInstaller：

```bash
python3 -m pip install -r requirements-desktop-build.txt
npm run build
```

`requirements-desktop-build.txt` 始终包含正常运行所需的 `requirements.txt`，再额外安装 PyInstaller。

## 启动与退出行为

每次桌面启动时，Electron 会在 `127.0.0.1` 请求一个由操作系统分配的动态端口，再以该端口启动 Python sidecar。sidecar 只绑定 loopback，不接受局域网连接。主进程轮询 `http://127.0.0.1:<port>/api/healthz`；开发模式默认最多等待 15 秒，打包应用为 PyInstaller sidecar 冷启动最多等待 60 秒。健康检查成功后才显示窗口，超时会停止 sidecar 并报告健康检查地址和最后一次错误；如果 sidecar 在健康检查前退出，错误会优先报告退出码或信号。

窗口加载本地的 React/Vite renderer，而 renderer 通过受限的 preload IPC 获取 sidecar URL、选择文件或目录、以及打开导出路径。应用只允许一个窗口实例：再次启动会聚焦已有窗口；迁移进行中关闭窗口会先请求确认。退出时 Electron 终止 Python sidecar，等待最多 5 秒，然后在必要时强制结束进程。

## 生成安装包

安装依赖后，在相应平台运行：

```bash
# macOS：生成 .dmg
npm run package:mac

# Windows：生成 NSIS 安装程序
npm run package:win
```

也可使用 `npm run package:current` 为当前平台构建。命令先执行 TypeScript 检查、前端测试和 renderer/Electron 编译，再用 PyInstaller 构建 Python sidecar，最后通过 electron-builder 输出到 `release/`。构建中间文件位于 `dist-electron/`、`dist/renderer/` 和 `dist/backend/`；不要把 `release/` 配置为应用输入。

请在目标操作系统上构建相应安装包。Windows 构建脚本会调用 `npm.cmd`，并为打包后的 Python sidecar 使用 `evernote-backend.exe`；不要手动用 POSIX 路径拼接或运行该可执行文件。通过 Electron 的文件选择器得到的 Windows 路径会原样传给 sidecar，因而应保留反斜杠、驱动器号和 Unicode 路径，避免手动转换为 macOS/Linux 格式。

## 资源与启动故障诊断

如果应用打开后无法显示界面或 sidecar 无法就绪，先查看从安装包启动时的日志/终端输出中的 health URL 和最后错误。常见原因包括：

- `dist/renderer/index.html` 未被打入应用：重新运行 `npm run build`，并确认 electron-builder 包含 `dist/renderer/**/*`。
- `backend/evernote-backend`（Windows 为 `backend/evernote-backend.exe`）缺失：重新安装 `requirements-desktop-build.txt` 后重新执行打包命令，并确认 `dist/backend` 被作为 `extraResources` 打包。
- sidecar 在开发模式 15 秒或打包应用 60 秒内未通过 `/api/healthz`：检查安全软件、防火墙和 Python sidecar 启动输出；动态 loopback 端口无需预先释放或固定为 5000。
- 构建时缺少 `templates/`、`static/` 或 `src/`：重新运行 Python sidecar 构建，确认 PyInstaller spec 收集这些运行时资源。

## macOS Gatekeeper、签名与公证

未签名或未公证的内部 `.dmg` 可能被 macOS 标记为“无法验证开发者”。确认来源后，可在“系统设置 → 隐私与安全性”选择“仍要打开”，或在 Finder 中按住 Control 点击应用并选择“打开”。

正式分发前，在发布环境配置 Apple Developer ID Application 证书以签名 `.app`，使用 `codesign --verify --deep --strict --verbose=2` 验证签名，然后将 `.dmg` 或 `.app` 提交到 Apple notarization 服务并使用 `stapler` 附加票据。签名身份、Apple ID/App Store Connect 凭据及公证过程属于发布者环境，本仓库不会保存这些机密。
