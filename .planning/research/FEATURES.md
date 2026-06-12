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
