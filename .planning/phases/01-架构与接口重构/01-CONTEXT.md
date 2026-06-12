# Phase 1 Context: 架构与接口重构

> **Domain:** 建立 BaseProvider 抽象，适配 Gemini 与通用 OpenAI 接口

## 📚 Canonical References
- ROADMAP.md
- REQUIREMENTS.md
*(No additional specs/ADRs referenced during discussion)*

## 🎯 Implementation Decisions

### 内部消息格式
- **使用 OpenAI dict 格式作为内部统一标准**。
- `PhotoshopAgent` 及整个系统的上下文中，所有消息体格式使用标准的 `{"role": "user", "content": "..."}`。
- 对于使用 Gemini 的情况，`GeminiProvider` 在真正发起请求前，将统一格式转换为 `google-genai` 的 `types.Content` 格式。

### 配置存储加密
- **暂时保持 `ai_config.json` 明文存储**。
- 在当前重构阶段，不需要引入复杂的 `keyring` 或加密库。
- 安全措施仅限于：**前端接口脱敏**（只传输前四后四位 API Key，不在网络层暴露完整密钥），这是由 CONF-02 需求涵盖的。

### 工具执行上下文
- **通过参数传递（依赖注入）**。
- 抽离到 `ps_tools.py` 的纯业务操作函数，如果需要与 WebSocket 通信，将显式地通过签名接收 `sid` 或其他上下文 Context 对象，拒绝引入可能造成并发污染的全局状态。

## 💡 Codebase Context
- **现存逻辑**：11 个 Photoshop 操作（如 `get_layer_tree`, `create_layer` 等）不依赖任何 AI SDK 的逻辑，因此非常适合提取为独立的函数。
- **配置系统**：目前存储在 `store/ai_config.json`，在扩充多 Provider 时需要保持旧版 JSON 向后兼容迁移。

## ⏭️ Deferred Ideas
- 针对 DeepSeek 的 Reasoning Tokens (`<think>`) 的前端展示已在 Roadmap 中移至 v2。
- 自动化视觉功能降级工作流已在 Roadmap 中移至 v2。
