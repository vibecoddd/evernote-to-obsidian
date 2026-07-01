# Web 界面使用指南

Web 界面和 CLI 共用 `src/evernote_to_obsidian/` 的任务引擎，支持本地 ENEX 上传和印象笔记中国版账号同步。

## 启动

```bash
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy
python3 migrate.py web
```

服务默认绑定 `127.0.0.1`，启动后会自动打开本地浏览器。不要把该服务暴露到公网。

## 使用步骤

1. 进入“迁移”页面。
2. 选择“自动导出模式”或“文件上传模式”。
3. 明确填写目标 Obsidian vault 路径。
4. 开始迁移并等待后台任务完成。
5. 在“结果”页面查看服务端任务历史、报告和缓存清理入口。

## 自动导出模式

自动模式会调用 `evernote-backup==1.13.1`：

- 首个发布版主打印象笔记中国版。
- 密码只用于当前同步流程，不写入任务状态或日志。
- 如果启用了两步验证，请使用应用专用密码。

## 文件上传模式

上传 `.enex` 文件后，后端会创建任务并后台执行。页面会先加入当前任务的 Socket.IO room，再接收进度事件。

## 故障排除

```bash
python3 migrate.py doctor --vault /path/to/ObsidianVault
python3 migrate.py report <task_id> --json
python3 migrate.py resume <task_id>
```

如需删除本地任务缓存：

```bash
python3 migrate.py cleanup <task_id> --yes
```
