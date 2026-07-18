## Implementation

- Deleted the retired PyWebView desktop entry point, packaging tests, build script, PyInstaller spec, and macOS-only build requirements: `macos_app.py`, `test_macos_app.py`, `test_macos_packaging.py`, `scripts/build_macos_app.py`, `packaging/macos/evernote_to_obsidian.spec`, and `requirements-macos-build.txt`.
- Added `ELECTRON_CLIENT.md` and updated `README.md` and `MACOS_CLIENT.md` to document Electron development, macOS `.dmg` and Windows NSIS packaging, renderer/sidecar startup and shutdown, loopback health checks, resource diagnostics, Windows path behavior, Gatekeeper, signing, and notarization.
- Removed PyWebView from normal requirements; `requirements-desktop-build.txt` continues to include normal requirements plus PyInstaller.
- Updated Electron packaging documentation assertions and ran `.venv/bin/pytest -q test_electron_packaging.py test_web_environment.py test_web_integration.py` (7 passed, 1 skipped), `npm run typecheck`, and `npm run build` (38 frontend tests passed).
- Concerns: the local Node runtime is v21.7.3 while the project declares Node >=22.12.0. npm installation and the requested typecheck/build completed, but emitted engine warnings; release builds should use the declared Node version. npm also reported two dependency-audit vulnerabilities that are outside Task 8 scope. One concurrent full frontend-suite run had an existing focus assertion failure in `frontend/src/App.test.tsx`; the isolated test then passed three consecutive runs, and Task 8 does not modify that UI code.

## Fixes

- Corrected the clean-checkout Electron development flow: install dependencies from the repository root, run `npm run build:renderer && npm run build:electron`, then launch with `npx electron .` from that same directory. The guide now states that `dev:renderer` only starts Vite and cannot provide Electron HMR until the main process explicitly loads its URL.
- Strengthened the packaging contract test to verify the manifest's build outputs and the documentation's exact build-before-launch and repository-root sidecar requirements.

- Reclassified the legacy macOS plan and design as historical context and directed all current implementation, packaging, and troubleshooting guidance to the Electron plan, design, and `ELECTRON_CLIENT.md` commands.
- Updated the Electron plan's completed-retirement wording so it no longer instructs readers to act on deleted PyWebView files, and stated explicitly in the Electron guide that desktop users do not need PyWebView.
- Strengthened `test_electron_packaging.py` to require the Task 8 documentation contract: npm install and platform packaging commands, dynamic loopback startup, health timeout, sidecar shutdown, macOS `.dmg`, Windows NSIS and path handling, missing-resource diagnostics, signing/notarization, and no PyWebView requirement.
- Verification: `.venv/bin/pytest -q test_electron_packaging.py test_web_environment.py test_web_integration.py` (7 passed, 1 skipped); `npm run typecheck` passed; `npm run build` passed with 38 frontend tests; `git diff --check` passed. The tracked-file reference scan found only the historical deletion record in this report.
- Concerns: the existing Node-version and dependency-audit concerns above still apply. The npm build also emitted Vite's CJS Node API deprecation warning.

## Fixes

- Made the Electron clean-checkout runtime prerequisite explicit in `ELECTRON_CLIENT.md` and the README: Node.js >=22.12.0 is required before `npm install`, `npm run build`, or Electron launch. The guides now state that npm engine warnings do not enforce this floor and that release packaging must use Node 22.12+.
- Added deterministic packaging-documentation assertions for the declared Node engine, required runtime wording, the non-enforcing npm warning caveat, and the release-packaging floor. Kept the existing `package.json` engine declaration and did not add a platform-specific preinstall hook or version-manager file.

## Fixes

- Added the prominent Node.js >=22.12.0 prerequisite and npm engine-warning caveat before the Electron/macOS install and packaging command blocks in `MACOS_CLIENT.md` and the retained historical macOS plan and design. These legacy documents now identify `ELECTRON_CLIENT.md` as the canonical current workflow.
- Extended `test_electron_packaging.py` so every maintained Electron/macOS documentation entry point must state that prerequisite and caveat before its actionable command block.

## Fixes

- Added a Node.js >=22.12.0 prerequisite, npm engine-warning caveat, and `ELECTRON_CLIENT.md` canonical-guidance link to the active Electron implementation plan and design. The plan places the prerequisite before every actionable npm command; the design keeps its architectural content while directing operational commands to the canonical guide.
- Extended `test_electron_packaging.py` to enforce that both active Electron documents contain the prerequisite, caveat, and canonical-guidance link, and that any actionable npm command follows the prerequisite.

## Fixes

- Corrected the active Electron documentation assertion to use real word boundaries when matching npm commands and to verify the Node.js >=22.12.0 prerequisite plus npm engine-warning caveat before every actionable command in the active plan and design documents.

## Fixes

- Replaced the hand-picked documentation command tuple with one explicit inventory of all active and historical Electron/macOS command entry points. The regression test now enumerates each supported, concrete npm invocation (`install`, `ci`, `exec`, `run`, `test`, `build`, and the three platform packaging scripts) and requires the Node.js >=22.12.0 prerequisite and npm engine-warning caveat before every match.
- Kept both historical macOS documents in scope because they retain actionable quick-reference commands; the matcher uses complete npm invocation forms so prose that merely mentions npm cannot create a false positive.
- Reordered the prerequisite wording in README, Electron, and macOS guides so the textual prerequisite and caveat precede their command references as well as their command blocks.

## Fixes

- Tightened the exhaustive documentation matcher to recognize only supported executable npm forms: `install`, `ci`, `test` with flags, `run <script>`, and `exec <package>`. It now rejects unsupported direct `npm build` and `npm package:*` forms, a bare `npm exec`, and generic npm prose while preserving the per-document Node.js >=22.12.0 and npm engine-warning ordering checks.

## Fixes

- Required whitespace or end-of-input boundaries for matched npm command and script tokens, preventing `npm test:frontend`, `npm run build:renderer!`, `npm install:all`, and `npm ci:clean` from being treated as supported commands. The `npm exec` matcher now also requires a non-flag package token, so `npm exec -- --mac` is rejected while `npm exec electron-builder -- --mac` remains supported. Added explicit negative regression cases and retained the exhaustive prerequisite-order assertions across every Electron/macOS documentation entry point.
