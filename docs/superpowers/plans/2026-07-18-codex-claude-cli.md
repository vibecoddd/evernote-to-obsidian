# Codex 与 Claude Code CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有印象笔记迁移能力包装成可安装、非交互、支持 JSON 输出的 `evernote-to-obsidian` CLI，供 Codex 和 Claude Code 通过 shell 稳定调用。

**Architecture:** 新增一个 argparse 适配层 `src/agent_cli.py`，只负责参数、配置覆盖、调用现有转换器/迁移器和输出结果；新增 `pyproject.toml` 以 console script 暴露该适配层。合并到发布主线时，适配层改为调用 `evernote_to_obsidian` 包内的 `ENEXParser`、`MigrationRunner` 和 `EvernoteBackupSource`，不恢复旧的扁平 `src/*.py` 模块。

**Tech Stack:** Python 3.9+, argparse, setuptools PEP 621 packaging, 现有 Click/PyYAML/lxml/html2text 转换栈, unittest。

## Global Constraints

- 命令名固定为 `evernote-to-obsidian`。
- `convert --input` 接受单个 `.enex` 文件或包含 `.enex` 文件的目录。
- `convert --output` 和命令行输入/输出覆盖优先于 YAML 配置。
- `--json` 模式 stdout 只能输出一个可由 `json.loads()` 解析的 JSON 对象。
- 成功退出码为 `0`，业务失败为 `1`，argparse 参数错误为 `2`。
- `migrate` 缺少凭据时不得读取 stdin；凭据来源为配置中的 `evernote_credentials` 或 `EVERNOTE_USERNAME`/`EVERNOTE_PASSWORD`。
- JSON 机器模式不自动打开 Obsidian；普通旧入口行为保持不变。
- 不复制或重写 ENEX 解析、Markdown 转换、附件保存和同步逻辑。
- 每个行为先写测试、确认失败，再写最小实现并运行回归测试。

## File Map

- Create: `pyproject.toml` — setuptools 构建元数据、依赖和 `evernote-to-obsidian` console script。
- Create: `src/agent_cli.py` — argparse 解析、命令分发、配置合并、结构化结果和 JSON 输出。
- Use: `src/evernote_to_obsidian/` — 调用发布主线包内的 ENEX 解析、迁移 runner 和 Evernote 导出封装。
- Create: `test_agent_cli.py` — CLI 帮助、JSON、预览、实际转换、配置覆盖和无凭据行为测试。
- Create: `AGENTS.md` — Codex 使用契约。
- Create: `CLAUDE.md` — Claude Code 使用契约。
- Modify: `README.md` — 安装、命令和机器模式文档。

### Task 1: Add a failing CLI contract test

**Files:**
- Create: `test_agent_cli.py`

**Interfaces:**
- Consumes: future `agent_cli.main(argv: Sequence[str] | None) -> int`.
- Produces: executable tests for the public command contract before implementation exists.

- [ ] **Step 1: Write the failing tests**

Create a self-contained temporary ENEX fixture and test these public behaviors:

```python
class AgentCliTests(unittest.TestCase):
    def test_preview_json_is_single_object_and_does_not_write(self):
        code, payload, stdout = self.run_cli(
            "convert", "--input", str(self.enex),
            "--output", str(self.vault), "--preview", "--json"
        )
        self.assertEqual(code, 0)
        self.assertEqual(stdout.count("\n"), 1)
        self.assertTrue(payload["success"])
        self.assertEqual(payload["command"], "convert")
        self.assertEqual(payload["mode"], "preview")
        self.assertFalse(self.vault.exists())

    def test_convert_json_writes_markdown(self):
        code, payload, _ = self.run_cli(
            "convert", "--input", str(self.enex),
            "--output", str(self.vault), "--json"
        )
        self.assertEqual(code, 0)
        self.assertTrue(payload["success"])
        self.assertGreaterEqual(payload["stats"]["converted_notes"], 1)
        self.assertEqual(len(list(self.vault.rglob("*.md"))), 1)

    def test_command_line_paths_override_yaml_config(self):
        config = self.temp_dir / "config.yaml"
        config.write_text(
            "input:\n  enex_files: []\n"
            "output:\n  obsidian_vault: /wrong/path\n",
            encoding="utf-8",
        )
        code, payload, _ = self.run_cli(
            "convert", "--config", str(config),
            "--input", str(self.enex), "--output", str(self.vault),
            "--preview", "--json"
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["output"], str(self.vault.resolve()))

    def test_migrate_without_credentials_fails_without_prompt(self):
        code, payload, _ = self.run_cli(
            "migrate", "--output", str(self.vault), "--json"
        )
        self.assertEqual(code, 1)
        self.assertFalse(payload["success"])
        self.assertIn("credentials", payload["error"].lower())
```

`run_cli()` must import `src.agent_cli`, redirect stdout to a `StringIO`, call `main(argv)`, assert exactly one JSON line, and return `(code, json.loads(stdout), stdout)`.

- [ ] **Step 2: Run the focused test to verify it fails**

Run:

```bash
python3 -m unittest -v test_agent_cli.AgentCliTests
```

Expected: import failure because `src/agent_cli.py` does not exist yet. Do not add production code in this step.

- [ ] **Step 3: Commit the red test**

```bash
git add test_agent_cli.py
git commit -m "test: define agent CLI contract"
```

### Task 2: Add installable package metadata

**Files:**
- Create: `pyproject.toml`

**Interfaces:**
- Consumes: `src/agent_cli.py` module created in Task 3.
- Produces: `pip install -e .` and the executable `evernote-to-obsidian`.

- [ ] **Step 1: Write the packaging smoke test**

Extend `test_agent_cli.py` with a test that verifies the repository metadata exposes the expected project and script without installing anything:

```python
def test_pyproject_declares_console_script(self):
    text = (Path(__file__).parent / "pyproject.toml").read_text(encoding="utf-8")
    self.assertIn('name = "evernote-to-obsidian"', text)
    self.assertIn('evernote-to-obsidian = "agent_cli:main"', text)
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest -v test_agent_cli.AgentCliTests.test_pyproject_declares_console_script
```

Expected: FAIL because `pyproject.toml` is absent.

- [ ] **Step 3: Add minimal PEP 621 metadata**

Create a setuptools configuration with `package-dir = {"" = "src"}`, `py-modules` containing `agent_cli`, `config`, `enex_parser`, `markdown_converter`, `file_organizer`, `sync_manager`, `obsidian_manager`, `deduplication_manager`, `evernote_exporter`, `unified_migrator`, and `evernote2obsidian`, and this script:

```toml
[project.scripts]
evernote-to-obsidian = "agent_cli:main"
```

Copy the runtime dependencies from `requirements.txt` into `[project].dependencies`, retain `requires-python = ">=3.9"`, and set version `0.1.0`.

- [ ] **Step 4: Run the packaging test and build metadata check**

Run:

```bash
python3 -m unittest -v test_agent_cli.AgentCliTests.test_pyproject_declares_console_script
python3 -m pip wheel --no-deps --no-build-isolation . -w /tmp/evernote-to-obsidian-wheel
```

Expected: the test passes and `pip wheel` exits `0`.

- [ ] **Step 5: Commit packaging metadata**

```bash
git add pyproject.toml test_agent_cli.py
git commit -m "build: expose installable migration CLI"
```

### Task 3: Implement the structured non-interactive CLI

**Files:**
- Create: `src/agent_cli.py`
- Modify: `src/evernote2obsidian.py:22-51, 400-424`

**Interfaces:**
- Consumes: `Config`, `EvernoteToObsidianConverter`, `UnifiedMigrator`.
- Produces: `build_parser()`, `run_convert(args) -> dict`, `run_migrate(args) -> dict`, `main(argv=None) -> int`.

- [ ] **Step 1: Add the minimal injected-config constructor test**

Add a test that constructs `Config`, sets valid temporary input/output paths, passes it to `EvernoteToObsidianConverter(config=config)`, and asserts `converter.config is config`. This catches the existing initialization-order bug without mocking conversion internals.

- [ ] **Step 2: Run the focused test to verify it fails**

Run:

```bash
python3 -m unittest -v test_agent_cli.AgentCliTests.test_converter_accepts_prepared_config
```

Expected: FAIL with `TypeError` because the constructor does not accept `config`.

- [ ] **Step 3: Implement config injection and the CLI adapter**

Change the converter constructor to:

```python
def __init__(self, config_path: Optional[str] = None,
             config: Optional[Config] = None):
    colorama.init(autoreset=True)
    if config is not None and config_path is not None:
        raise ValueError("Pass either config_path or config, not both")
    self.config = config if config is not None else Config(config_path)
    if not self.config.validate():
        raise ValueError("Configuration validation failed")
    self._setup_logging()
    self.parser = ENEXParser()
    self.converter = MarkdownConverter(self.config.get_all())
    self.organizer = FileOrganizer(self.config.get_all())
    self.sync_manager = SyncManager(self.config.get_all())
```

Update the old Click entry to pass `converter_config` into the constructor instead of constructing a default converter and replacing its config afterward.

Implement `src/agent_cli.py` with these exact public behaviors:

```python
def build_parser() -> argparse.ArgumentParser: ...
def run_convert(args: argparse.Namespace) -> dict: ...
def run_migrate(args: argparse.Namespace) -> dict: ...
def main(argv: Optional[Sequence[str]] = None) -> int: ...
```

`run_convert` must resolve the input path, set `input.enex_files` for a file or `input.input_directory` for a directory, set `output.obsidian_vault`, disable console logging for JSON mode, construct `EvernoteToObsidianConverter(config=prepared_config)`, support `--reset` and `--preview`, and return the fixed keys `success`, `command`, `mode`, `input`, `output`, `stats`, and `error`.

`run_migrate` must load `Config`, set the optional output override, resolve credentials in this order (config mapping, then the two environment variables), return a credential error before constructing `UnifiedMigrator` when both values are absent, set `migration.auto_open_obsidian` to `not args.no_open`, assign the prepared config to `UnifiedMigrator.config`, call `run_migration()`, and return the same result shape.

`main` must use argparse subcommands `convert` and `migrate`, define `--json` on both, catch `KeyboardInterrupt` and ordinary exceptions, capture stdout/stderr around execution in JSON mode with `contextlib.redirect_stdout` and `redirect_stderr`, print exactly one `json.dumps(..., ensure_ascii=False)` object, and return `0` only for `success=True`, otherwise `1`.

- [ ] **Step 4: Run the focused tests to verify they pass**

Run:

```bash
python3 -m unittest -v test_agent_cli.AgentCliTests
```

Expected: all CLI contract tests pass and JSON stdout contains one object.

- [ ] **Step 5: Commit the CLI implementation**

```bash
git add src/agent_cli.py src/evernote2obsidian.py test_agent_cli.py
git commit -m "feat: add structured non-interactive CLI"
```

### Task 4: Document Codex and Claude Code workflows

**Files:**
- Create: `AGENTS.md`
- Create: `CLAUDE.md`
- Modify: `README.md` after the existing command-line usage section

**Interfaces:**
- Consumes: installed `evernote-to-obsidian` command and JSON contract from Task 3.
- Produces: copyable instructions for both assistants and human users.

- [ ] **Step 1: Add documentation assertions**

Extend the test suite with:

```python
def test_agent_guides_use_json_preview_command(self):
    for name in ("AGENTS.md", "CLAUDE.md"):
        text = (Path(__file__).parent / name).read_text(encoding="utf-8")
        self.assertIn("evernote-to-obsidian convert", text)
        self.assertIn("--preview", text)
        self.assertIn("--json", text)
        self.assertIn("--no-open", text)
```

- [ ] **Step 2: Run the documentation test to verify it fails**

Run:

```bash
python3 -m unittest -v test_agent_cli.AgentCliTests.test_agent_guides_use_json_preview_command
```

Expected: FAIL because the guide files do not exist.

- [ ] **Step 3: Write the two guides and README section**

Both guides must state: install with `python3 -m pip install -e .`; inspect `--help`; use `convert --preview --json` before writing; use `convert --json` to execute; use `migrate --config ... --no-open --json` for full migration; never place passwords in command arguments or committed YAML; inspect the JSON `success`, `stats`, and `error` fields.

Add the same workflow to README with a short note that Codex reads `AGENTS.md` and Claude Code reads `CLAUDE.md`.

- [ ] **Step 4: Run the documentation test**

Run:

```bash
python3 -m unittest -v test_agent_cli.AgentCliTests.test_agent_guides_use_json_preview_command
```

Expected: PASS.

- [ ] **Step 5: Commit the documentation**

```bash
git add AGENTS.md CLAUDE.md README.md test_agent_cli.py
git commit -m "docs: add Codex and Claude Code CLI workflows"
```

### Task 5: Verify installation and regression behavior

**Files:**
- Modify: none unless verification exposes an implementation defect.

**Interfaces:**
- Consumes: all prior tasks.
- Produces: fresh evidence for installation, CLI behavior and existing tests.

- [ ] **Step 1: Run the complete local CLI test suite**

Run:

```bash
python3 -m unittest -v test_agent_cli.py
```

Expected: all tests pass.

- [ ] **Step 2: Install into a temporary virtual environment**

Run:

```bash
agent_env=$(mktemp -d)
python3 -m venv "$agent_env"
"$agent_env/bin/python" -m pip install --upgrade pip
"$agent_env/bin/python" -m pip install -e .
"$agent_env/bin/evernote-to-obsidian" --version
"$agent_env/bin/evernote-to-obsidian" convert --help
```

Expected: installation exits `0`, version prints `0.1.0`, and help lists `convert` and `migrate`.

- [ ] **Step 3: Run the existing non-network tests**

Run:

```bash
"$agent_env/bin/python" -m unittest -v test_agent_cli.py
python3 -m pytest -q test_integration_steps.py test_web_environment.py
```

Expected: the new tests and existing deterministic tests pass; tests requiring live Evernote credentials are not invoked.

- [ ] **Step 4: Inspect final diff and repository status**

Run:

```bash
git diff --check HEAD~5..HEAD
git status --short --branch
```

Expected: no whitespace errors, only intentional CLI files/documents changed, and no credentials or temporary artifacts tracked.

- [ ] **Step 5: Commit any verification-only fixes and report evidence**

If a verification failure requires a fix, add a regression test first, rerun the focused and full tests, then commit the fix with a message describing the defect. Do not claim completion until the install command, CLI tests and regression tests all have fresh successful output.
