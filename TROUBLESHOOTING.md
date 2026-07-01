# 故障排除

## 环境检查

```bash
python3 migrate.py doctor --vault /path/to/ObsidianVault
```

`doctor` 会检查 Python、任务目录、vault 写入权限、磁盘空间、路径长度、Web 端口和 `evernote-backup` 可用性。

## 账号同步失败

先禁用代理并重试：

```bash
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy
python3 migrate.py migrate --username you@example.com --vault /path/to/ObsidianVault
```

两步验证账号需要使用应用专用密码。如果账号同步仍不可用，请先导出 ENEX，再使用：

```bash
python3 migrate.py import-enex notes.enex --vault /path/to/ObsidianVault
```

## 任务中断

任务状态保存在 `~/.evernote2obsidian/tasks/<task_id>/`，可以恢复：

```bash
python3 migrate.py resume <task_id>
```

恢复会跳过已 checkpoint 的 ENEX 文件和 note id。

## 查看报告

```bash
python3 migrate.py report <task_id>
python3 migrate.py report <task_id> --json
```

报告包含输出路径、统计、错误、警告、checkpoint 和校验信息。

## 删除任务缓存

```bash
python3 migrate.py cleanup <task_id> --yes
```
