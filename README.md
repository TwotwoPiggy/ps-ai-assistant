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
```

## 使用方法

### 启动服务器

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
├── frontend/                # 前端 UI (待开发)
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
