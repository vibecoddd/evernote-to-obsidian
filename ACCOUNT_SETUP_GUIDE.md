# 账号设置指南

自动导出模式用于印象笔记中国版账号同步。如果账号同步失败，优先用本地 ENEX 导入作为稳定路径。

## 常见原因

- 邮箱地址错误或账号不存在。
- 选择了错误的服务区域。
- 密码错误。
- 两步验证账号未使用应用专用密码。
- 本地代理影响 `evernote-backup` 访问印象笔记服务器。

## 建议流程

1. 先在浏览器登录 https://app.yinxiang.com，确认账号可用。
2. 如启用两步验证，在账号安全设置中生成应用专用密码。
3. 启动前临时禁用代理：

```bash
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy
python3 migrate.py web
```

4. 在 Web 自动导出模式中输入邮箱、密码和目标 vault 路径。

## CLI 检查

```bash
python3 migrate.py doctor --vault /path/to/ObsidianVault
python3 migrate.py migrate --username you@example.com --vault /path/to/ObsidianVault
```

如果账号同步仍失败，先通过印象笔记客户端或其它工具导出 ENEX，再运行：

```bash
python3 migrate.py import-enex notes.enex --vault /path/to/ObsidianVault
```
