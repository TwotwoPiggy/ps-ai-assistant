# Phase 2: 集成预置厂商 - Context

**Gathered:** 2026-06-12
**Status:** Ready for planning

<domain>
## Phase Boundary

实现对 DeepSeek (V3/R1), 通义千问 (Qwen-VL), MiMo (小米) 和自定义 OpenAI 兼容厂商在服务端的差异化适配支持，设计并开发 DeepSeek 思考过程 (Thinking Process) 的实时提取推送机制，以及连接超时/报错时的自适应降级至 Gemini 的高可用容错机制。

</domain>

<decisions>
## Implementation Decisions

### 1. DeepSeek R1 思考过程的处理机制
- **D-01:** 后端通过正则提取（针对 `<think>` 标签）或从 API 的 `reasoning_content` 字段中提取 DeepSeek R1 的思维链思考内容。
- **D-02:** 提取的思考内容通过独立的 WebSocket 事件 `ai_chat_thinking` 实时推送至前端展示，使用户能在等待最终结果前看到模型的推理状态。
- **D-03:** 在将助手（Assistant）消息记录并持久化到 `self.conversations[sid]` 历史记录中时，必须在后端剥离思考过程（仅保留最终回复的文本及 tool_calls），防止超长的思维链内容污染下文上下文并白白消耗后续请求的 Token。

### 2. 连接容错与超时自动降级
- **D-04:** 在请求第三方提供商（如局域网 MiMo、自定义兼容端或 DeepSeek/Qwen 发生网络阻断）遇到连接超时、报错且三次重试皆失败时，系统将触发自适应降级逻辑。
- **D-05:** 若当前已配置了 Gemini 的 API Key，系统会自动临时将当前会话的底层 Provider 切换至 Gemini 运行以完成本次会话调度，并在回复前向客户端发送一条提示信息，告知用户发生了自动降级。
- **D-06:** 提供一个全局配置项 `auto_fallback_to_gemini`（默认 `True`，可在 `ai_config.json` 中配置），使用户能控制是否开启自动降级行为。

### 3. 并行工具调用 (Parallel Tool Calls)
- **D-07:** 维持对所有提供商（包括 DeepSeek, Qwen, MiMo 和 Custom）并行工具调用的支持，以最大化指令执行效率。
- **D-08:** 为防止特定兼容端对并行工具调用的支持不佳引发异常，我们在 `agent.py` 串行执行各 `tool_calls` 时必须确保工具执行的幂等性，并准确通过 `tool_call_id` 和 name 组合出 `role: tool` 的回复队列回喂给接口，保证协议层面的完全对齐。同时，在 `ai_config.json` 里可提供可选的参数以允许在未来针对某一 Provider 显式关闭并行工具调用。

### the agent's Discretion
- 超时时限的具体定义（如默认 30 秒超时）及重试策略的退避算法细节由开发人员在实现时决定。
- 提取并清理 `<think>` 时，若遇到标签未闭合的异常格式，开发人员可自主编写正则表达式的容错降级。

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Roadmap
- `.planning/ROADMAP.md` — 规定了 Phase 2 的目标为“实现对 DeepSeek, Qwen, MiMo 和自定义厂商的差异化支持及容错”
- `.planning/STATE.md` — 项目当前状态，包含 Phase 1 中所确立的 Adapter 设计及 Key 安全脱敏决策。

### Codebase Implementations
- `backend/providers/openai_compat.py` — OpenAI 兼容 Provider。
- `backend/providers/gemini.py` — Gemini 官方 SDK 接口。
- `backend/agent.py` — 协调对话循环的 PhotoshopAgent。

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/providers/registry.py` -> `get_provider(provider_name, config)`: 我们已在 Phase 1 完成了基本的工厂化 Provider 创建。在 Phase 2 中，可以在该工厂中进一步细化不同提供商的具体参数（例如 timeout、自定义 headers）。
- `backend/agent.py` -> `handle_message`: 负责对话迭代和多步工具调用的分发循环。我们将在这里扩展 `ai_chat_thinking` WebSocket 推送逻辑和自动降级回退机制。

### Established Patterns
- **标准 OpenAI 格式会话**：在 `agent.py` 里的 `self.conversations` 统一是标准的 OpenAI `dict` 列表，这对实现 D-03（剥离思考内容后存盘）提供了极佳的修改基准。
- **多端 Adapter 隔离**：各模型的特定协议处理，应当保留在各自的 Adapter 实现类中（如 `OpenAICompatProvider` 或新建特定的 `DeepSeekProvider` 继承类），避免污染 `agent.py`。

</code_context>

<specifics>
## Specific Ideas
No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas
None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-集成预置厂商*
*Context gathered: 2026-06-12*
