# Electron 跨平台客户端 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有 PyWebView/macOS 桌面入口改造为支持 macOS 和 Windows 的 Electron + React 单窗口客户端，同时复用 Flask/Python 迁移后端。

**Architecture:** Electron 主进程以 `127.0.0.1` 动态端口启动打包后的 Python 子进程，等待 `/api/healthz` 就绪后加载本地 React renderer。React 通过受限 preload API 获取后端地址、选择路径、打开 Vault 和处理关闭确认，通过 HTTP + Socket.IO 调用 Flask API；Python 保留 Evernote 导出、ENEX 处理、Markdown 转换和 Obsidian 写入职责。

**Tech Stack:** Electron, React, Vite, TypeScript, electron-builder, Flask/Flask-SocketIO, PyInstaller, pytest, Vitest, React Testing Library, Node.js/npm.

## Global Constraints

- 在运行本计划中的任何 `npm` 安装、测试、构建或打包命令前，开发/发布环境必须使用 **Node.js >=22.12.0**。npm 的 engine 警告不足以阻止不受支持的 Node 版本继续安装或构建，因此不能把警告当作兼容性检查；发布打包必须使用 Node 22.12+。安装后的桌面应用不要求用户预装 Node.js。以 [ELECTRON_CLIENT.md](../../../ELECTRON_CLIENT.md) 为当前开发、构建、打包和故障排除的规范操作指南。
- 客户端只监听 `127.0.0.1`，不得使用 `0.0.0.0` 或允许局域网访问。
- 客户端必须选择动态空闲端口，不得依赖固定的 5000 端口。
- 用户运行安装包时不需要预装 Python 或手动启动 Flask 服务。
- Electron 开启 context isolation，关闭 Node.js 直通页面；系统能力只能经 preload 白名单 API 暴露。
- 迁移算法继续由 Python 实现，不在 React 或 Electron 中复制。
- 单窗口向导包含“选择数据源 → 配置目标 → 迁移预检 → 执行迁移 → 迁移结果”五个阶段。
- macOS 和 Windows 共用 React 交互；平台差异由 Electron、preload 和打包配置处理。
- 每个生产代码行为先写一个可观察失败的测试；配置、静态样式和打包脚本按配置例外处理。
- 迁移停止不回滚已写入文件；关闭确认必须明确这一点。
- 不修改用户已有的 `欢迎使用Obsidian.md` 工作区改动。
- 每个任务完成后运行焦点测试并创建独立提交。

## 文件结构与职责

- `package.json`、`package-lock.json`：Node 依赖、脚本和 Electron 入口。
- `vite.config.ts`、`tsconfig.json`、`tsconfig.electron.json`：renderer/主进程构建配置。
- `electron/main.ts`：单实例、Python 子进程、BrowserWindow、关闭和 IPC handlers。
- `electron/preload.ts`、`electron/types.ts`：隔离系统能力桥接和共享类型。
- `frontend/src/`：React 应用、向导状态、API 客户端、组件和样式。
- `backend_app.py`：只监听 loopback 的 PyInstaller 后端入口。
- `src/desktop_api.py`：预检和路径校验纯函数。
- `web_app.py`：健康检查、预检/停止接口、CORS 来源和任务事件。
- `packaging/backend/evernote_backend.spec`：Python sidecar 的 PyInstaller 规格。
- `packaging/electron-builder.yml`：安装包、`extraResources` 和平台目标。
- `scripts/build_backend.py`、`scripts/build_electron_app.py`：可重复构建入口。
- `ELECTRON_CLIENT.md`：开发、构建、运行时故障排除和平台说明。

旧的 PyWebView 文件在 Electron 产物通过 macOS 冒烟验证后移除；Jinja 路由继续作为 Web 兼容入口。

## Task 1: 建立 React/Electron 工程和测试基线

**Files:** Create `package.json`, `package-lock.json`, `vite.config.ts`, `tsconfig.json`, `tsconfig.electron.json`, `electron/types.ts`, `frontend/index.html`, `frontend/src/main.tsx`; modify `.gitignore`.

**Interfaces:** Provides `npm run dev:renderer`, `npm run typecheck`, `npm run test:frontend`, `npm run build:renderer`, and `npm run build:electron`; renderer output is `dist/renderer`, Electron output is `dist-electron`.

- [ ] **Step 1: Create the package manifest and install dependencies.**

Use React, React DOM, Socket.IO client, Electron, Vite, TypeScript, `@vitejs/plugin-react`, Vitest, JSDOM, React Testing Library, user-event, Jest DOM, and Node/React type packages. Define these scripts:

```json
"dev:renderer": "vite --config vite.config.ts",
"typecheck": "tsc -p tsconfig.json --noEmit && tsc -p tsconfig.electron.json --noEmit",
"test:frontend": "vitest run",
"build:renderer": "vite build --config vite.config.ts",
"build:electron": "tsc -p tsconfig.electron.json",
"build": "npm run typecheck && npm run test:frontend && npm run build:renderer && npm run build:electron"
```

Run `npm install`; expected result is a committed `package-lock.json` and exit code 0.

- [ ] **Step 2: Add a valid renderer entry and Vite/TypeScript configuration.**

Create `frontend/index.html` with `<div id="root"></div>` and `frontend/src/main.tsx` with a strict React root:

```tsx
createRoot(document.getElementById("root")!).render(
  <StrictMode><main aria-live="polite">印象笔记迁移工具正在启动…</main></StrictMode>,
);
```

Configure Vite with `root: "frontend"`, the React plugin, and `build.outDir: "../dist/renderer"`. Configure the renderer for strict DOM/JSX types and Electron for strict CommonJS output in `dist-electron`. Add `electron/types.ts` containing only `export {};` so the initial Electron typecheck has a valid input before the main process is added.

- [ ] **Step 3: Ignore generated artifacts and verify the baseline.**

Append `node_modules/`, `dist-electron/`, `.vite/`, and `coverage/` to `.gitignore`. Run `npm run typecheck && npm run test:frontend && npm run build:renderer`; expected: all commands pass and `dist/renderer/index.html` exists.

- [ ] **Step 4: Commit the workspace baseline.**

```bash
git add package.json package-lock.json vite.config.ts tsconfig.json tsconfig.electron.json frontend/index.html frontend/src/main.tsx .gitignore
git commit -m "build: scaffold Electron React workspace"
```

## Task 2: Add the Python desktop backend contract

**Files:** Create `test_desktop_api.py`, `test_backend_app.py`, `src/desktop_api.py`, `backend_app.py`; modify `web_app.py`, `requirements.txt`.

**Interfaces:** Provides `preflight_config(config_data) -> dict`; provides `backend_app.run_backend(port, debug=False) -> None`; adds `GET /api/healthz`, `POST /api/preflight`, and `POST /api/cancel_migration/<task_id>`; preserves existing migration/export/upload/status routes and Socket.IO event names.

- [ ] **Step 1: Write failing preflight tests.**

Test an existing `.enex` plus writable Vault returns `ok: true`, and invalid suffix/missing Vault returns error codes `invalid_enex` and `vault_missing`.

Run `.venv/bin/pytest -q test_desktop_api.py`; expected: `ModuleNotFoundError` for `src.desktop_api`.

- [ ] **Step 2: Implement `preflight_config`.**

Expand user paths, validate ENEX suffix/existence, validate account credentials, validate Vault existence/create option/write access, and return exactly `{ok, errors, warnings, summary}` with JSON-compatible values. Re-run the focused tests; expected: pass.

- [ ] **Step 3: Write failing health and loopback-entry tests.**

```python
def test_healthz_returns_status():
    from web_app import WebMigrator
    response = WebMigrator().app.test_client().get("/api/healthz")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}

def test_backend_entry_uses_loopback(monkeypatch):
    import backend_app
    calls = []
    fake = type("M", (), {"run": lambda self, **kwargs: calls.append(kwargs)})()
    monkeypatch.setattr(backend_app, "WebMigrator", lambda: fake)
    backend_app.run_backend(43123)
    assert calls[0]["host"] == "127.0.0.1"
```

Run `.venv/bin/pytest -q test_backend_app.py test_desktop_api.py`; expected: fail because the route and entry do not exist.

- [ ] **Step 4: Implement sidecar entry, health, preflight, and restricted origins.**

`backend_app.py` accepts only `--port` and `--debug`, and calls `WebMigrator.run(host="127.0.0.1", port=port, debug=debug, allow_unsafe_werkzeug=True)`. Add `/api/healthz`, `/api/preflight` with 200/422 responses, and `flask-cors>=4.0.0`; allow `null` and Vite’s development origin for the desktop entry while preserving ordinary Web mode.

- [ ] **Step 5: Implement safe cancellation.**

Store a `threading.Event` per task. The cancel endpoint sets it and returns a machine-readable `cancelling` response; unknown tasks return 404. Check the event before major steps and inside the ENEX loop, update status to `cancelled`, emit `migration_cancelled`, and preserve written files. Add endpoint and event-check tests.

- [ ] **Step 6: Verify and commit the backend contract.**

Run `.venv/bin/pytest -q test_backend_app.py test_desktop_api.py test_web_integration.py`; expected: new tests pass and existing Web integration behavior remains unchanged. Commit:

```bash
git add backend_app.py src/desktop_api.py web_app.py requirements.txt test_backend_app.py test_desktop_api.py
git commit -m "feat: add desktop backend health and preflight APIs"
```

## Task 3: Implement Electron main lifecycle and preload bridge

**Files:** Create `electron/main.ts`, `electron/preload.ts`, `electron/main.test.ts`, `electron/preload.test.ts`, `frontend/src/types/desktop.d.ts`; modify `electron/types.ts`, `tsconfig.electron.json`.

**Interfaces:** Provides `startBackend(options): Promise<BackendHandle>`, `waitForBackend(url, options): Promise<void>`, and `window.desktop.getBackendUrl`, `selectDirectory`, `selectEnexFiles`, `openPath`, `setMigrationActive`, `onCloseRequested`, `confirmClose`.

- [ ] **Step 1: Write failing health polling tests.**

```ts
it("retries until health succeeds", async () => {
  const fetchImpl = vi.fn()
    .mockRejectedValueOnce(new Error("not ready"))
    .mockResolvedValueOnce(new Response('{"status":"ok"}', { status: 200 }));
  await waitForBackend("http://127.0.0.1:43123", { fetchImpl, timeoutMs: 100, intervalMs: 1 });
  expect(fetchImpl).toHaveBeenCalledTimes(2);
});
```

Run `npm run test:frontend -- electron/main.test.ts`; expected: fail because `waitForBackend` is missing.

- [ ] **Step 2: Implement dynamic port and health polling.**

Bind a Node `net.Server` to `127.0.0.1:0`, close it, and return the assigned port. Poll `/api/healthz` with an injected fetch, monotonic deadline, bounded interval, and final error containing URL and last failure.

- [ ] **Step 3: Write failing preload and single-instance tests.**

Mock Electron modules and assert the bridge exposes exactly the seven listed methods, a second instance focuses the existing window, the renderer loads `dist/renderer/index.html`, and backend stop runs before quit.

- [ ] **Step 4: Implement the isolated preload bridge.**

Use `contextBridge.exposeInMainWorld("desktop", api)`; each method invokes a named IPC channel. The close listener returns an unsubscribe function. Declare the matching `DesktopBridge` type in `frontend/src/types/desktop.d.ts`.

- [ ] **Step 5: Implement the main process.**

Acquire `app.requestSingleInstanceLock()` before creating a window. In development spawn `PYTHON`/`python3 backend_app.py --port <port>`; in production spawn `process.resourcesPath/backend/evernote-backend[.exe]`. Create the window only after health succeeds, with:

```ts
webPreferences: { preload, contextIsolation: true, nodeIntegration: false, sandbox: true },
minWidth: 960,
minHeight: 640,
show: false,
```

Add IPC handlers for path dialogs, `shell.openPath`, backend URL, active-task close guard, and confirmed close. Intercept unauthorized navigation. On `before-quit`, stop the backend and use a bounded fallback kill.

- [ ] **Step 6: Verify and commit.**

Run `npm run test:frontend -- electron && npm run typecheck`; expected: all Electron tests and TypeScript checks pass. Commit the main/preload files with `feat: add Electron backend lifecycle and preload bridge`.

## Task 4: Add typed renderer state and API client

**Files:** Create `frontend/src/domain/types.ts`, `wizardReducer.ts`, `wizardReducer.test.ts`, `frontend/src/api/client.ts`, `client.test.ts`; modify `frontend/src/main.tsx`.

**Interfaces:** `WizardState` holds step/source/target/preflight/migration/backend/error; `wizardReducer` never discards form data; `createApiClient(baseUrl)` provides health/preflight/start/status/cancel; `connectMigrationEvents` joins a task room and returns `disconnect()`.

- [ ] **Step 1: Write failing reducer tests.**

Test that source and target values survive `navigation/next`, that `navigation/back` preserves them, and that reset clears the password. Run the focused Vitest file; expected: missing reducer failure.

- [ ] **Step 2: Implement the model and reducer.**

Define source modes `account | enex`, credentials, current Python config keys, preflight issues, progress statistics, log entries, terminal results, and actions for navigation/form/preflight/migration/error/reset. Passwords remain in memory only.

- [ ] **Step 3: Write failing API tests and implement transport.**

Mock a 422 `/api/preflight` response and assert `{code, message}` survives. Implement `requestJson` converting non-2xx responses into `ApiError {status, code, message}` without logging bodies; implement start/status/cancel and Socket.IO event normalization.

- [ ] **Step 4: Connect bootstrap and verify.**

Await `window.desktop.getBackendUrl()`, build the client, and render a retryable startup error. Run `npm run test:frontend -- frontend/src/domain frontend/src/api && npm run typecheck`; expected: pass. Commit with `feat: add typed wizard state and backend client`.

## Task 5: Build the single-window setup wizard

**Files:** Create `frontend/src/App.tsx`, `AppShell.tsx`, `StepIndicator.tsx`, `ActionBar.tsx`, `FormField.tsx`, `ErrorPanel.tsx`, `SourceStep.tsx`, `TargetStep.tsx`, `PreflightStep.tsx`, their tests, `frontend/src/styles/tokens.css`, and `app.css`.

**Interfaces:** Shell has header/five-step indicator/scrollable main/fixed footer; setup steps receive state and dispatch; source maps to `source_mode`, `evernote_backend`, credentials, and `input.enex_files`; target preserves existing output/conversion/organization/migration keys.

- [ ] **Step 1: Write failing shell/source tests.**

Assert all five labels, `aria-current="step"`, ENEX selection through `window.desktop.selectEnexFiles`, and path preservation after back navigation. Run the two focused tests; expected: missing-component failure.

- [ ] **Step 2: Implement shell and design tokens.**

Use semantic header/main/footer, minimum 960×640 layout, scrollable content, fixed action bar, and variables for surface/text/accent/success/warning/danger/focus/spacing/radius.

- [ ] **Step 3: Implement source step.**

Account mode collects username/password and China/International backend. ENEX mode uses the native multi-file picker. Passwords are not persisted or logged. Disable next until the source is valid.

- [ ] **Step 4: Test and implement target/preflight.**

Test Vault selection, create/backup options, conversion toggles, organization mode, attachment folder, welcome note, templates, temp files, preflight success, warnings, and blocking errors. On preflight entry call `api.preflight(config)`; warnings permit confirmation and errors keep the user on the step.

- [ ] **Step 5: Verify and commit.**

Run `npm run test:frontend -- frontend/src/components && npm run typecheck`; expected: all setup tests pass. Commit with `feat: add single-window React wizard shell`.

## Task 6: Build progress, logs, results, and close handling

**Files:** Create `MigrationStep.tsx`, `ProgressSummary.tsx`, `LogPanel.tsx`, `ResultStep.tsx`, and focused tests; modify `App.tsx` and `wizardReducer.ts`.

**Interfaces:** `MigrationStep` starts a task and consumes Socket.IO events; `LogPanel` retains all logs and is collapsed by default; `ResultStep` handles success/partial/failed/cancelled and open/restart/log actions.

- [ ] **Step 1: Write failing progress/result tests.**

Test that a progress event renders `42%` and its message, and that a partial result lists failed paths. Run focused tests; expected: missing-component failure.

- [ ] **Step 2: Implement migration and event state.**

Start only after preflight, call `setMigrationActive(true)`, store task ID, join its room, update progress/statistics/logs, and transition on completed/error/cancelled. Disable setup controls during execution.

- [ ] **Step 3: Implement log panel and native close confirmation.**

Register `onCloseRequested`; during an active task show an in-window confirmation, call `api.cancelMigration`, explain that written files are not rolled back, then call `confirmClose`. Without an active task, confirm close immediately.

- [ ] **Step 4: Implement results and verify.**

Open Vault through `window.desktop.openPath`, reset without retaining the password, expand logs, and never silently retry. Run focused UI tests plus `npm run typecheck`; expected: pass. Commit with `feat: add migration progress and result workflow`.

## Task 7: Add Python sidecar and Electron packaging

**Files:** Create `packaging/backend/evernote_backend.spec`, `packaging/electron-builder.yml`, `scripts/build_backend.py`, `scripts/build_electron_app.py`, `test_electron_packaging.py`, `requirements-desktop-build.txt`; modify `package.json`, `.gitignore`.

**Interfaces:** Backend output is `dist/backend/evernote-backend[.exe]`; complete build runs renderer, Electron, backend, and electron-builder; builder packages `dist-electron`, `dist/renderer`, and backend as `extraResources`.

- [ ] **Step 1: Write failing packaging tests.**

Assert the backend spec contains `backend_app.py`, `templates`, `static`, `src`, and Socket.IO runtime imports; assert builder config contains `extraResources`, `to: backend`, `target: dmg`, and `target: nsis`. Run focused pytest; expected: missing-file failure.

- [ ] **Step 2: Implement the PyInstaller spec and script.**

Use `backend_app.py`, collect templates/static/src and `eventlet`, `engineio`, `socketio` submodules, name the binary `evernote-backend`, and do not create a PyWebView GUI bundle. Resolve PyInstaller from `PYINSTALLER` or current Python and pass `--distpath dist/backend --workpath build/backend`.

- [ ] **Step 3: Implement electron-builder and complete build scripts.**

Use `appId: com.evernote-to-obsidian.migrator`, `productName: 印象笔记迁移工具`, `extraResources: [{from: dist/backend, to: backend}]`, mac target `dmg`, and Windows target `nsis`. Add `package:mac`, `package:win`, and `package:current`; complete build order is `npm run build`, backend script, then `npm exec electron-builder -- --config packaging/electron-builder.yml`.

- [ ] **Step 4: Verify and commit packaging.**

Run `.venv/bin/pytest -q test_electron_packaging.py && npm run typecheck && npm run build:renderer && npm run build:electron`; expected: config checks pass and renderer/main outputs exist. Commit with `build: package Electron app with Python sidecar`.

## Task 8: Document Electron and retire PyWebView desktop files

**Files:** Create `ELECTRON_CLIENT.md`; modify `README.md`, `MACOS_CLIENT.md`, `requirements.txt`, `requirements-desktop-build.txt`, `test_electron_packaging.py`; the retired PyWebView entry point, tests, build script, PyInstaller spec, and macOS-only build requirements were deleted after packaging validation.

**Interfaces:** Documentation uses Electron commands for macOS/Windows; normal Web users no longer install PyWebView; old PyWebView is no longer a supported desktop runtime.

- [ ] **Step 1: Add failing documentation assertions.**

Assert README contains `npm install`, `npm run package:mac`, and `npm run package:win`; assert `ELECTRON_CLIENT.md` documents loopback, Python sidecar, macOS, and Windows. Run focused pytest; expected: failure because docs are absent.

- [ ] **Step 2: Write and link the new documentation.**

Document development, `.dmg` and NSIS builds, dynamic loopback startup, sidecar shutdown, health timeout, missing resources, Windows paths, macOS unverified-app behavior, signing, and notarization.

- [ ] **Step 3: Remove obsolete dependency and files.**

Remove `pywebview>=5.4.0` from `requirements.txt`; keep desktop build requirements as `-r requirements.txt` plus PyInstaller; remove only the listed PyWebView files. Do not delete templates, static assets, `web_app.py`, or migration source.

- [ ] **Step 4: Verify Web regression and commit docs.**

Run `.venv/bin/pytest -q test_electron_packaging.py test_web_environment.py test_web_integration.py`; expected: docs and Web-mode tests pass. Commit with `docs: document Electron desktop workflow`.

## Task 9: Run desktop smoke tests and final verification

**Files:** Create `test_desktop_smoke.py`; modify `TEST_SUMMARY.md`.

**Interfaces:** Smoke test launches the Python sidecar, waits for `/api/healthz`, confirms loopback, and terminates it; test summary records exact platform results.

- [ ] **Step 1: Write and run the sidecar smoke test.**

Launch `[sys.executable, "backend_app.py", "--port", str(port)]`, poll `http://127.0.0.1:<port>/api/healthz` with a deadline, assert `{"status":"ok"}`, terminate in `finally`, and assert exit. Run `.venv/bin/pytest -q test_desktop_smoke.py`; expected: fail until sidecar is available, then pass.

- [ ] **Step 2: Run all automated checks.**

Run `.venv/bin/pytest -q`, `npm run typecheck`, `npm run test:frontend`, and `npm run build`. Record unrelated pre-existing integration failures by exact test name instead of changing them in this task.

- [ ] **Step 3: Verify macOS and Windows packages.**

On macOS run `npm run package:mac`, launch the `.app`, verify React startup, dynamic sidecar, source step, and clean exit. On Windows x64 install the NSIS output and verify directory/file dialogs, paths, progress, Vault opening, and clean exit. If a GUI/platform is unavailable, record that check as not run and retain sidecar/API evidence.

- [ ] **Step 4: Verify final worktree and commit records.**

Run:

```bash
git status --short --branch
git diff --check
git diff -- "欢迎使用Obsidian.md"
```

Expected: the welcome-document change remains untouched and unstaged. Update `TEST_SUMMARY.md` with actual results and commit `test: verify Electron desktop workflow`.

## Self-review checklist

- Spec coverage: Tasks 2–3 cover backend health, loopback binding, lifecycle, preload isolation, and safe shutdown; Tasks 4–6 cover the five-step React wizard, progress, logs, results, and close confirmation; Tasks 7–9 cover sidecars, builder targets, documentation, macOS/Windows acceptance, and clean exit.
- Placeholder scan: every production behavior names a file, interface, test, and command; no unbounded implementation instruction remains.
- Type consistency: `window.desktop` is declared once and exposed by preload; `createApiClient` and `connectMigrationEvents` are the renderer transport entry points; `backend_app.run_backend` and `/api/healthz` are used consistently.
- Scope safety: PyWebView files are removed only after Electron packaging and smoke checks; `欢迎使用Obsidian.md` is outside all staged paths.
