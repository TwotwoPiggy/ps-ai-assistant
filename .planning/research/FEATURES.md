# 多 AI 提供商 Function Calling 研究报告

> 研究日期: 2026-06-12
> 目标: 为 Photoshop AI 助手评估 DeepSeek、Qwen、MiMo 及 OpenAI 兼容提供商的函数调用能力

## 1. 当前实现分析

当前应用使用 `google-genai` SDK 与 Gemini 模型交互，核心特点：
- 通过 Python 方法引用直接注册工具（自动推断 schema）
- 使用 `types.Content` / `types.Part` 构建对话历史
- 多轮工具调用循环（最多 10 轮）
- 截图以 `Part.from_bytes(data=img_bytes, mime_type="image/jpeg")` 注入

**暴露的 11 个工具函数：**
`get_layer_tree`, `get_canvas_snapshot`, `create_layer`, `delete_layer`, `rename_layer`, `set_layer_visibility`, `reorder_layer`, `adjust_brightness_contrast`, `crop_canvas`, `resize_canvas`, `flip_image`

---

## 2. OpenAI 兼容 API 函数调用标准格式

所有目标提供商均支持 OpenAI `/v1/chat/completions` 端点的 `tools` 参数。标准格式如下：

```json
{
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_layer_tree",
        "description": "获取当前 Photoshop 文档的完整图层树结构...",
        "parameters": {
          "type": "object",
          "properties": {
            "param1": {"type": "string", "description": "..."}
          },
          "required": ["param1"]
        }
      }
    }
  ]
}
```

### 多轮工具调用协议

```
用户消息 → role: "user"
模型工具调用 → role: "assistant", tool_calls: [{id, type, function: {name, arguments}}]
工具执行结果 → role: "tool", tool_call_id: "call_xxx", content: "结果JSON字符串"
模型最终回复 → role: "assistant", content: "最终文本回复"
```

> **与 Gemini SDK 的关键差异：** OpenAI 格式使用 `role: "tool"` + `tool_call_id` 配对机制返回结果，而 Gemini 使用 `role: "user"` + `Part.from_function_response()`。迁移时需转换此消息格式。

---

## 3. 提供商详细对比

### 3.1 DeepSeek

| 维度 | 详情 |
|------|------|
| **Base URL** | `https://api.deepseek.com` |
| **SDK** | `openai` Python SDK（替换 base_url） |
| **Schema 格式** | 与 OpenAI 完全一致 |
| **支持函数调用的模型** | `deepseek-chat` (V3系列), `deepseek-reasoner` (R1) |
| **最大工具数** | 128 个函数/请求 |
| **parallel_tool_calls** | ✅ 支持 |
| **tool_choice** | `auto`, `required`, `none`, 指定函数名 |
| **Strict Mode** | ✅ Beta 可用，强制 JSON Schema 遵从 |
| **Thinking Mode 工具调用** | V3.2+ 支持，但 R1 早期版本不稳定 |

**视觉/多模态：**
- ⚠️ **DeepSeek-V3/R1 不原生支持图片输入**
- 视觉能力由独立 VLM 提供：`DeepSeek-VL2`、`Janus` 系列
- **对本项目的影响：** 需要分步工作流 — 先用 VL 模型分析截图，再将描述传给 Chat 模型做工具调用；或使用第三方 Vision Router

**DeepSeek-R1 局限性：**
- 早期版本不原生支持函数调用（主要优化推理任务）
- `<think>` 推理内容与工具调用输出的分离可能导致解析问题
- 部署环境（平台 vs 自托管）会影响工具调用能力
- 建议：优先使用 `deepseek-chat` (V3) 用于工具密集场景

### 3.2 Qwen (通义千问)

| 维度 | 详情 |
|------|------|
| **Base URL (国际)** | `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` |
| **Base URL (国内)** | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| **SDK** | `openai` Python SDK（替换 base_url） |
| **Schema 格式** | 与 OpenAI 完全一致 |
| **支持函数调用的模型** | `qwen-max`, `qwen-plus`, `qwen-turbo`, `qwen3-xxx` 系列 |
| **支持视觉+工具的模型** | `qwen3-vl-plus`, `qwen3-vl-flash`, `qwen-vl-plus` |
| **parallel_tool_calls** | ✅ 支持 |
| **tool_choice** | `auto`, `required`, `none`, 指定函数名 |
| **Thinking Mode** | Qwen3 支持 thinking/non-thinking 切换，两种模式均支持工具调用 |

**视觉/多模态 — Qwen 是本项目最佳选择之一：**
- ✅ **Qwen-VL 系列可同时支持图片输入 + 函数调用**
- 使用 OpenAI 兼容格式传递图片（`image_url` content part）
- 需设置 `result_format: "message"` 确保返回工具调用指令
- Qwen3 thinking 模式下若工具解析异常，可设置 `enable_thinking: false`

**图片输入格式：**
```json
{
  "role": "user",
  "content": [
    {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,{base64_data}"}},
    {"type": "text", "text": "分析这张画布截图"}
  ]
}
```

### 3.3 MiMo (小米)

| 维度 | 详情 |
|------|------|
| **Base URL** | `https://mimo.xiaomi.com/api` (或通过 OpenRouter) |
| **SDK** | `openai` Python SDK（替换 base_url） |
| **Schema 格式** | 与 OpenAI 完全一致 |
| **支持函数调用的模型** | `mimo-v2.5-pro`, `mimo-v2.5`, `mimo-v2-flash` |
| **最大工具数** | 128 个函数/请求 |
| **parallel_tool_calls** | ✅ 支持 |
| **tool_choice** | `auto`, `required`, `none` |
| **多模态** | ✅ V2.5 系列原生支持文本、图片、音频、视频 |
| **上下文窗口** | 最大 100 万 token (V2.5 系列) |
| **开源协议** | MIT (V2.5 系列) |

**视觉/多模态：**
- ✅ **MiMo V2.5 全模态支持 — 可同时处理图片+工具调用**
- `MiMo-V2-Omni`: 专门的多模态模型
- 输入格式兼容 OpenAI 的 `image_url` content part

---

## 4. 核心功能对比总结

| 特性 | Gemini (当前) | DeepSeek | Qwen | MiMo |
|------|--------------|----------|------|------|
| **函数调用** | ✅ 原生 | ✅ OpenAI 兼容 | ✅ OpenAI 兼容 | ✅ OpenAI 兼容 |
| **Schema 格式** | 自动推断 | OpenAI JSON Schema | OpenAI JSON Schema | OpenAI JSON Schema |
| **并行工具调用** | ✅ | ✅ | ✅ | ✅ |
| **最大工具数** | 无明确限制 | 128 | 未明确公布 | 128 |
| **tool_choice 支持** | ✅ | ✅ 全部 | ✅ 全部 | ✅ 全部 |
| **Strict Mode** | ❌ | ✅ Beta | ❌ | ❌ |
| **图片+工具同时使用** | ✅ | ❌ (需VL模型分步) | ✅ (VL模型) | ✅ (V2.5) |
| **原生图片理解** | ✅ | ⚠️ 仅VL模型 | ✅ VL系列 | ✅ V2.5系列 |
| **推荐用于本项目的模型** | gemini-2.5-flash | deepseek-chat (V3) | qwen-vl-plus / qwen-max | mimo-v2.5-pro |

---

## 5. 对本项目的实现建议

### 5.1 架构改造方向

**从 Gemini 专用 → OpenAI 兼容统一层：**

1. **统一工具 Schema 生成器** — 从 Python 方法的 docstring + type hints 自动生成 OpenAI 格式 JSON Schema（替代 Gemini 的自动推断）
2. **统一消息格式适配器** — 抽象对话历史管理，支持 Gemini 原生格式 和 OpenAI 兼容格式切换
3. **Provider 路由器** — 根据配置选择不同后端（Gemini 继续使用原生 SDK，其余走 OpenAI SDK）

### 5.2 视觉输入处理策略

| 场景 | 策略 |
|------|------|
| **Gemini** | 继续使用 `Part.from_bytes()` 注入 |
| **Qwen-VL / MiMo** | 使用 OpenAI 兼容的 `image_url` content part (base64) |
| **DeepSeek (纯文本模型)** | 方案A：降级为仅文本（不发送截图）<br>方案B：先用其他VL模型生成画面描述，再传给DeepSeek |

### 5.3 关键风险与注意事项

- **DeepSeek 视觉限制**: DeepSeek 的主力模型(V3/R1)不支持图片输入。使用 DeepSeek 时，`get_canvas_snapshot` 的截图数据无法直接发送给模型。需要实现降级策略或 VL 路由。
- **tool_call_id 匹配**: OpenAI 格式要求 `tool_call_id` 精确匹配（40字符限制）。从 Gemini 的 `function_response` 迁移时需要正确管理 ID 映射。
- **Qwen Thinking Mode**: 使用 Qwen3 模型时，若 thinking 模式导致工具调用解析失败，需在 `extra_body` 中设置 `"enable_thinking": false`。
- **推荐实现优先级**: Qwen > MiMo > DeepSeek。Qwen 的 VL 模型同时支持视觉+工具调用，最适合本项目需求。DeepSeek 作为纯文本模型的视觉限制较大。

### 5.4 配置扩展

当前 `config.py` 仅支持 `gemini_api_key` 和 `model`。需扩展为：

```python
{
    "provider": "gemini",          # gemini | deepseek | qwen | mimo | custom
    "api_key": "...",
    "model": "gemini-2.5-flash",
    "base_url": null,              # 自定义 OpenAI 兼容端点 (custom provider 必填)
    "vision_model": null,          # 可选：用于视觉处理的独立模型
    "enable_thinking": true,       # Qwen3/DeepSeek thinking mode 开关
    "max_tools_per_request": 128
}
```

---

## 6. 提供商 API 端点速查

| 提供商 | Base URL | API Key 获取 |
|--------|----------|-------------|
| **Gemini** | 使用原生 `google-genai` SDK | [Google AI Studio](https://aistudio.google.com) |
| **DeepSeek** | `https://api.deepseek.com` | [DeepSeek Platform](https://platform.deepseek.com) |
| **Qwen (国际)** | `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` | [Alibaba Cloud Model Studio](https://modelstudio.console.alibabacloud.com) |
| **Qwen (国内)** | `https://dashscope.aliyuncs.com/compatible-mode/v1` | [阿里云百炼](https://bailian.console.aliyun.com) |
| **MiMo** | `https://mimo.xiaomi.com/api` 或 OpenRouter | [MiMo Developer](https://mimo.xiaomi.com) |

---

# UXP 能力与 API 边界研究报告 (UXP Operations Research)

> 研究日期: 2026-06-13
> 目标: 探索 Photoshop UXP 架构所支持的所有可编程操作和能力范围，评估其作为当前 COM 接口（pywin32）替代或补充的可行性。

## 1. UXP 能力与 API 边界概述 (API Boundaries & Expected Behavior)
UXP (Unified Extensibility Platform) 是 Adobe 推出的现代插件架构，使用 JavaScript (V8 引擎) 运行环境，提供更安全、跨平台（Windows & macOS）的扩展能力。

- **DOM 抽象层 (Document Object Model)**：提供了对 Document（文档）、Layer（图层）、Group（图层组）的标准面向对象化操作（创建、删除、复制、属性修改）。
- **BatchPlay API (Action Manager 的桥梁)**：这是 UXP 最核心的能力边界。任何未被标准 DOM 封装的进阶操作（如复杂的滤镜、选区操作、特定的调整图层参数），都可以通过 `batchPlay` 以 JSON 描述符（Descriptors）的形式与 Photoshop 内部引擎直接通信。
- **事件监听体系 (Event Listeners)**：UXP 能够实时监听 Photoshop 内部的事件触发（如用户切换图层、修改文档名称、选中特定工具等），并予以响应。
- **沙盒文件系统 (Sandboxed File I/O)**：通过 `uxp.storage` 提供严格受控的文件读写，以及内置了原生的 `fetch` 与 WebSocket API 用于网络通信。

## 2. 功能分类评估 (Feature Categorization)

### 2.1 基础必备功能 (Table Stakes)
为了对齐当前基于 COM 接口已实现的能力，UXP 必须且能够完全胜任以下操作：
*   **图层 CRUD 操作**：利用 UXP DOM API，可以轻松实现图层的创建、重命名、隐藏/显示、顺序移动及删除。
*   **画布基础编辑**：调整画布尺寸、图像翻转与裁剪操作。
*   **基础图像调整**：增加亮度/对比度等调整图层（主要依赖 `batchPlay` 实现精确参数控制）。
*   **画布快照抓取 (Canvas Snapshot)**：通过 UXP 将当前视图或图层导出为临时图像文件（PNG/JPEG），用于输送给多模态 AI 进行视觉理解。

### 2.2 核心差异化优势 (Differentiators)
相较于当前 COM 接口方案，UXP 可以带来的独特增量价值：
*   **跨平台原生支持**：摆脱 Windows `pywin32` 的硬绑定，实现一次开发，Windows 与 macOS 均可运行。
*   **原生面板内嵌式集成**：可将当前的 React 聊天面板直接打包为 UXP 面板，与 Photoshop 的原生 UI 无缝融为一体，提升用户体验，而不再是外部的独立悬浮窗。
*   **实时上下文感知**：通过事件订阅（Event Listeners），AI 助手可以实时感知用户界面的变化，无需主动拉取即可提供上下文精准的 AI 建议。
*   **执行效率与稳定性**：异步 API (`async/await`) 和 `batchPlay` 相比外部进程的 COM 轮询，具备更快的响应速度和更低的崩溃率。

### 2.3 反模式与避坑指南 (Anti-features / Pitfalls)
*   **混用 ExtendScript (.jsx)**：极力避免在 UXP 中回调或混用旧版 ExtendScript。混合双引擎将引入严重的性能开销和极难排查的异步时序 Bug。
*   **在 UXP 端执行重型逻辑或 AI 推理**：UXP 运行时的内存和算力依然受限。不应尝试在 UXP 端本地执行模型处理。UXP 仅仅作为“前端 UI”与“执行终端”，AI 的核心编排与多 Provider 逻辑必须维持在独立运行的 Python/FastAPI 后端。
*   **越权文件系统读写**：试图绕过沙盒（Sandbox）安全策略去读写不受信的系统任意目录会导致异常，所有快照写入或临时文件管理需严格遵循 UXP 持久化 Token 规范。

## 3. 复杂度与现有功能依赖 (Complexity & Dependencies)

### 3.1 实现复杂度评估 (Complexity)
1.  **高复杂度 - `batchPlay` 描述符解析**：由于 UXP 现有的 DOM 尚未涵盖 100% 的 PS 功能，许多现有功能（如特定图像调整）必须依赖 `batchPlay`。将原有的 Python 代码翻译为晦涩的 JSON 描述符（如通过 Alchemist 插件逆向获取），是一项巨大的工程量。
2.  **中复杂度 - IPC 架构重构**：若将执行端由 Python 移至 UXP，现有的系统通信流向需要重塑。需在 UXP 插件与 FastAPI 后端之间建立持久的 WebSocket 双向通信机制。
3.  **低复杂度 - DOM 基础操作映射**：现存的大多数图层和画布 CRUD 操作能在一对一的 UXP DOM 接口中找到完美平替，转换成本极低。

### 3.2 对现有功能的依赖与影响 (Dependencies on Existing Features)
1.  **AI Provider 抽象层与配置**：现有的多 Provider 架构、安全验证、API Key 脱敏逻辑完全不受影响，依旧在后端运转。UXP 只负责调用。
2.  **聊天面板前端**：现存基于 React 的对话界面具备极高的复用性，只需将其构建目标稍作调整，即可作为 UXP 的 WebView 渲染内容。
3.  **Function Calling Schema (工具定义)**：LLM 返回的工具调用定义保持稳定，仅需将 Tool Call 的物理执行器从 `pywin32` 转移至 UXP 端对应的 JS 函数接口。后端的模型路由与思维链能力可以百分百无缝保留。
