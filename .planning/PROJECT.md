# PS AI Assistant

## What This Is

一个 Photoshop AI 助手，通过自然语言聊天界面让用户用中文描述操作意图，AI 自动调用 Photoshop COM 接口执行图层管理、画布编辑、亮度对比度调整等操作。支持多种 AI Provider，用户可在前端配置面板灵活选择和切换。

## Core Value

用户可以用自然语言直接控制 Photoshop，AI 自动理解意图并执行对应的 PS 操作。

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

- ✓ 用户可通过聊天界面发送自然语言指令操控 Photoshop — v0 (existing)
- ✓ AI 可获取图层树并进行图层 CRUD 操作 — v0 (existing)
- ✓ AI 可截取画布快照进行视觉理解 — v0 (existing)
- ✓ AI 可调整亮度对比度、裁剪画布、调整画布尺寸、翻转图像 — v0 (existing)
- ✓ 前端 React 聊天面板 + Socket.IO 实时通信 — v0 (existing)
- ✓ API Key 和模型名称可通过配置面板保存 — v0 (existing)

### Active

<!-- Current scope. Building toward these. -->

- [ ] Provider 抽象层：统一接口适配 Gemini (google-genai) 和 OpenAI 兼容 provider
- [ ] 预置 Provider：Gemini、DeepSeek、Qwen、MiMo，各自内置 base URL
- [ ] 自定义 OpenAI 兼容 Provider：用户可填入任意 base URL + API Key + 模型名
- [ ] 前端配置面板改造：Provider 选择、API Key、base URL、模型名称
- [ ] Function Calling 兼容：统一 tool 定义格式，适配不同 provider 的 function calling 实现

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- 不支持 function calling 的模型降级方案 — 当前所有 PS 操作依赖 function calling，降级方案复杂度高
- 多 provider 同时在线/热切换 — v1 只需在配置面板选择一个 provider 使用
- Provider 特有高级功能（如 Gemini 的 grounding、DeepSeek 的 reasoning tokens 展示）— 统一接口层不承载差异化功能

## Context

- 现有后端完全绑定 `google-genai` SDK，PhotoshopAgent 类中 tool 定义为 Python 方法，由 Gemini 自动推断 schema
- 其他 provider 使用 OpenAI SDK，tool 定义需要显式 JSON schema 格式
- 所有 provider 都通过 `/v1/chat/completions` 端点通信（Gemini 除外，保留原生 SDK）
- 前端配置面板目前只有 API Key 和模型名两个字段
- 运行环境：Windows + Adobe Photoshop（COM 接口硬依赖）

## Constraints

- **Platform**: Windows OS — Photoshop COM 接口 (pywin32) 硬依赖
- **Runtime**: 需要运行中的 Adobe Photoshop 实例
- **Function Calling**: 所有接入的模型必须支持 function calling / tool use
- **SDK Strategy**: Gemini 用 google-genai SDK，其他 provider 用 openai SDK

## Key Decisions

<!-- Decisions that constrain future work. Add throughout project lifecycle. -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Gemini 保留 google-genai SDK | 已有稳定实现，原生 SDK 功能更完整 | — Pending |
| 其他 provider 统一用 openai SDK | DeepSeek/Qwen/MiMo 均兼容 OpenAI API 格式，一个 SDK 覆盖所有 | — Pending |
| 预置 provider 内置 base URL | 降低用户配置门槛，只需填 API Key | — Pending |
| 只支持有 function calling 能力的模型 | PS 操作完全依赖 tool use，无降级方案 | — Pending |

## Current Milestone: v1.0 多 Provider 支持

**Goal:** 让 PS AI Assistant 支持多个 AI Provider（Gemini、DeepSeek、Qwen、MiMo 及自定义 OpenAI 兼容），用户可在前端配置面板选择和切换。

**Target features:**
- Provider 抽象层
- 预置 Provider 接入（Gemini、DeepSeek、Qwen、MiMo）
- 自定义 OpenAI 兼容 Provider
- 前端配置面板改造
- Function Calling 兼容性统一

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-12 after milestone v1.0 initialization*
