---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: 多 Provider 支持
status: Ready to build
last_updated: "2026-06-12T14:13:09.625Z"
last_activity: 2026-06-12 — Roadmap approved
---

## Current Position

Phase: 1 (架构与接口重构)
Plan: —
Status: Ready to plan
Last activity: 2026-06-12 — Phase 1 context gathered

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-12)

**Core value:** 用户可以用自然语言直接控制 Photoshop，AI 自动理解意图并执行对应的 PS 操作。
**Current focus:** Roadmap completed, ready to start Phase 1.

## Accumulated Context

### Decisions

- Gemini 保留 google-genai SDK，其他 provider 用 openai SDK
- 预置 provider 内置 base URL，降低配置门槛
- 只支持有 function calling 能力的模型
- 采用 Strategy + Adapter 模式拆分 Backend

### Blockers

(none)

### Todos

(none)
