# 🚀 印象笔记到Obsidian一键迁移工具

**一键完成印象笔记到Obsidian的完整迁移，包括导出、转换和配置！**

## ✨ 核心特性

### 🔄 全自动流程
- **自动导出**: 集成evernote-backup，自动从印象笔记导出数据
- **智能转换**: HTML到Markdown的完美转换
- **自动配置**: 一键创建和配置Obsidian库
- **即开即用**: 迁移完成后自动启动Obsidian

### 🎯 完整保留
- **📁 文件夹结构**: 完整保留原有笔记本分类
- **📝 笔记内容**: 保留格式、表格、列表、链接
- **📎 图片附件**: 自动提取并组织所有附件
- **🏷️ 元数据**: 保留标签、时间戳、作者信息

### 🛡️ 安全可靠
- **智能检测**: 自动检查并安装依赖
- **错误恢复**: 完善的错误处理机制
- **进度显示**: 实时显示迁移进度
- **备份保护**: 自动备份现有文件

## 🚀 两种使用方式

### 🌐 Web界面模式（推荐）

```bash
# 1. 克隆项目
git clone <repository-url>
cd evernote-to-obsidian

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动Web界面
python3 web_app.py

# 或使用启动脚本（支持更多选项）
python3 start_web.py --help
```

然后在浏览器中打开 http://localhost:5000，享受友好的图形界面！

### 💨 命令行模式

```bash
# 1. 安装依赖（同上）
pip install -r requirements.txt

# 2. 一键迁移
python3 migrate.py
```

无论使用哪种方式，工具都会自动：
1. 🔐 引导您输入印象笔记账号
2. 📤 自动导出所有笔记数据
3. 🎯 智能转换为Markdown格式
4. 🏗️ 创建并配置Obsidian库
5. 🚀 自动启动Obsidian

## 🌐 Web界面特性

### ✨ 友好的用户界面
- **响应式设计**: 完美支持PC、平板、手机
- **实时进度**: WebSocket实时显示迁移进度
- **直观配置**: 图形化配置向导，无需记忆参数
- **文件上传**: 支持直接拖拽上传ENEX文件

### 🎯 高级功能
- **配置保存**: 保存和管理多套配置方案
- **历史记录**: 查看所有迁移历史和统计
- **错误处理**: 友好的错误提示和解决方案
- **深色主题**: 自动适配系统主题

## 🎛️ 使用选项

### 🧙‍♂️ 配置向导模式（推荐）
```bash
python3 migrate.py --wizard
```
交互式配置，适合首次使用

### ⚡ 快速自动模式
```bash
python3 migrate.py --auto
```
使用默认设置，快速执行

### 📄 使用配置文件
```bash
python3 migrate.py --config my_config.yaml
```
使用自定义配置文件

### ❓ 查看帮助
```bash
python3 migrate.py --help
```

## 🌐 Web界面使用指南

### 📱 界面导航
- **首页**: 功能概览和快速开始
- **配置**: 详细的迁移配置设置
- **迁移**: 开始迁移并实时监控进度
- **结果**: 查看迁移历史和详细统计

### 🚀 快速开始
1. **启动应用**: `python3 web_app.py`
2. **打开浏览器**: 访问 http://localhost:5000
3. **选择模式**:
   - 自动导出：输入印象笔记账号，自动导出并转换
   - 文件上传：直接上传已有的ENEX文件进行转换
4. **配置设置**: 根据需要调整转换参数
5. **开始迁移**: 实时查看进度，自动完成所有步骤

### 💡 Web界面优势
- ✅ **零学习成本**: 图形化界面，点击即用
- ✅ **实时反馈**: WebSocket实时显示详细进度
- ✅ **配置管理**: 保存常用配置，一键复用
- ✅ **历史追踪**: 完整的迁移历史和统计信息
- ✅ **多设备支持**: 手机、平板、电脑均可使用

## 🎯 迁移流程

工具将按以下4个步骤自动执行：

### 📤 步骤1: 导出印象笔记
- 自动检测并安装evernote-backup
- 连接到印象笔记服务器
- 下载并导出所有笔记为ENEX格式

### 📝 步骤2: 转换为Markdown
- 解析ENEX文件结构
- 转换HTML内容为Markdown
- 提取并组织图片附件
- 生成笔记索引文件

### 🏗️ 步骤3: 配置Obsidian库
- 创建Obsidian库目录结构
- 配置最佳实践设置
- 创建欢迎笔记和模板
- 推荐有用插件

### 🔧 步骤4: 完成配置
- 清理临时文件
- 自动启动Obsidian
- 显示迁移统计信息

## 📋 配置向导

首次运行时，工具会启动友好的配置向导：

```
🛠️ 配置向导
--------------------------------------------------

1. 选择印象笔记版本:
1) 印象笔记中国版 (yinxiang.com)
2) Evernote国际版 (evernote.com)
请选择 [1]:

2. 设置Obsidian库路径:
Obsidian库路径 [/Users/username/Documents/ObsidianVault]:

3. 高级选项:
完成后自动打开Obsidian? [Y/n]:
保留临时文件(用于调试)? [y/N]:

✅ 配置完成
```

## 🔧 转换后效果

### 📁 文件夹结构
```
ObsidianVault/
├── 📂 工作笔记/                # 原笔记本1
│   ├── 📄 会议记录.md
│   ├── 📄 项目计划.md
│   └── 📄 工作笔记_Index.md     # 自动生成的索引
├── 📂 学习资料/                # 原笔记本2
│   ├── 📄 读书笔记.md
│   └── 📄 学习资料_Index.md
├── 📂 attachments/             # 所有附件
│   ├── 🖼️ image1.jpg
│   └── 📎 document.pdf
├── 📂 templates/               # 笔记模板
│   └── 📄 日记模板.md
├── 📄 欢迎使用Obsidian.md       # 使用指南
└── 🔧 .obsidian/              # Obsidian配置
```

### 📄 Markdown格式
转换后的笔记包含完整元数据：

```markdown
---
title: "会议记录"
created: "2023-12-01 10:30:00"
updated: "2023-12-01 15:45:00"
tags: ["工作", "会议"]
notebook: "工作笔记"
source: "Evernote"
---

# 会议记录

## 会议议题
1. 项目进度回顾
2. 下周工作安排

## 决议事项
- [x] 完成需求文档
- [ ] 准备演示材料

![[attachments/meeting_photo.jpg]]

[相关链接](http://example.com)
```

## 🎉 迁移完成后

迁移成功后，您将看到：

```
🎉 迁移完成！
============================================================

📊 统计信息:
 ⏱️ 总耗时: 0:05:23
 📄 总笔记数: 245
 ✅ 成功转换: 243
 📎 附件数量: 67

📁 输出位置:
 /Users/username/Documents/ObsidianVault

🚀 下一步:
 1. 在Obsidian中打开您的库
 2. 浏览转换后的笔记
 3. 根据需要安装推荐插件
 4. 开始您的知识管理之旅！
```

## 💡 实用提示

### 🔐 账号安全
- 工具支持记住用户名（密码不保存）
- 支持印象笔记中国版和国际版
- 安全的本地处理，不上传任何数据

### 📱 兼容性
- ✅ Windows 10/11
- ✅ macOS 10.15+
- ✅ Linux (Ubuntu/CentOS/Debian)
- ✅ Python 3.7+

### 🚀 性能优化
- 智能增量同步避免重复处理
- 并行处理提高转换速度
- 内存优化处理大型文件

## ❓ 常见问题

### Q: 印象笔记中国版无法导出怎么办？
A: 工具自动集成evernote-backup解决方案，无需手动操作。

### Q: 转换需要多长时间？
A: 取决于笔记数量，通常每100篇笔记需要1-2分钟。

### Q: 是否支持增量更新？
A: 是的，再次运行工具只会处理新增和修改的内容。

### Q: Obsidian没有自动打开？
A: 工具会显示手动打开指南，或者可以先安装Obsidian。

## 🛠️ 高级用法

### Web界面部署

#### 本地使用
```bash
# 基础启动
python3 web_app.py

# 指定端口
python3 -c "
from web_app import WebMigrator
app = WebMigrator()
app.run(host='0.0.0.0', port=8080)
"
```

#### 生产环境部署
```bash
# 使用Gunicorn部署
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8080 web_app:app

# 使用Docker部署
# 创建Dockerfile
```

### 命令行自定义配置文件
```yaml
# custom_config.yaml
evernote_backend: "china"              # 或 "international"
output:
  obsidian_vault: "/path/to/vault"     # 自定义库路径
migration:
  auto_open_obsidian: true             # 自动打开Obsidian
  create_welcome_note: true            # 创建欢迎笔记
  keep_temp_files: false               # 是否保留临时文件
```

### 批量处理
```bash
# 处理多个ENEX文件
python3 migrate.py --config batch_config.yaml
```

## 🤝 支持与贡献

- 🐛 **问题反馈**: 请提交 GitHub Issue
- 💡 **功能建议**: 欢迎提交 Feature Request
- 🔧 **代码贡献**: 欢迎提交 Pull Request

## 📄 许可证

本项目采用MIT许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

特别感谢以下开源项目：
- [evernote-backup](https://github.com/vzhd1701/evernote-backup) - 印象笔记导出
- [html2text](https://github.com/Alir3z4/html2text) - HTML转Markdown
- [click](https://click.palletsprojects.com/) - 命令行界面
- [tqdm](https://tqdm.github.io/) - 进度条显示

---

**🎯 现在就开始您的印象笔记到Obsidian迁移之旅吧！**

### 🌐 推荐: Web界面模式
```bash
python3 web_app.py
```
然后打开 http://localhost:5000

### 💻 经典: 命令行模式
```bash
python3 migrate.py
```