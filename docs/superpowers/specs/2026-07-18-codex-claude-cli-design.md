# Codex 与 Claude Code CLI 支持设计

## 背景

仓库目前有 `migrate.py` 和 `src/evernote2obsidian.py` 两个 Python 入口，但它们依赖当前工作目录、部分流程会进入交互式向导，也没有 Python 打包元数据。因此 Codex 或 Claude Code 虽然可以通过 shell 运行脚本，却不能稳定地发现、安装和调用一个有明确输出契约的迁移命令。

本次目标是增加一个可安装、可脚本化、适合编码助手调用的 CLI，同时保留现有 Web 和人工交互入口。

合并到发布主线时，CLI 适配层改为调用 `src/evernote_to_obsidian/` 包内的 `ENEXParser`、`MigrationRunner` 和 `EvernoteBackupSource`，不再恢复旧的扁平 `src/*.py` 模块。

## 目标与非目标

### 目标

1. 通过 `pip install -e .` 安装后提供 `evernote-to-obsidian` 命令。
2. 提供不依赖交互输入的 ENEX 到 Obsidian 转换命令。
3. 提供完整 Evernote 导出迁移命令；账号信息可通过配置或环境变量提供。
4. 用 `--json` 输出稳定的单个 JSON 对象，便于 Codex 和 Claude Code 读取结果。
5. 使用明确的退出码报告成功、业务失败和参数错误。
6. 提供 `AGENTS.md` 与 `CLAUDE.md`，说明两个编码助手应如何调用 CLI。
7. 不破坏已有的 `python3 migrate.py`、Web 界面和模块级 API。

### 非目标

- 不调用或封装 Codex、Claude 或其他模型 API。
- 不增加 MCP 服务；两个编码助手通过 shell 调用可安装 CLI 即可。
- 不重写现有 ENEX 解析、Markdown 转换和 Obsidian 文件组织逻辑。
- 不在配置文件中新增明文密码要求；环境变量只作为非交互凭据来源。

## 使用契约

### 安装与发现

```bash
python3 -m pip install -e .
evernote-to-obsidian --help
evernote-to-obsidian --version
```

### `convert` 命令

用于已有 ENEX 文件的确定性转换，不需要 Evernote 网络登录：

```bash
evernote-to-obsidian convert \
  --input /path/export.enex \
  --output /path/vault \
  --preview \
  --json
```

行为约定：

- `--input` 接受单个 `.enex` 文件或包含 `.enex` 文件的目录。
- `--output` 指定 Obsidian 库目录；目录不存在时遵循配置中的创建策略。
- `--config` 可提供现有 YAML 配置，命令行输入和输出参数优先级更高。
- `--preview` 只解析并返回统计信息，不写入 Markdown、附件或同步状态。
- `--json` 时 stdout 只输出一个 JSON 对象；进度和诊断信息不得污染 JSON。
- 成功退出码为 `0`；没有有效输入、配置错误或转换失败退出码为 `1`；参数解析错误由 argparse 使用退出码 `2`。

JSON 顶层字段固定为：

```json
{
  "success": true,
  "command": "convert",
  "mode": "preview",
  "input": ["/path/export.enex"],
  "output": "/path/vault",
  "stats": {},
  "error": null
}
```

### `migrate` 命令

用于完整的 Evernote 导出、转换和 Obsidian 库设置：

```bash
EVERNOTE_USERNAME='user@example.com' \
EVERNOTE_PASSWORD='app-password' \
evernote-to-obsidian migrate \
  --config /path/config.yaml \
  --no-open \
  --json
```

行为约定：

- 优先使用配置中的 `evernote_credentials`，否则读取 `EVERNOTE_USERNAME` 和 `EVERNOTE_PASSWORD`。
- 在没有凭据时，机器模式直接返回错误，不进入 prompt；人工模式仍可使用旧向导。
- `--no-open` 禁止迁移完成后启动 Obsidian，默认用于编码助手调用。
- `--json` 使用与 `convert` 相同的顶层字段，并在 `stats` 中返回迁移统计。

## 结构设计

### 安装层

新增 `pyproject.toml`，项目名为 `evernote-to-obsidian`，console script 使用 `agent_cli:main` 指向 `src/agent_cli.py` 的 `main()`。打包时只保留顶层 `agent_cli` 模块，并通过 setuptools package discovery 安装 `evernote_to_obsidian` 包。

### CLI 适配层

新增 `src/agent_cli.py`，只负责：

- 解析子命令和参数；
- 合并 YAML 配置、命令行覆盖项和环境凭据；
- 调用已有 `ENEXParser`、`MigrationRunner` 或 `EvernoteBackupSource`；
- 将内部统计转换为文本或 JSON；
- 将异常映射为稳定退出码。

适配层不复制 ENEX 转换逻辑。`convert --preview` 只解析 ENEX 并返回统计，实际转换交给 `MigrationRunner.import_enex()`。

### 输出层

CLI 以 `run_command()` 返回结构化字典，再由 `emit_result()` 输出。JSON 模式通过临时捕获内部进度输出，确保 stdout 只有最终 JSON；普通模式保持现有彩色进度信息。

### 助手说明

`AGENTS.md` 和 `CLAUDE.md` 采用相同的命令契约，分别说明：先运行 `--help`，文件转换优先使用 `convert --preview --json`，完整迁移使用 `migrate --no-open --json`，不要把账号密码写入命令行参数或提交到仓库。

## 错误处理

- 参数和路径错误在执行前返回结构化错误。
- 业务异常不会输出 Python traceback 到 JSON stdout；错误消息写入 `error`，必要时保留日志文件。
- 输入为空、配置无效、转换没有成功处理任何笔记均视为失败。
- `KeyboardInterrupt` 返回失败结果，不留下半成品成功状态。

## 测试策略

1. CLI 单元测试验证 `--help`、`--version`、子命令参数、退出码和 JSON 结构。
2. 使用临时 ENEX fixture 验证 `convert --preview --json` 不写文件，普通转换产生 Markdown 和附件。
3. 验证 YAML 配置会在组件创建前被命令行输入/输出覆盖。
4. 验证 `migrate` 在缺少环境凭据时直接失败且不等待 stdin。
5. 在独立临时环境执行 `python3 -m pip install -e .`，验证安装后的 console script 可以运行。
6. 运行现有无网络测试，确认 Web 和历史模块测试未被 CLI 改动破坏。

## 验收标准

- `pip install -e .` 成功并能发现 `evernote-to-obsidian`。
- Codex 与 Claude Code 文档中的命令可复制执行。
- JSON 模式 stdout 可被 `json.loads()` 一次解析。
- ENEX 预览和转换的实际行为与现有转换器一致。
- 现有入口保持可用，新增测试和现有相关测试通过。
