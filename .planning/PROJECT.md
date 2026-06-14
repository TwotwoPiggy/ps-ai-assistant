# PS AI Assistant

## What This Is

一个 Photoshop AI 助手，通过自然语言聊天界面让用户用中文描述操作意图，AI 自动调用 Photoshop COM 接口执行图层管理、画布编辑、亮度对比度调整等操作。支持多种 AI Provider，用户可在前端配置面板灵活选择和切换。具备极高的底层稳定性和丰富的操作能力。

## Core Value

用户可以用自然语言直接控制 Photoshop，AI 自动理解意图并执行对应的 PS 操作，且过程不依赖易中断的环境，具有生产级的高可用性。

## Current Milestone: v1.3 COM 接口高级能力实现

**Goal:** 基于 `COM-CAPABILITIES-REFERENCE.md`，全面实现 3、4、5、6 四大核心能力模块的接入，使 AI 助手掌握高级修图与工作流自动化能力。

**Target features:**
- 3. 选区与蒙版 (Selection & Mask)
- 4. 专业调色与光影 (Color Correction)
- 5. 高级滤镜与人像美化 (Filters & Retouching)
- 6. 自动化与动作集成 (Automation & Actions)

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
- ✓ UXP 方案废弃前探索：完成了 UXP manifest 网络安全权限配置、ModalQueue 操作串行机制以及双引擎策略/适配器抽象层 — v1.1 (Abandon)
- ✓ 实现文档管理 7 项核心 API (create_document, open_and_place, save_document, resize_image, change_color_mode, history_control, zoom_view) — v1.2
- ✓ 实现图层进阶操作 8 项核心 API (group_layers, set_layer_opacity_and_fill, set_layer_blend_mode, translate_layer, merge_layers, duplicate_layer, rasterize_layer, convert_to_smart_object) — v1.2
- ✓ 在 ps_tools 中引入 execute_jsx() 机制以便绕过部分 DOM 限制 — v1.2
- ✓ 在 agent.py 中将这 15 个功能进行准确的 Schema 注册与系统提示词外置描述 — v1.2

### Active

- 3. 选区与蒙版 (Selection & Mask) 功能接入
- 4. 专业调色与光影 (Color Correction) 功能接入
- 5. 高级滤镜与人像美化 (Filters & Retouching) 功能接入
- 6. 自动化与动作集成 (Automation & Actions) 功能接入

### Out of Scope

- 废弃所有关于 UXP 插件迁移的计划：因目标环境 (免安装版 Photoshop 2026) 精简了 UXP 验证与加载引擎，强行挂载会引发白屏或拉黑，故全面退回 Web+COM 方案。
- 不支持 function calling 的模型降级方案 — 所有 PS 操作强依赖 tool use，降级复杂度高
- 多 provider 同时在线/热切换对话 — v1.0 仅限单例全局配置切换使用

## Context

- 运行环境：Windows + Adobe Photoshop (通过 win32com 进行本地化控制)
- 架构调整：彻底抛弃 UXP 插件思路，用户仅需在浏览器打开 Web UI，通过 Socket 与 Python 后端通信，由后端 COM 接管 PS。
- 核心突破：引入 `ps_app.DoJavaScript()` 后门能力，确保 COM 可以实现所有原先只有 UXP batchPlay 能完成的操作。

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
| 引入 JS 层面安全校验拦截空图层操作 | 防止空图层转化为智能对象时，触发 Photoshop 原生弹窗导致 Python 进程永久阻塞 | ✓ Good (v1.2) |
| 提示词外置 | 将硬编码提示词抽离至 markdown 文件中，支持动态加载热重载与 Fallback | ✓ Good (v1.2) |

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
*Last updated: 2026-06-13 after milestone v1.3 initialized*
