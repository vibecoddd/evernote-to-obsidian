# 印象笔记到 Obsidian 迁移工具

发布主线集中在 `src/evernote_to_obsidian/`：CLI、Web UI、任务状态、ENEX 解析、Markdown 写入和报告都共用同一套实现。

## 快速开始

```bash
python3 -m pip install -r requirements.txt

# 检查本机环境
python3 migrate.py doctor --vault /path/to/ObsidianVault

# 导入本地 ENEX 文件
python3 migrate.py import-enex notes.enex --vault /path/to/ObsidianVault

# 从印象笔记中国版账号同步并迁移
python3 migrate.py migrate --username you@example.com --vault /path/to/ObsidianVault

# 启动本地 Web 界面
python3 migrate.py web
```

开发和测试环境使用：

```bash
python3 -m pip install -r requirements-dev.txt
pytest -q
python3 packaging/smoke_test.py
```

## Web UI

启动：

```bash
python3 migrate.py web
```

Web 服务默认只绑定 `127.0.0.1`。页面会注入一次性的本地 session token，敏感 API、上传、报告、任务列表和任务清理都必须携带该 token。

Web 支持两种模式：

- 自动导出：输入印象笔记中国版账号密码，后端调用 `evernote-backup` 同步并导出 ENEX，再执行迁移。
- 文件上传：上传已有 ENEX 文件，创建后台任务，实时查看转换进度。

两种模式都必须明确填写目标 Obsidian vault 路径，不再提供默认 `/tmp/obsidian_vault`。

## 任务与恢复

任务状态默认写入 `~/.evernote2obsidian/tasks/<task_id>/`，可通过 `--app-data` 改到其它目录。

迁移过程中会保存：

- ENEX 文件清单
- 已处理 ENEX 文件 checkpoint
- 已处理 note id checkpoint
- 每条笔记的输出路径和附件清单
- 校验结果和报告

恢复任务：

```bash
python3 migrate.py resume <task_id>
```

删除本地任务缓存：

```bash
python3 migrate.py cleanup <task_id> --yes
```

Web 结果页也会从服务端任务状态读取历史，并可删除任务缓存。

## 输出校验

迁移完成前会检查：

- 已写入笔记文件是否存在
- Markdown frontmatter 是否可解析
- 附件文件是否存在
- 附件 md5 是否匹配 ENEX 资源 hash
- 笔记正文是否包含应有附件链接
- 笔记数和附件数是否与任务状态一致

写入笔记和附件时使用同目录临时文件加原子替换，降低中断导致半文件的风险。

## 打包

```bash
# macOS
bash packaging/build_macos.sh

# Windows
powershell -ExecutionPolicy Bypass -File packaging/build_windows.ps1
```

打包入口是 `migrate.py`，PyInstaller 会携带 `templates/`、`static/`、`docs/` 和烟测 ENEX fixture。

## Codex / Claude Code CLI

仓库也提供可安装的非交互命令，Codex 会读取 `AGENTS.md`，Claude Code 会读取
`CLAUDE.md`：

```bash
# 安装 CLI
python3 -m pip install -e .

# 先预览；--json 便于编码助手解析结果
evernote-to-obsidian convert \
  --input /path/export.enex \
  --output /path/ObsidianVault \
  --preview --json

# 确认预览结果后执行转换
evernote-to-obsidian convert \
  --input /path/export.enex \
  --output /path/ObsidianVault \
  --json

# 完整导出迁移（不会自动打开 Obsidian）
EVERNOTE_USERNAME='user@example.com' \
EVERNOTE_PASSWORD='app-password' \
evernote-to-obsidian migrate \
  --config /path/config.yaml --no-open --json
```

机器模式会输出单个 JSON 对象并使用明确退出码。请勿将密码写入命令参数或提交到仓库的配置文件。

## 目录

```text
migrate.py                       # CLI 入口
src/evernote_to_obsidian/        # 发布主线实现
templates/                       # Web UI 模板
static/                          # Web UI 静态资源
tests/                           # 自动化测试
packaging/                       # 打包与烟测
docs/                            # 发布设计和检查清单
```

## 依赖

运行时依赖见 `requirements.txt`。测试、打包等开发依赖见 `requirements-dev.txt`。
