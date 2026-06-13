---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: 研究并整理uxp支持的所有操作有哪些
status: executing
last_updated: "2026-06-13T02:46:41.375Z"
last_activity: 2026-06-13 -- Phase 6 execution started
progress:
  total_phases: 3
  completed_phases: 2
  total_plans: 5
  completed_plans: 4
  percent: 80
---

## Current Position

Phase: 6 (api-research-documentation-guidelines) — EXECUTING
Plan: 1 of 1
Status: Executing Phase 6
Last activity: 2026-06-13 -- Phase 6 execution started

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-12)

**Core value:** 用户可以用自然语言直接控制 Photoshop，AI 自动理解意图并执行对应的 PS 操作。
**Current focus:** Phase 6 — api-research-documentation-guidelines

## Accumulated Context

### Decisions

- Gemini 保留 google-genai SDK，其他 provider 用 openai SDK
- 预置 provider 内置 base URL，降低配置门槛
- 只支持有 function calling 能力的模型
- 采用 Strategy + Adapter 模式拆分 Backend
- 统一使用标准 OpenAI 格式作为全系统内部的消息流与工具描述，由 Provider 自行适配底层
- 拦截 ai_config 并对密钥脱敏掩码传递 (mask)，防止抓包泄露，同时防范无改动保存覆写 Key
- 为支持 R1 思维链实时推送，对 OpenAI 兼容 Provider 启用 stream=True 异步提取并在历史记录中剥离
- 当第三方请求超时/出错时自动降级切换至 Gemini 兜底以保证系统高可用（提供开关控制）
- 串行执行各并行 tool 调用并依次收集，将所有 tool 回复消息一次性且连续地追加，截图移至最末尾以严格契合 OpenAI 消息序列协议

### Blockers

(none)

### Todos

(none)
