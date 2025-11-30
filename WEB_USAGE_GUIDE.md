# Web界面使用指南

## 🌐 启动Web应用

```bash
# 方法1：禁用代理后启动（推荐）
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy
python web_app.py

# 方法2：直接启动（已自动处理代理问题）
python web_app.py
```

访问地址：http://localhost:5000

## 📋 使用步骤

### 1. 进入迁移页面
- 点击导航栏的"迁移"按钮
- 或直接访问：http://localhost:5000/migrate

### 2. 选择迁移模式
界面显示两个选项卡：

#### 🎯 自动导出模式（推荐）
- **功能**：自动连接印象笔记服务器导出数据
- **适用**：首次迁移或完整备份
- **按钮**：`输入账号开始迁移`（绿色"推荐"标签）

#### 📁 文件上传模式
- **功能**：上传已有的ENEX文件进行转换
- **适用**：已有ENEX文件的用户

### 3. 输入账号密码（自动模式）
选择自动模式后，会显示登录表单：

```
印象笔记账号（邮箱）: [your-email@example.com]
印象笔记密码:         [your-password]
□ 记住用户名（密码不会保存）
```

**重要说明**：
- ✅ 账号密码仅用于连接印象笔记导出数据
- ✅ 密码不会被保存或上传
- ✅ 支持印象笔记中国版和国际版
- ❌ **不支持**已启用两步验证的账号（需要应用密码）

### 4. 开始迁移
- 点击`开始导出和迁移`按钮
- 实时查看迁移进度和状态
- 完成后自动跳转到结果页面

## ⚠️ 常见问题

### Q：看不到账号密码输入框？
**A：** 需要先点击"输入账号开始迁移"按钮，选择自动导出模式

### Q：提示"Username not found"？
**A：**
1. 检查邮箱地址是否正确
2. 确认选择了正确的印象笔记版本（中国/国际）
3. 确认账号密码正确

### Q：同步失败？
**A：**
1. 临时禁用代理设置：`unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy`
2. 重启Web应用
3. 检查网络连接

### Q：两步验证账号如何处理？
**A：** 需要在印象笔记账号设置中生成应用专用密码，使用应用密码登录

## 🔧 故障排除

```bash
# 1. 重启Web应用（禁用代理）
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy
python web_app.py

# 2. 运行网络诊断
python debug_sync_failure.py

# 3. 检查详细错误信息
# 查看终端输出的完整错误日志
```

## 📞 获取帮助

如果遇到问题：
1. 查看终端输出的错误信息
2. 运行诊断工具：`python debug_sync_failure.py`
3. 参考：[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
4. GitHub Issues：https://github.com/vibecoddd/evernote-to-obsidian/issues

---

💡 **提示**：首次使用建议先用测试账号尝试，确保网络和配置正常后再迁移重要数据。