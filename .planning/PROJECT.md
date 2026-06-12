# PS AI Assistant

## What This Is

一个 Photoshop AI 助手，通过自然语言聊天界面让用户用中文描述操作意图，AI 自动调用 Photoshop COM 接口执行图层管理、画布编辑、亮度对比度调整等操作。支持多种 AI Provider，用户可在前端配置面板灵活选择和切换。

## Core Value

用户可以用自然语言直接控制 Photoshop，AI 自动理解意图并执行对应的 PS 操作。

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

### Active

<!-- Pending next milestone planning -->
- (暂无，等待规划下一个里程碑)

### Out of Scope

- 不支持 function calling 的模型降级方案 — 所有 PS 操作强依赖 tool use，降级复杂度高
- 多 provider 同时在线/热切换对话 — v1.0 仅限单例全局配置切换使用

## Context

- 运行环境：Windows + Adobe Photoshop (COM 接口依赖)
- SDK 策略：Gemini 走原生 `google-genai`，其他厂商通过 `AsyncOpenAI` 兼容
- 通信机制：FastAPI + Socket.IO 进行事件握手
- 已发布版本：v1.0 (多 Provider 支持与安全脱敏配置落盘，R1 实时思考流显示)

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

---
*Last updated: 2026-06-12 after milestone v1.0 completion*
