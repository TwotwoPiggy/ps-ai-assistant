# PS AI Assistant

## What This Is

一个 Photoshop AI 助手，通过自然语言聊天界面让用户用中文描述操作意图，AI 自动调用 Photoshop COM 接口执行图层管理、画布编辑、亮度对比度调整等操作。支持多种 AI Provider，用户可在前端配置面板灵活选择和切换。

## Core Value

用户可以用自然语言直接控制 Photoshop，AI 自动理解意图并执行对应的 PS 操作。

## Current Milestone: v1.2 Photoshop 核心功能全面 UXP 迁移与重构

**Goal:** 逐步将原有的 pywin32 COM 调用接口全量替换为 UXP 通道，实现完整的跨平台 Photoshop AI 助手重构。

**Target features:**
- 全量移植图层树获取、图层 CRUD 和画布调整等现有核心操作到 UXP 接口
- 实现更加精细的多会话和客户端连接路由，确保客户端异常离线时的平滑退回与安全处理
- 全面适配 UXP 前端通信防抖，防范事件监听推送机制在 Photoshop 高频操作下产生的事件风暴
- 清理并完全移除 pywin32 COM 的硬依赖，实现与 Photoshop 本地宿主进程的彻底解耦

## Requirements

### Validated

- ✓ 用户可通过聊天界面发送自然语言指令操控 Photoshop — v0 (existing)
- ✓ AI 可获取图层树并进行图层 CRUD 操作 — v0 (existing)
- ✓ AI 可截取画布快照进行视觉理解 — v0 (existing)
- ✓ AI 可调整亮度对比度、裁剪画布、调整画布尺寸、翻转图像 — v0 (existing)
- ✓ 前端 React 聊天面板 + Socket.IO 实时通信 — v0 (existing)
- ✓ API Key 和模型名称可通过配置面板保存 — v0 (existing)
- ✓ 多 Provider 抽象层（支持 Gemini SDK 与 OpenAI SDK 双通道） — v1.0
- ✓ 预置提供商集成（DeepSeek R1 推理思维链展示、Qwen、MiMo） — v1.0
- ✓ 自定义 OpenAI 兼容 Provider（手动填入 Base URL 与模型名称） — v1.0
- ✓ 安全的双向 API Key 掩码及聚焦置空保护交互 — v1.0
- ✓ 连接异常自动向高可用 Gemini 降级及并行工具消息规范对齐 — v1.0
- ✓ 搭建 UXP 插件骨架与 manifest 网络安全权限配置 — v1.1
- ✓ 实现 UXP 前端 ModalQueue 操作串行机制与 Socket 实时长连接 — v1.1
- ✓ 实现双引擎策略/适配器抽象层及客户端在线自动动态路由路由决策 — v1.1
- ✓ 验证 11 个高频核心工具方法在 UXP DOM 与 batchPlay 的对比 PoC — v1.1
- ✓ 完成 Photoshop 操作事件反向毫秒级捕获监听及推送日志链路 — v1.1
- ✓ 制定 UXP 沙箱/防抖/并发铁律并集成至 AI Guide 配置文件 — v1.1

### Active

- [ ] 全面封装并移植 11 项图层及画布核心工具方法至 UXP 实现，并在插件端通过 ModalQueue 承载
- [ ] 优化 Socket 事件推送，在 UXP 侧引入图层和文档切换的防抖 (Debounce) 以防事件风暴
- [ ] 后端完善 Session/Client 多会话机制，隔离多端或重复连接的操作指令
- [ ] 安全移除本地 pywin32 与 COM 环境硬依赖，交付独立的跨平台 UXP + Backend 架构


### Out of Scope

- 不支持 function calling 的模型降级方案 — 所有 PS 操作强依赖 tool use，降级复杂度高
- 多 provider 同时在线/热切换对话 — v1.0 仅限单例全局配置切换使用

## Context

- 运行环境：Windows + Adobe Photoshop (COM 接口依赖，下一里程碑重构为跨平台 UXP 通道)
- SDK 策略：Gemini 走原生 `google-genai`，其他厂商通过 `AsyncOpenAI` 兼容
- 通信机制：FastAPI + Socket.IO 进行事件握手
- 已发布版本：v1.1 (UXP 插件基础底座搭建，WebSocket 双引擎指令透明路由，核心工具 API 清单及大模型铁律指南)
- 架构状态：已成功验证 UXP DOM / batchPlay 混合执行与双引擎动态回退 PoC，具备完全移除 pywin32 COM 依赖的重构前提

## Constraints

- **Platform**: Windows OS — Photoshop COM 接口 (pywin32) 硬依赖
- **Runtime**: 需要运行中的 Adobe Photoshop 实例
- **Function Calling**: 所有接入的模型必须支持 function calling / tool use
- **SDK Strategy**: Gemini 用 google-genai SDK，其他 provider 用 openai SDK

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Gemini 保留 google-genai SDK | 原生 SDK 对新模型功能更完整 | ✓ Good |
| 其他 provider 统一用 openai SDK | DeepSeek/Qwen/MiMo 均兼容 OpenAI 格式 | ✓ Good |
| 统一以 OpenAI 格式规范内部消息和 Schema | 最大化降低数据转换复杂度，Provider 自动适配 | ✓ Good |
| 双向 Key 掩码过滤设计 | 防止网络及文件存盘泄露 API Key，聚焦自动置空利于用户修改 | ✓ Good |
| 自动降级 Gemini 容错机制 | 第三方服务网络波动时，自动降级回退，保障服务高可用 | ✓ Good |
| 并行工具及图像剥离重组序列 | 对齐 OpenAI 的 Message Sequence 标准，防范 API 报错 400 | ✓ Good |
| 双引擎共存架构 (COM & UXP) | 采用策略/适配器模式解耦底层调用，实现外部 COM 接口与内部 UXP 插件双通道支持，对大模型层透明 | ✓ Good (v1.1) |
| UXP 开发 4 大铁律 (沙盒隔离/事件防抖/executeAsModal/DOM优先) | 针对 UXP runtime 核心限制的规范定义，集成于 .planning/GEMINI.md 中 | ✓ Good (v1.1) |
| 11 个核心 DOM 对应工具 Schema | 形成初始 MVP API 并以标准 JSON Schema 导出，供大模型 function calling 使用 | ✓ Good (v1.1) |

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
*Last updated: 2026-06-13 after milestone v1.2 initialization*
