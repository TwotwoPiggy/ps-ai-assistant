# Phase 2 Plan: 集成预置厂商

**Phase Goal:** 实现对 DeepSeek, Qwen, MiMo 和自定义厂商的差异化支持及容错
**Status:** Complete

## 1. 现状分析与实现思路

在 Phase 1 中，我们成功建立起了 `BaseProvider` 与适配器架构。在本阶段（Phase 2），我们将侧重于预置服务商的高级支持与容错能力。
核心实现涉及三大机制：
1. **R1 推理思维链流式提取**：利用 `AsyncOpenAI` 的流式客户端解析 `delta.reasoning_content`，实时推送给前端。同时在存入物理历史时剥离它以防消耗后续请求的 token 资源。
2. **连接超时与高可用降级**：捕获任何连接故障与网络报错，在三次重试失败后判定提供商离线，自动无缝回退至 Gemini 续接对话。
3. **并行工具对齐规范**：为了让第三方兼容端在发起并行工具调用时完全稳定运行，我们规范化 `agent.py` 的消息队列写入顺序，保证并行产生的多条 `role: tool` 回复消息连续、不被打断地追加进会话。

---

## 2. 详细技术方案

### 2.1 Provider 抽象与流式提取 (`backend/providers/`)
1. 修改 `BaseProvider` (`backend/providers/base.py`)：
   - [ ] 调整 `chat` 签名，添加可选的 `on_thinking_callback` 用于思维链推送。
2. 修改 `OpenAICompatProvider` (`backend/providers/openai_compat.py`)：
   - [ ] 重构 `chat()` 函数为 `stream=True` 流式响应模式。
   - [ ] 流式读取 chunk，若是 `delta.reasoning_content` 则异步触发 `on_thinking_callback(chunk)`。
   - [ ] 流式拼接 `delta.content` 并捕获 `delta.tool_calls` 各索引的分片，在流结束后反序列化。

### 2.2 Orchestrator 核心循环增强 (`backend/agent.py`)
1. 重构 `handle_message`：
   - [ ] 在调用 `provider.chat` 时传入思维链回调。该回调将推理词组装并通过 status 渠道往外发送。
   - [ ] 异常防护：对 `chat` 调用加外层捕获，若报错（如 Timeout / 503 等），判断 `auto_fallback_to_gemini` 是否开启且满足回退条件，动态降级至 `GeminiProvider`。
   - [ ] 并行工具历史序列校准：
     - [ ] 收集并行产生的各 tool_call_id 的回复，通过 `extend` 一次性连续写入。
     - [ ] 收集的所有 canvas 截图 base64 被合成一个独立的 `user` 角色消息，整体追加在工具消息队列之后。

### 2.3 API 与通信事件分发 (`backend/server.py`)
1. 增强 Socket 消息分发：
   - [ ] 当 `server.py` 的 `status_callback` 接收到类型为 `thinking` 且带有字词的事件时，通过 socket 发送专有事件 `ai_chat_thinking`。

---

## 3. 验证计划 (Verification)
1. **思维链测试**：启动后端，向 DeepSeek-R1 提问“你如何帮我用 Photoshop 做一个高光圆角阴影按钮？”观察控制台日志是否能在接收到正文前，捕获到流式传输的 `reasoning_content`。
2. **降级测试**：在配置文件中故意填写错误的 DeepSeek API Key 或错误的 Base URL，发送聊天，验证后台是否能捕获异常，并在 3 次重试失败后自动、无缝切换到 Gemini 顺畅完成图层调用。同时查看前端是否收到了包含降级说明的回复。
3. **并行稳定性测试**：让支持并行工具的模型一次性获取图层树并抓取画布截图（即并行触发 `get_layer_tree` 和 `get_canvas_snapshot`），校验 `self.conversations` 中的最终消息队列，保证所有的 `role: tool` 消息都是连续被添加，没有任何其他非 tool 消息穿插其间。

---

## 4. 执行步骤分解
- [ ] **Step 1**: 调整 `BaseProvider` 并重构 `OpenAICompatProvider` 的 `stream=True` 流式响应与思维链提取逻辑。
- [ ] **Step 2**: 增强 `PhotoshopAgent` 的异常捕获与自动回退降级到 Gemini 运行机制。
- [ ] **Step 3**: 校准 `PhotoshopAgent` 的并行工具返回消息的队列顺序，确保 OpenAI 格式合规。
- [ ] **Step 4**: 修改 `server.py` 以向前端实时抛出 `ai_chat_thinking` 思考链事件。
