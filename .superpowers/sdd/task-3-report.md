# Task 3: Electron main lifecycle and preload bridge report

## Status

Implemented the Electron main-process lifecycle, loopback backend launcher, health polling, isolated preload bridge, renderer `window.desktop` typing, IPC handlers, single-instance behavior, navigation restriction, and bounded backend shutdown.

## Commits

- Prerequisite Task 2 state: `2368b7a` (`fix: complete Task 2 export cancellation`), including the completed backend entry and health endpoint from the prior Task 2 commits.
- Task 3 implementation: `cb3295e` (`feat: add Electron backend lifecycle and preload bridge`).

## Files changed

- Created `electron/main.ts`: dynamic loopback port allocation, `/api/healthz` polling, development and packaged sidecar launches, lifecycle/IPC/window handling, navigation policy, and shutdown fallback.
- Created `electron/preload.ts`: the seven-method `contextBridge` whitelist.
- Created `electron/main.test.ts`: port/health, single-instance focus, renderer load, and stop-before-quit tests using injected Electron/backend doubles.
- Created `electron/preload.test.ts`: exact bridge whitelist, IPC-channel, and unsubscribe tests.
- Created `frontend/src/types/desktop.d.ts`: renderer-side `DesktopBridge` declaration.
- Modified `electron/types.ts`: `BackendHandle` and `StartBackendOptions` interfaces.
- Modified `tsconfig.electron.json`: enables Vitest globals for Electron tests.

## RED/GREEN evidence

### Port and health polling

RED command:

```text
node --input-type=module -e "...startVitest(...electron/main.test.ts...)"
FAIL electron/main.test.ts: Cannot find module './main'
```

GREEN command:

```text
node --input-type=module -e "...startVitest(...electron/main.test.ts...)"
PASS electron/main.test.ts (3 tests)
```

The tests cover retrying a rejected health request, a final timeout message containing the health URL and last failure, and allocation/release of an ephemeral loopback port.

### Preload, single-instance, and shutdown

RED command:

```text
node --input-type=module -e "...startVitest(...electron/main.test.ts, electron/preload.test.ts...)"
FAIL createDesktopLifecycle is not a function
FAIL Cannot find module './preload'
```

GREEN command/output:

```text
node --input-type=module -e "...startVitest(...electron/main.test.ts, electron/preload.test.ts...)"
PASS electron/preload.test.ts (2 tests)
PASS electron/main.test.ts (5 tests)
Test Files  2 passed (2)
Tests  7 passed (7)
```

The tests use dependency injection and Electron mocks; no BrowserWindow, Electron application, or Python sidecar is launched.

## Final verification

```text
npm run typecheck
PASS: tsc -p tsconfig.json --noEmit && tsc -p tsconfig.electron.json --noEmit

focused Electron Vitest command (above)
PASS: 2 files, 7 tests

git diff --check
PASS: no output
```

Self-review checked each Task 3 requirement: loopback dynamic port and bounded poll; development `PYTHON`/`python3` and packaged `resourcesPath/backend/evernote-backend[.exe]` launch paths; post-health window creation; secure `webPreferences`; renderer-only navigation; the seven-method preload surface; path/close IPC; one-instance focus; and graceful-then-forceful shutdown.

## Concerns

- The inherited `vitest.config.ts` has `include: ["frontend/**/*.test.{ts,tsx}"]`. Consequently, the brief's literal `npm run test:frontend -- electron` reports “No test files found.” It was left unchanged because it is outside Task 3’s allowed files. Focused Electron tests were run through Vitest’s Node API with an `electron/**/*.test.ts` include and Node environment.
- This task verifies lifecycle behavior with mocks as required. A live Electron/Python sidecar smoke test and packaged-resource execution remain packaging/smoke-test work for later tasks.
- As required by the brief, the port is reserved by binding then released before sidecar spawn. There is an inherent small bind-to-spawn race; health polling makes a failed launch observable.
- The pre-existing modification to `欢迎使用Obsidian.md` was inspected only to verify it was unchanged, and remains unstaged.
