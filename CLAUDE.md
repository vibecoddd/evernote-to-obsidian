# Claude Code CLI workflow

本仓库提供可安装命令 `evernote-to-obsidian`，供 Claude Code 通过 shell 调用。

## 推荐流程

```bash
python3 -m pip install -e .
evernote-to-obsidian --help
evernote-to-obsidian convert --input /path/export.enex --output /path/vault --preview --json
evernote-to-obsidian convert --input /path/export.enex --output /path/vault --json
```

先运行预览命令，确认 JSON 中的 `success`、`stats` 和 `error`，再执行写入命令。目录输入可以替换单个 ENEX 文件路径。

如果需要执行完整的 Evernote 导出迁移：

```bash
EVERNOTE_USERNAME='user@example.com' \
EVERNOTE_PASSWORD='app-password' \
evernote-to-obsidian migrate --config /path/config.yaml --no-open --json
```

不要把密码放在命令参数或提交到仓库的 YAML 中；使用环境变量或本地未提交配置。`--json` 模式 stdout 只有一个 JSON 对象，遇到 `success: false` 时先读取 `error`，不要重复执行写入命令。
