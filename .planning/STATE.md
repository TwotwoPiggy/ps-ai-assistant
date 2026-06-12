---
milestone: v1.0
milestone_name: 多 Provider 支持
status: planning
progress:
  phases_total: 0
  phases_done: 0
  current_phase: null
  current_plan: null
---

## Current Position

Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements
Last activity: 2026-06-12 — Milestone v1.0 started

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-12)

**Core value:** 用户可以用自然语言直接控制 Photoshop，AI 自动理解意图并执行对应的 PS 操作。
**Current focus:** Defining requirements for multi-provider support

## Accumulated Context

### Decisions
- Gemini 保留 google-genai SDK，其他 provider 用 openai SDK
- 预置 provider 内置 base URL，降低配置门槛
- 只支持有 function calling 能力的模型

### Blockers
(none)

### Todos
(none)
