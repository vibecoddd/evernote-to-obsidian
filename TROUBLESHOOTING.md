# 🔧 故障排除指南

## ❌ 导出失败：初始化失败

### 🔍 问题描述
运行迁移工具时出现"导出失败：初始化失败"错误，通常发生在evernote-backup初始化阶段。

### 🎯 常见原因和解决方案

#### 1. 📦 依赖问题
**症状**: evernote-backup未正确安装或版本过旧
**解决方案**:
```bash
# 重新安装最新版本
pip install evernote-backup --upgrade

# 验证安装
evernote-backup --version
```

#### 2. 🌐 网络连接问题
**症状**: 无法连接到印象笔记服务器
**解决方案**:
```bash
# 测试网络连接
curl -s https://yinxiang.com  # 中国版
curl -s https://evernote.com  # 国际版

# 如果无法连接，检查防火墙和代理设置
```

#### 3. 🔐 账号认证问题
**症状**: 用户名密码错误或认证失败
**解决方案**:
- ✅ 确认用户名是邮箱地址格式
- ✅ 在浏览器中验证账号密码正确
- ✅ 选择正确的印象笔记版本（中国版/国际版）
- ✅ 如果账号启用了两步验证，需要使用应用密码

#### 4. 🏗️ 后端选择错误
**症状**: 选错了印象笔记版本
**解决方案**:
- 中国用户（yinxiang.com）: 选择 `china`
- 国际用户（evernote.com）: 选择 `international`

#### 5. 🔒 两步验证问题
**症状**: 启用了2FA但未正确处理
**解决方案**:
1. 登录印象笔记网站
2. 进入设置 → 安全性
3. 生成应用专用密码
4. 使用应用密码而不是普通密码

#### 6. 📁 权限问题
**症状**: 临时目录无法创建或写入
**解决方案**:
```bash
# 检查临时目录权限
ls -la /tmp/evernote_migration

# 手动创建临时目录
mkdir -p /tmp/evernote_migration
chmod 755 /tmp/evernote_migration
```

#### 7. 🕒 超时问题
**症状**: 网络缓慢导致初始化超时
**解决方案**:
- 重试操作
- 检查网络连接稳定性
- 尝试在网络较好的时间段操作

### 🧪 调试方法

#### 方法1: 使用调试脚本
```bash
cd /root/vibecoding/evernote-to-obsidian
python3 debug_evernote.py
```

#### 方法2: 手动测试evernote-backup
```bash
# 创建测试目录
mkdir -p /tmp/test_evernote
cd /tmp/test_evernote

# 手动运行初始化
evernote-backup init-db --backend china  # 或 international

# 查看详细错误信息
```

#### 方法3: 使用测试脚本
```bash
cd /root/vibecoding/evernote-to-obsidian
python3 test_export.py
```

### 📝 错误信息解读

| 错误关键词 | 可能原因 | 解决方案 |
|------------|----------|----------|
| `authentication` | 账号密码错误 | 验证账号密码，检查后端选择 |
| `network`/`connection` | 网络连接问题 | 检查网络，尝试VPN |
| `2fa`/`two-factor` | 两步验证问题 | 使用应用密码 |
| `timeout` | 超时 | 重试，检查网络稳定性 |
| `permission` | 权限不足 | 检查目录权限 |
| `command not found` | 依赖未安装 | 重新安装evernote-backup |

### 🆘 进一步求助

如果以上方法都无法解决问题：

1. **收集错误信息**:
   ```bash
   python3 migrate.py --wizard 2>&1 | tee migration_log.txt
   ```

2. **提交Issue**: 前往 https://github.com/vibecoddd/evernote-to-obsidian/issues
   - 附上完整的错误日志
   - 说明操作系统和Python版本
   - 描述具体的操作步骤

3. **社区求助**:
   - 印象笔记官方论坛
   - Obsidian中文社区
   - GitHub Discussions

### 💡 预防措施

1. **定期更新**: 保持工具和依赖的最新版本
2. **备份重要**: 在迁移前备份重要笔记
3. **测试环境**: 先用少量笔记测试
4. **网络稳定**: 选择网络稳定的时间和环境进行迁移

---

## 🚀 快速修复命令

如果您确定是依赖或配置问题，可以尝试以下一键修复：

```bash
# 1. 重新安装所有依赖
pip install -r requirements.txt --upgrade

# 2. 验证evernote-backup
evernote-backup --version

# 3. 运行调试脚本
python3 debug_evernote.py

# 4. 重新尝试迁移
python3 migrate.py --wizard
```

祝您迁移成功！🎉