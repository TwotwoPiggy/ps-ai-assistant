# Photoshop AI Assistant

使用自然语言控制 Adobe Photoshop —— 基于 Gemini AI 的智能 PS 操作助手。

通过对话的方式，让 AI 直接操控 Photoshop，完成图层管理、画布编辑等常见操作。

## 系统要求

- **操作系统**: Windows（需要 COM 接口控制 Photoshop）
- **Python**: 3.10+
- **Adobe Photoshop**: 已安装并可运行
- **Gemini API Key**: 从 [Google AI Studio](https://aistudio.google.com/apikey) 获取

## 安装

```bash
# 克隆项目
git clone <repo-url>
cd ps-ai-assistant

# 安装 Python 依赖
pip install -r backend/requirements.txt

# (可选) 安装启动器托盘依赖 — 启用系统托盘图标
pip install -r requirements-launcher.txt
```

## 使用方法

### 一键启动 (推荐)

有两种启动方式可选：

**① `start.bat` — 带控制台窗口**：双击后显示一个 cmd 窗口实时输出日志，并在系统托盘显示图标。适合需要观察启动日志或排查问题的场景。

**② `start_silent.vbs` — 完全静默 (推荐日常使用)**：双击后**不弹出任何窗口**，只有托盘图标在后台运行。适合日常使用，桌面更清爽。

首次使用建议先安装托盘依赖（可选，缺失时自动降级为纯后台进程，但将无法通过托盘退出，需用任务管理器结束）：

```bash
pip install -r requirements-launcher.txt
```

启动参数（适用于 `start.bat`，或直接调用 `python launcher.py`）：

| 参数 | 说明 |
|------|------|
| (无) | 生产模式：仅启动后端，使用 `frontend/dist` 已构建产物 |
| `--dev` | 开发模式：同时启动后端 + Vite dev server（前端热更新） |
| `--no-tray` | 不显示托盘图标，仅命令行运行 |
| `--no-browser` | 启动后不自动打开浏览器 |
| `--port <端口>` | 指定后端端口（默认 18919；生产模式下因前端硬编码不建议改） |

示例：
```bash
start.bat --dev          REM 开发模式
start.bat --no-browser   REM 不自动开浏览器
python launcher.py --dev --no-tray
```

启动器具备以下自动化能力：
- **环境预检**：Python / Node 版本、关键依赖缺失时自动安装
- **端口检测**：18919 被占用时（开发模式）自动寻找可用端口
- **日志落盘**：所有输出写入 `logs/launcher.log`，便于排查

#### 系统托盘菜单

启动后右下角托盘会出现 PS 图标，鼠标悬停显示运行状态（`运行中 :18919` 或 `已停止`），右键菜单：

| 菜单项 | 说明 |
|--------|------|
| **打开浏览器**（双击图标亦可） | 用默认浏览器打开应用页面 |
| **停止服务 / 启动服务** | 动态切换：运行时显示「停止服务」，停止后显示「启动服务」，便于临时释放端口或暂停 |
| **重启服务** | 停止后重新拉起，用于应用配置变更后生效 |
| **查看日志** | 用记事本打开 `logs/launcher.log` |
| **退出** | 停止所有子进程并退出启动器 |

> 注意：生产模式下端口固定为 18919（前端 `socket.ts` 硬编码），切换端口会导致前端连不上后端。

---

### 命令行启动 (手动)

如不想使用启动器，也可以直接运行：

```bash
python -m backend.server
```

服务器默认运行在 `http://localhost:18919`。

### 配置 API Key

有两种方式配置 Gemini API Key：

1. **环境变量**（推荐）:
   ```bash
   set GEMINI_API_KEY=your-api-key-here
   python -m backend.server
   ```

2. **前端配置面板**: 启动服务器后，在前端 UI 的设置面板中输入并保存 API Key。

### 使用 AI 助手

启动服务器并配置好 API Key 后，通过前端聊天界面发送自然语言指令即可。例如：

- "帮我新建一个叫'背景'的图层"
- "把第一个图层隐藏"
- "把画面亮度调高一点"
- "裁剪掉画布右边 100 像素"
- "水平翻转整个画面"

## 支持的操作

| 操作 | 说明 |
|------|------|
| 获取图层树 | 查看当前文档的完整图层结构 |
| 获取画布快照 | 截取当前画面用于视觉分析 |
| 创建图层 | 新建普通图层，可指定名称、透明度和位置 |
| 删除图层 | 删除指定图层 |
| 重命名图层 | 修改图层名称 |
| 图层可见性 | 显示或隐藏指定图层 |
| 图层排序 | 调整图层在面板中的上下位置 |
| 亮度/对比度 | 调整图层的亮度和对比度 |
| 裁剪画布 | 按像素坐标裁剪画布 |
| 调整画布大小 | 更改画布尺寸 |
| 翻转画布 | 水平或垂直翻转整个文档 |

## 项目结构

```
ps-ai-assistant/
├── backend/
│   ├── __init__.py          # 包入口
│   ├── agent.py             # Photoshop AI Agent (Gemini + COM 工具)
│   ├── config.py            # API Key 配置管理
│   ├── server.py            # FastAPI + Socket.IO 服务器
│   ├── requirements.txt     # Python 依赖
│   └── store/               # 运行时配置存储 (gitignored)
├── frontend/                # 前端 UI (React + Vite)
├── launcher.py              # 服务启动器 (环境检查/托盘/双模式)
├── start.bat                # Windows 启动入口 (带控制台窗口)
├── start_silent.vbs         # Windows 静默启动入口 (无窗口, 仅托盘)
├── requirements-launcher.txt # 启动器可选依赖 (托盘图标)
├── logs/                    # 启动器日志 (gitignored)
├── .gitignore
└── README.md
```

## 技术栈

- **AI 模型**: Google Gemini 2.5 Flash (Function Calling)
- **后端**: FastAPI + python-socketio + uvicorn
- **PS 控制**: pywin32 COM 接口
- **通信协议**: Socket.IO (WebSocket)

## License

MIT
