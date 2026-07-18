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

## Fixes

Changed files:

- `electron/main.ts`: bounds every health request with an abortable deadline race; shutdown now waits for an `exit` event or `exitCode` before force-killing an alive child.
- `electron/main.test.ts`: adds never-settling health-fetch, SIGTERM-without-exit, and prematurely-resolved lifecycle-stop regression tests.
- `electron/types.ts`: includes the child-process `once` event interface required for exit observation.
- `vitest.config.ts`: includes `electron/**/*.test.{ts,tsx}` in the default suite.
- `frontend/src/test/setup.ts`: skips the JSDOM root fixture under Electron tests' existing Node environment pragmas.

Exact verification commands and outputs:

```text
$ npm run test:frontend

> evernote-to-obsidian-desktop@0.1.0 test:frontend
> vitest run

The CJS build of Vite's Node API is deprecated. See https://vite.dev/guide/troubleshooting.html#vite-cjs-node-api-deprecated for more details.

 RUN  v3.2.4 /Users/bytedance/orca/workspaces/evernote-to-obsidian/hearturchin

 ✓ electron/preload.test.ts (2 tests) 3ms
 ✓ electron/main.test.ts (8 tests) 87ms
 ✓ frontend/src/main.test.tsx (1 test) 5ms

 Test Files  3 passed (3)
      Tests  11 passed (11)
   Start at  22:08:06
   Duration  1.30s (transform 107ms, setup 372ms, collect 149ms, tests 94ms, environment 785ms, prepare 402ms)
```

```text
$ npm run test:frontend -- electron

> evernote-to-obsidian-desktop@0.1.0 test:frontend
> vitest run electron

The CJS build of Vite's Node API is deprecated. See https://vite.dev/guide/troubleshooting.html#vite-cjs-node-api-deprecated for more details.

 RUN  v3.2.4 /Users/bytedance/orca/workspaces/evernote-to-obsidian/hearturchin

 ✓ electron/preload.test.ts (2 tests) 3ms
 ✓ electron/main.test.ts (8 tests) 83ms

 Test Files  2 passed (2)
      Tests  10 passed (10)
   Start at  22:08:13
   Duration  567ms (transform 76ms, setup 237ms, collect 84ms, tests 86ms, environment 0ms, prepare 286ms)
```

```text
$ npm run typecheck

> evernote-to-obsidian-desktop@0.1.0 typecheck
> tsc -p tsconfig.json --noEmit && tsc -p tsconfig.electron.json --noEmit
```

```text
$ npm run build

> evernote-to-obsidian-desktop@0.1.0 build
> npm run typecheck && npm run test:frontend && npm run build:renderer && npm run build:electron

> evernote-to-obsidian-desktop@0.1.0 typecheck
> tsc -p tsconfig.json --noEmit && tsc -p tsconfig.electron.json --noEmit

> evernote-to-obsidian-desktop@0.1.0 test:frontend
> vitest run

The CJS build of Vite's Node API is deprecated. See https://vite.dev/guide/troubleshooting.html#vite-cjs-node-api-deprecated for more details.

 RUN  v3.2.4 /Users/bytedance/orca/workspaces/evernote-to-obsidian/hearturchin

 ✓ electron/preload.test.ts (2 tests) 3ms
 ✓ electron/main.test.ts (8 tests) 85ms
 ✓ frontend/src/main.test.tsx (1 test) 5ms

 Test Files  3 passed (3)
      Tests  11 passed (11)
   Start at  22:08:26
   Duration  1.10s (transform 164ms, setup 381ms, collect 173ms, tests 93ms, environment 597ms, prepare 389ms)

> evernote-to-obsidian-desktop@0.1.0 build:renderer
> vite build --config vite.config.ts

The CJS build of Vite's Node API is deprecated. See https://vite.dev/guide/troubleshooting.html#vite-cjs-node-api-deprecated for more details.

vite v6.4.1 building for production...
transforming...
✓ 27 modules transformed.
rendering chunks...
computing gzip size...
../dist/renderer/index.html                  0.34 kB │ gzip:  0.27 kB
../dist/renderer/assets/index-DRhG52Vu.js  194.57 kB │ gzip: 60.86 kB
✓ built in 499ms

> evernote-to-obsidian-desktop@0.1.0 build:electron
> tsc -p tsconfig.electron.json
```

The original `vitest.config.ts` concern is resolved: both default frontend test commands now collect the Node-environment Electron lifecycle tests.
