# 🚀 印象笔记ENEX导出工具

**一键从印象笔记导出ENEX格式文件，方便与其他应用（如Obsidian）进行数据迁移！**

## ✨ 核心特性

### 🔄 全自动流程
- **自动导出**: 集成evernote-backup，自动从印象笔记导出ENEX格式数据

### 🎯 完整保留
- **📁 文件夹结构**: 完整保留原有笔记本分类
- **📝 笔记内容**: 保留格式、表格、列表、链接
- **📎 图片附件**: 自动提取并组织所有附件
- **🏷️ 元数据**: 保留标签、时间戳、作者信息

### 🛡️ 安全可靠
- **智能检测**: 自动检查并安装依赖
- **错误恢复**: 完善的错误处理机制
- **进度显示**: 实时显示导出进度
- **备份保护**: 自动创建导出目录，避免文件冲突

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

# 2. 一键导出
python3 migrate.py
```

### 🖥️ Electron 桌面客户端

桌面客户端使用 Electron、React/Vite 和本地 Python 服务；双击安装后的应用即可使用，无需手动启动浏览器或 Flask。**必须先安装并使用 Node.js >=22.12.0。** npm 的 engine 警告不足以阻止不受支持的版本继续运行；发布打包必须使用 Node 22.12+。先用 `node --version` 确认版本；在干净 checkout 中运行 `npm install`、`npm run build` 或启动 Electron 前都必须满足这一前提，再安装 Node 依赖和 Python 桌面构建依赖：

```bash
npm install
python3 -m pip install -r requirements-desktop-build.txt
```

构建 macOS `.dmg` 或 Windows NSIS 安装包：

```bash
npm run package:mac
npm run package:win
```

安装包输出到 `release/`。完整的开发、构建、签名和故障排除说明见 [ELECTRON_CLIENT.md](ELECTRON_CLIENT.md)。[MACOS_CLIENT.md](MACOS_CLIENT.md) 提供 macOS 专用的快速参考。

无论使用哪种方式，工具都会自动：
1. 🔐 引导您输入印象笔记账号
2. 📤 自动导出所有笔记为ENEX格式文件
3. 📁 自动创建导出目录，整理ENEX文件

## 🌐 Web界面特性

### ✨ 友好的用户界面
- **响应式设计**: 完美支持PC、平板、手机
- **实时进度**: WebSocket实时显示导出进度
- **直观配置**: 图形化配置向导，无需记忆参数

### 🎯 高级功能
- **配置保存**: 保存和管理多套配置方案
- **历史记录**: 查看所有导出历史和统计
- **错误处理**: 友好的错误提示和解决方案
- **深色主题**: 自动适配系统主题

## 🎛️ 使用选项

### 🧙‍♂️ 配置向导模式（推荐）
```bash
python3 migrate.py --wizard
```
交互式配置导出选项，适合首次使用

### ⚡ 快速自动模式
```bash
python3 migrate.py --auto
```
使用默认设置，快速导出ENEX文件

### 📄 使用配置文件
```bash
python3 migrate.py --config my_config.yaml
```
使用自定义配置文件进行导出

### ❓ 查看帮助
```bash
python3 migrate.py --help
```

## 🌐 Web界面使用指南

### 📱 界面导航
- **首页**: 功能概览和快速开始
- **配置**: 详细的导出配置设置
- **迁移**: 开始导出并实时监控进度
- **结果**: 查看导出历史和详细统计

### 🚀 快速开始
1. **启动应用**: `python3 web_app.py`
2. **打开浏览器**: 访问 http://localhost:5000
3. **选择导出方式**:
   - 自动导出：输入印象笔记账号，自动导出ENEX文件
4. **配置设置**: 根据需要调整导出参数（如导出目录等）
5. **开始导出**: 实时查看进度，自动完成所有步骤

### 💡 Web界面优势
- ✅ **零学习成本**: 图形化界面，点击即用
- ✅ **实时反馈**: WebSocket实时显示详细导出进度
- ✅ **配置管理**: 保存常用导出配置，一键复用
- ✅ **历史追踪**: 完整的导出历史和统计信息
- ✅ **多设备支持**: 手机、平板、电脑均可使用

## 🎯 导出流程

工具将按以下2个步骤自动执行：

### 📤 步骤1: 导出印象笔记
- 自动检测并安装evernote-backup
- 连接到印象笔记服务器
- 下载并导出所有笔记为ENEX格式

### 🔧 步骤2: 完成导出
- 清理临时文件
- 整理ENEX文件到指定目录
- 显示导出统计信息

## 📋 配置向导

首次运行时，工具会启动友好的配置向导：

```
🛠️ 配置向导
--------------------------------------------------

1. 选择印象笔记版本:
1) 印象笔记中国版 (yinxiang.com)
2) Evernote国际版 (evernote.com)
请选择 [1]:

2. 设置ENEX导出路径:
ENEX导出路径 [默认路径]:

3. 高级选项:
保留临时文件(用于调试)? [y/N]:

✅ 配置完成
```



## 🎉 导出完成后

导出成功后，您将看到：

```
🎉 导出完成！
============================================================

📊 统计信息:
 ⏱️ 总耗时: 0:05:23
 📄 总笔记数: 245
 ✅ 成功导出: 245
 📎 附件数量: 67

📁 输出位置:
 /Users/username/Documents/EvernoteExport

🚀 下一步:
 1. 查看导出的ENEX文件
 2. 使用其他工具（如Obsidian Importer）导入ENEX文件
 3. 开始您的知识管理之旅！
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
- 并行处理提高导出速度
- 内存优化处理大型文件

### 📤 如何将ENEX文件导入到Obsidian

如果您希望将导出的ENEX文件导入到Obsidian，可以使用Obsidian的Importer插件：

1. 打开Obsidian
2. 进入设置 → 社区插件 → 安装并启用 "Importer" 插件
3. 使用命令面板或功能区图标打开Importer插件
4. 在文件格式中选择 "Evernote (.enex)"
5. 选择您使用本工具导出的ENEX文件位置
6. 点击导入，等待导入完成

更多详细信息请访问：[https://help.obsidian.md/import/evernote](https://help.obsidian.md/import/evernote)

## ❓ 常见问题

### Q: 印象笔记中国版无法导出怎么办？
A: 工具自动集成evernote-backup解决方案，无需手动操作。

### Q: 导出需要多长时间？
A: 取决于笔记数量，通常每100篇笔记需要1-2分钟。

### Q: 是否支持增量更新？
A: 是的，再次运行工具只会处理新增和修改的内容。

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
  enex_export_path: "/path/to/export"  # 自定义ENEX导出路径
export:
  keep_temp_files: false               # 是否保留临时文件
```

### 批量处理
```bash
# 导出笔记
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
- [click](https://click.palletsprojects.com/) - 命令行界面
- [tqdm](https://tqdm.github.io/) - 进度条显示

---

**🎯 现在就开始您的印象笔记ENEX导出之旅吧！**

### 🌐 推荐: Web界面模式
```bash
python3 web_app.py
```
然后打开 http://localhost:5000

### 💻 经典: 命令行模式
```bash
python3 migrate.py
```
