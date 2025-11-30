# 账号设置指南 - 解决"导出失败：没有导出任何文件"

## 🎯 常见错误原因

当您看到"导出失败：没有导出任何文件"错误时，通常是因为以下原因：

### 1. 账号不存在错误
**错误信息**: `Username not found!`

**解决方案**:
- ✅ **检查账号邮箱地址是否正确**
- ✅ **确认选择了正确的印象笔记版本**：
  - 中国用户 → 选择"印象笔记中国版"
  - 海外用户 → 选择"Evernote国际版"
- ✅ **确认账号已激活且可正常使用**

### 2. 认证失败
**错误信息**: `Authentication failed` 或 `Login failed`

**解决方案**:
- ✅ **检查密码是否正确**
- ✅ **如果启用了两步验证**：
  1. 登录印象笔记网页版
  2. 进入账户设置 → 安全性
  3. 生成"应用专用密码"
  4. 使用应用密码而不是普通密码

### 3. 网络连接问题
**解决方案**:
```bash
# 1. 临时禁用代理
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy

# 2. 重启Web应用
python web_app.py

# 3. 检查网络连接
ping app.yinxiang.com  # 中国版
ping www.evernote.com  # 国际版
```

## 📋 正确的账号设置步骤

### 步骤1：确定印象笔记版本
- **中国版用户**：如果您在中国注册，通常使用印象笔记中国版
- **国际版用户**：如果您在海外注册，使用Evernote国际版

### 步骤2：验证账号可用性
1. 先在浏览器中登录对应的印象笔记网站：
   - 中国版：https://app.yinxiang.com
   - 国际版：https://www.evernote.com
2. 确认可以正常登录并查看笔记

### 步骤3：处理两步验证
如果您的账号启用了两步验证：

1. **中国版操作**：
   - 登录 https://app.yinxiang.com
   - 进入"账户设置" → "安全性"
   - 生成"应用密码"

2. **国际版操作**：
   - 登录 https://www.evernote.com
   - 进入"Account Settings" → "Security"
   - 创建"App Password"

### 步骤4：在迁移工具中输入信息
1. **邮箱地址**：输入完整的注册邮箱
2. **密码**：
   - 普通账号：使用登录密码
   - 两步验证账号：使用应用专用密码
3. **版本选择**：根据步骤1确定的版本选择

## 🔍 测试账号设置

您可以使用以下命令测试账号设置是否正确：

```bash
# 进入项目目录
cd /path/to/evernote-to-obsidian

# 运行调试脚本
python debug_evernote.py
```

## ⚠️ 常见错误示例

### ❌ 错误示例1：使用测试账号
```
账号: test@example.com
错误: Username not found!
```
**解决**: 使用真实的印象笔记注册账号

### ❌ 错误示例2：版本选择错误
```
账号: zhang@qq.com (中国用户)
版本: Evernote国际版
错误: Username not found!
```
**解决**: 改选"印象笔记中国版"

### ❌ 错误示例3：两步验证密码错误
```
账号: user@gmail.com
密码: 普通登录密码
错误: Authentication failed
```
**解决**: 生成并使用应用专用密码

## 📞 获取更多帮助

如果按照以上步骤仍无法解决：

1. 查看详细错误日志（Web界面的详细日志区域）
2. 运行 `python debug_sync_failure.py` 进行网络诊断
3. 参考 [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
4. 在GitHub提交Issue：https://github.com/vibecoddd/evernote-to-obsidian/issues

---

💡 **提示**: 如果您不确定自己使用的是哪个版本，可以先尝试中国版，如果提示账号不存在再尝试国际版。