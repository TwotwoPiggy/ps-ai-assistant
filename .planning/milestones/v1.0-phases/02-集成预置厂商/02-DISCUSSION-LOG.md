# Phase 2: 集成预置厂商 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-12
**Phase:** 02-集成预置厂商
**Areas discussed:** DeepSeek R1 思考过程的处理机制, 自定义与 MiMo 提供商的容错降级, 并行工具调用限制

---

## DeepSeek R1 思考过程的处理机制

| Option | Description | Selected |
|--------|-------------|----------|
| 方案 A | 后端实时提取思考内容，通过独立 WS 事件 `ai_chat_thinking` 推送，并在历史记录中剥离它，防干扰下文。 | ✓ |
| 方案 B | 作为普通文本，直接将思考内容拼接在最终回复的最前面，返回给前端。 | |
| 方案 C | 直接过滤丢弃，不向前端展现思考链。 | |

**User's choice:** 方案 A
**Notes:** 用户同意推荐的方案 A，以在前端展示实时思维链。

---

## 自定义与 MiMo 提供商的容错降级

| Option | Description | Selected |
|--------|-------------|----------|
| 方案 A | 若第三方连接超时或出错，且已配 Gemini 密钥，则自动临时切换回 Gemini 运行，并通过 WS 推送降级提示（支持配置开关控制）。 | ✓ |
| 方案 B | 直接报错中断，不作任何自动切换，让用户自行检查网络或切换提供商。 | |

**User's choice:** 方案 A
**Notes:** 用户同意推荐的方案 A，以确保局域网/不稳定第三方服务的高可用性，但要求支持开关控制。

---

## 并行工具调用限制

| Option | Description | Selected |
|--------|-------------|----------|
| 方案 A | 针对所有非 Gemini 渠道 (DeepSeek/Qwen/MiMo/Custom) 默认禁用并行工具调用，强制单步顺序调用，提高 Photoshop 稳定性。 | |
| 方案 B | 不作限制，默认允许模型发起并行工具调用。 | ✓ |

**User's choice:** 方案 B 
**Notes:** 用户明确希望在所有渠道上依然支持并行工具调用。我们在底层通过串行运行各调用、并严格确保 `tool_call_id` 协议对齐的方式来实现容错支持，同时可在配置中保留是否关闭特定 Provider 的开关。

---

## the agent's Discretion
- 网络重试超时时限的具体数值（如 30 秒超时）及避让重试退避时间。
- 对未闭合思考标签（如没有配对的 `</think>`）的正则处理容错方案。

## Deferred Ideas
(none)
