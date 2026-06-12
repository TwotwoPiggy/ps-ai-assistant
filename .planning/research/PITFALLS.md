# 多供应商 AI 集成风险与陷阱清单

> 针对 ps-ai-assistant 项目：从 Gemini 单供应商扩展到 DeepSeek / Qwen / MiMo / 自定义 OpenAI 兼容供应商

## 📊 风险优先级说明

- 🔴 **P0 — 阻断性**：不处理将导致功能完全不可用
- 🟠 **P1 — 严重**：会导致关键功能不稳定或安全隐患
- 🟡 **P2 — 中等**：影响用户体验或增加维护成本
- 🟢 **P3 — 低优**：值得注意但不紧急

---

## 🔴 P0 — 阻断性风险

### 1. Function Calling 格式不兼容

**问题描述：**
当前项目重度依赖 Gemini 的原生 function calling。Gemini 使用自有的 SDK 格式定义工具（直接传入 Python 函数引用），而 OpenAI 兼容供应商需要手动编写 JSON Schema 定义。

**具体差异：**
- **Gemini**：直接传入 Python 函数引用，SDK 自动推断 schema
- **OpenAI 兼容**：需要 `type: "function"`, `function: {name, description, parameters}` JSON Schema
- **tool_choice 行为**：Gemini 使用 `tool_config`，OpenAI 兼容使用 `tool_choice`
- **parallel tool calls**：各供应商可靠性不同

**预防策略：**
- 建立统一的工具定义源（一份 Python 函数 + docstring），分别生成双格式
- 为每个供应商建立独立的工具调用解析逻辑
- 编写工具调用结果的回传格式转换

### 2. 对话历史格式完全不同

**问题描述：**
当前使用 `types.Content(role="user", parts=[...])` 管理对话历史。OpenAI 兼容 API 使用字典列表。两套格式不可互换。

**具体影响点：**
- `agent.py:15` — `self.conversations` 存储 `list[types.Content]`
- `agent.py:330-349` — 历史清理逻辑操作 `part.function_response`
- `agent.py:352-355` — 使用 `types.Content` 构建用户消息
- `agent.py:483-486` — 使用 `Part.from_function_response` 构建工具响应
- `agent.py:493-495` — 使用 `Part.from_bytes` 注入图像

**预防策略：**
- 定义内部统一的消息格式，适配器负责 from/to 转换
- 对话历史管理逻辑操作内部格式，而非供应商 SDK 对象

### 3. 多模态（图像）输入方式差异

**问题描述：**
Gemini 使用 `Part.from_bytes(data, mime_type)`，OpenAI 兼容使用 `image_url` content part。DeepSeek 纯文本模型不支持视觉输入。

**预防策略：**
- 为每个供应商配置 `supports_vision: bool` 标志
- 不支持视觉的供应商跳过图像注入，改为纯文本元数据
- 抽象 `inject_image()` 方法

---

## 🟠 P1 — 严重风险

### 4. Thinking/Reasoning 模式与 Tool Calling 冲突

**问题描述：**
DeepSeek 和 Qwen 的"思考模式"与 tool calling 存在已知冲突。模型可能在 `<think>` 块内发出工具调用标签，导致解析失败。

**预防策略：**
- PS 助手场景建议默认禁用 thinking mode
- 如启用，必须在对话边界清理 `reasoning_content`
- 解析时明确处理 `reasoning_content` 字段

### 5. API Key 存储安全

**问题描述：**
当前明文存储 API Key。多供应商后风险面扩大。server.py 将完整 API Key 返回前端。

**预防策略：**
- 保持 `.gitignore` 覆盖
- API Key 返回前端时做脱敏处理（只显示前4后4位）
- 每个供应商 key 使用独立字段名

### 6. 上下文窗口差异导致对话崩溃

**问题描述：**
| 供应商 | 上下文窗口 | 输出限制 |
|--------|-----------|---------|
| Gemini 2.5 Flash | 1M tokens | 65K tokens |
| DeepSeek V3 | ~128K tokens | ~16K tokens |
| Qwen 3 | 256K–1M | ~8K-32K tokens |
| MiMo | ~128K-256K | ~8K-16K tokens |

同一段对话历史在 Gemini 下正常，切换到 MiMo 后可能超限。

**预防策略：**
- 为每个供应商配置 `max_context_tokens`
- 实现基于 token 计数的历史截断
- 对小窗口模型降低截图质量

### 7. 错误处理与重试逻辑差异

**问题描述：**
当前仅处理 `google.genai.errors.APIError` 的 429/503。各供应商错误行为差异大。

**预防策略：**
- 每个适配器实现自己的 `call_with_retry()` 方法
- 使用指数退避 + 随机抖动
- 区分可重试和不可重试错误

---

## 🟡 P2 — 中等风险

### 8. "最低公约数"陷阱

**问题描述：**
过度统一的接口会丢失各供应商独特能力。

**预防策略：**
- 采用"薄适配器"模式，允许供应商特定参数透传
- 保持 Gemini 使用原生 SDK

### 9. System Prompt 行为差异

**问题描述：**
当前 system prompt 针对 Gemini 优化。不同模型对工具使用指令的遵从度不同。

**预防策略：**
- 允许为每个供应商配置 system prompt 后缀
- 对 DeepSeek/Qwen 添加明确的工具使用授权提示

### 10. 双 SDK 依赖管理

**问题描述：**
同时依赖 `google-genai` 和 `openai`，可能产生依赖冲突。

**预防策略：**
- 锁定版本，使用虚拟环境
- 延迟导入，避免交叉影响

---

## 🟢 P3 — 低优先级

### 11. 测试策略挑战

使用 `unittest.mock` 模拟 API 响应测试适配器格式转换逻辑。可用 Ollama 运行小模型进行本地测试。

### 12. 配置 UI 复杂度

从"一个 API Key"变为"多供应商 × 多配置项"。设计分层配置界面，提供合理默认值。

---

## 🎯 推荐实施顺序

1. **先设计内部消息格式**（解决 P0-#2）
2. **建立适配器接口**（解决 P0-#1, P2-#8）
3. **实现 Gemini 适配器**（重构现有代码到新接口）
4. **实现 OpenAI 兼容适配器**（DeepSeek/Qwen 共用）
5. **处理多模态差异**（P0-#3）
6. **添加上下文窗口管理**（P1-#6）
7. **强化安全和错误处理**（P1-#5, P1-#7）
8. **供应商特定优化**（P1-#4, P2-#9）
