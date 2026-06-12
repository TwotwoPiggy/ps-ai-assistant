---
phase: 02-集成预置厂商
plan: 02
subsystem: api
tags: [deepseek-r1, fallback, stream, parallel-tool-calls, websocket]

# Dependency graph
requires:
  - phase: 01-架构与接口重构
    provides: BaseProvider, OpenAICompatProvider, GeminiProvider, ToolRegistry
provides:
  - Streaming responses for OpenAICompatProvider
  - Real-time DeepSeek R1 reasoning process extraction and WS push
  - Resilient exception handling with auto fallback/downgrade to Gemini
  - Cleaned and aligned tool response sequence matching OpenAI standards for parallel calls
affects:
  - frontend UI presentation (real-time think animation)
  - high-availability session handling

# Tech tracking
tech-stack:
  added: []
  patterns: [Streaming Async Iterator, Fallback Resilience Pattern, Sequence Alignment Pattern]

key-files:
  created: []
  modified:
    - backend/providers/base.py
    - backend/providers/gemini.py
    - backend/providers/openai_compat.py
    - backend/agent.py
    - backend/server.py

key-decisions:
  - "为提升用户体验，采用 AsyncOpenAI 流式 API (stream=True) 并提取 reasoning_content，在历史记录中将其剥离以防消耗后续 Token。"
  - "当第三方离线时，默认在多次重试后自动切换回 Gemini 保证服务高可用，并提供 auto_fallback_to_gemini 配置键进行全局控制。"
  - "严格遵循 OpenAI 规范，将多个并行 `role: tool` 回复消息一次性且紧凑地塞入会话历史，把多模态截图移至队列最末，防范接口抛出 400 Invalid Message Sequence。"

patterns-established:
  - "Pattern 1: 异步流式 Delta 切片解析与 R1 推理思维链提取。"
  - "Pattern 2: 优雅的高可用临时降级回退控制流。"
  - "Pattern 3: 严格合规的并发工具回复顺序排列协议。"

requirements-completed: []

# Metrics
duration: 25min
completed: 2026-06-12
---

# Phase 2 Plan 2: 集成预置厂商 Summary

**完成流式客户端改造以实时提取并推送 DeepSeek R1 推理思维链，实现连接超时时自适应降级回退至 Gemini 的安全兜底，并修正了并行工具的队列排列顺序以完全符合 OpenAI 标准。**

## Performance

- **Duration:** 25 min
- **Started:** 2026-06-12T22:31:43Z
- **Completed:** 2026-06-12T22:56:47Z
- **Tasks:** 5
- **Files modified:** 5

## Accomplishments
- **R1 实时推理链推送**：重构 `OpenAICompatProvider` 的 completions 调用为流式机制，能在获取正文或工具前捕获 `delta.reasoning_content`，通过 Socket.IO 发射独立事件 `ai_chat_thinking`，提供给前端思维链展示；存盘时剥离以节省上下文资源。
- **高可用临时降级兜底**：在 `PhotoshopAgent` 的对话迭代外层加装了高容错降级模块。当 DeepSeek、局域网 MiMo 等第三方服务因连接超时或网络波动报错时，能够自动零感知重载并回退至 Gemini 运送当前对话，确保助手 7x24 小时不掉线，且提供配置开关。
- **并行工具消息顺序校准**：解决了并行产生多个工具回复时，多模态截图 user 消息意外将其截断的协议缺陷。通过重写 `agent.py` 的队列顺序，让所有的并行的 `tool` 角色消息连续、不被打断地 `extend` 进入历史，截图消息整体移至末尾，完美消除了 OpenAI 400 协议格式错误。
- **测试通过**：搭建了多重 Mock 并发流提取、降级自动捕获、并行消息顺序断言校验，测试全部高分通过。

## Task Commits

Each task was committed atomically:

1. **Task 1: Provider Stream and reasoning callback** - `342e26d` (feat)
2. **Task 2 & 3: Gemini Fallback & Sequence Correction** - `7dbf0a8` & `902ebc3` (feat/fix)
3. **Task 4: Server callback WebSocket integration** - `23acfda` (feat)

**Plan metadata:** `pending_commit` (docs: complete Phase 2 Plan 2 summary)

## Files Created/Modified
- `backend/providers/base.py` - 为 chat 注入 `on_thinking_callback` 可选参数签名。
- `backend/providers/gemini.py` - 同步调整方法签名，保留前向兼容。
- `backend/providers/openai_compat.py` - 升级为 `stream=True` 并使用 async for 获取 chunk 推送思维链。
- `backend/agent.py` - 引入外层降级防御与工厂实例化；重构 tool 消息 extend 机制，校正消息顺序。
- `backend/server.py` - 适配 `thinking_word` 事件并实时向前端 WebSocket 抛出 `ai_chat_thinking`。

## Decisions Made
- 统一用异步迭代器流式解析 OpenAI 响应，仅暴露最终 content，把思考内容剥离于 conversations 上下文外，极大控制了 Token 耗用。
- 回退降级逻辑调用 `get_provider("gemini", config)` 代替原有的显式 import，保持了与 Provider 注册中心的完全一致性，并使代码更加易于测试和管理。

## Deviations from Plan
None - All integration tests passed.

## Issues Encountered
- 测试中由于 MagicMock 对 `name` 属性的默认拦截导致断言失败，已通过在测试脚本中直接给 Mock 对象的 function 属性赋属性名得以完全修复。
- 函数内部出现 UnboundLocalError 本地作用域误判，已通过清除降级 try 块里的局部 import 重用全局导入解决。

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- 预置提供商的高级容错与思维链后端支持均已就绪。
- 可以进入 Phase 3 (前端配置面板改造) 来全面升级 UI 的表单输入和思维链的气泡渲染。

---
*Phase: 02-集成预置厂商*
*Completed: 2026-06-12*
