# 多供应商 AI 后端 — SDK 与依赖研究

> 研究日期：2026-06-12
> 目标：为 Photoshop AI 助手添加 DeepSeek、Qwen (DashScope)、MiMo (Xiaomi) 及自定义 OpenAI 兼容供应商的支持

---

## 1. 现有项目状况

### 当前依赖 (`backend/requirements.txt`)
```
google-genai>=1.0.0
pywin32
python-socketio[asgi]
fastapi
uvicorn[standard]
```

### 当前架构
- **SDK**: `google-genai` (Gemini 原生 SDK)
- **Agent**: `PhotoshopAgent` 类 (`backend/agent.py`, 508 行)
- **配置**: `backend/config.py` — 仅存储 `gemini_api_key` 和 `model`
- **工具定义方式**: 直接传递 Python 方法引用（Gemini 原生自动推断 schema）
- **对话历史**: 使用 `google.genai.types.Content` / `types.Part` 类型

---

## 2. 需新增的依赖

### 核心新增

| 包名 | 版本 | 用途 |
|------|------|------|
| `openai` | `>=2.41.1` (当前最新，2026-06-10 发布) | DeepSeek / Qwen / MiMo / 自定义供应商的统一 SDK |

### 可选（不推荐）

| 包名 | 说明 | 推荐？ |
|------|------|--------|
| `dashscope` | 阿里云 DashScope 原生 SDK | ❌ 不推荐。OpenAI 兼容模式已覆盖所有需要的功能 |
| `deepseek` (PyPI) | 社区非官方包 | ❌ 不推荐。DeepSeek 官方无独立 SDK |
| `mimo-tui` | 社区 MiMo TUI 工具 | ❌ 无关。小米无官方 Python SDK |

**结论：只需新增 `openai>=2.41.1` 一个依赖即可覆盖所有非 Gemini 供应商。**

---

## 3. 各供应商详细信息

### 3.1 DeepSeek

| 配置项 | 值 |
|--------|-----|
| **Base URL** | `https://api.deepseek.com` |
| **API Key 环境变量** | `DEEPSEEK_API_KEY` |
| **推荐模型** | `deepseek-chat` (V3系列) |
| **Function Calling** | ✅ 完全支持 OpenAI 兼容格式 |
| **并行工具调用** | ✅ 支持（最多 128 个函数） |
| **官方独立 SDK** | ❌ 无。官方推荐使用 `openai` SDK |

**初始化代码**：
```python
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)
```

**已知怪癖**：
1. **`tool_choice`**: 建议在确定性 Agent 循环中使用 `"required"` 而非 `"auto"`
2. **Schema 漂移**: 长对话 (15-30+ 轮) 中模型可能幻觉参数
3. **思维模式交互**: 启用 Thinking Mode 时，模型会在 tool call 前生成 `<think>` 块
4. **速率限制**: 遇到 429 需实现指数退避

---

### 3.2 Qwen / DashScope (阿里通义千问)

| 配置项 | 值 |
|--------|-----|
| **Base URL (国际)** | `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` |
| **Base URL (国内)** | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| **API Key 环境变量** | `DASHSCOPE_API_KEY` |
| **推荐模型** | `qwen-max`, `qwen-plus`, `qwen-vl-plus` |
| **Function Calling** | ✅ 全面支持 |
| **官方独立 SDK** | `dashscope` (有，但不推荐) |

**初始化代码**：
```python
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)
```

**已知怪癖**：
1. **`tool_choice="required"` 限制**: 思维模型启用时可能触发 `400 Bad Request`
2. **缺少 `/responses` 端点**: 只支持 `/chat/completions`
3. **流式解析**: `tool_calls` 的 `arguments` 可能跨多个 chunk 分段传输

---

### 3.3 MiMo (小米)

| 配置项 | 值 |
|--------|-----|
| **Base URL** | `https://api.xiaomimimo.com/v1` |
| **API Key 环境变量** | `MIMO_API_KEY` |
| **推荐模型** | `mimo-v2.5-pro`, `mimo-v2-flash` |
| **Function Calling** | ✅ 支持（V2.5-Pro 及以上） |
| **官方独立 SDK** | ❌ 无 |

**初始化代码**：
```python
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("MIMO_API_KEY"),
    base_url="https://api.xiaomimimo.com/v1"
)
```

**已知怪癖**：
1. 某些 Agent 框架无法正确解析 MiMo 的 tool-call 格式
2. 模型不确定时可能陷入 thinking loop
3. Schema 校验比标准 OpenAI 端点更严格

---

## 4. OpenAI SDK 工具调用核心 API

### 4.1 与 Gemini SDK 的关键差异

| 维度 | Gemini (`google-genai`) | OpenAI (`openai`) |
|------|------------------------|-------------------|
| **工具定义** | 直接传递 Python 函数引用 | 必须手动构建 JSON Schema |
| **对话类型** | `types.Content` / `types.Part` | 标准 `dict` |
| **函数结果角色** | `role="user"` + `Part.from_function_response()` | `role="tool"` + `tool_call_id` |
| **图片传递** | `Part.from_bytes(data, mime_type)` | Base64 内嵌 `image_url` |

---

## 5. 需要修改的 `requirements.txt`

```
google-genai>=1.0.0
openai>=2.41.1
pywin32
python-socketio[asgi]
fastapi
uvicorn[standard]
```

仅新增一行 `openai>=2.41.1`。

---

## 6. 架构影响摘要

### 建议架构模式

```
PhotoshopAgent (统一接口)
├── GeminiProvider (google-genai SDK)
│   └── 保持现有逻辑，使用函数引用自动推断
├── OpenAICompatibleProvider (openai SDK)
│   ├── DeepSeek
│   ├── Qwen/DashScope
│   ├── MiMo
│   └── Custom
│       └── 统一使用 JSON Schema 工具定义 + dict 消息格式
└── 共享工具注册表 (统一 tool 定义，双格式输出)
```

## 7. 风险与注意事项

| 风险 | 严重程度 | 缓解策略 |
|------|---------|---------|
| MiMo tool calling 不稳定 | 🟡 中 | 实施严格 token 上限 + max_turns 限制 |
| Qwen `tool_choice="required"` 不兼容 | 🟡 中 | 按供应商条件化设置 |
| DeepSeek 长对话 schema 漂移 | 🟡 中 | 服务端 schema 校验 + 错误回传 |
| 各供应商 multimodal 格式差异 | 🟠 中高 | 验证每个供应商的 vision 图片传递 |
