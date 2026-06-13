---
gsd_state_version: 1.0
milestone: v1.2
milestone_name: Photoshop 核心功能全面 UXP 迁移与重构
status: verifying
last_updated: "2026-06-13T10:33:07.372Z"
last_activity: 2026-06-13
progress:
  total_phases: 2
  completed_phases: 1
  total_plans: 1
  completed_plans: 1
  percent: 100
---

## Current Position

Phase: 01 (文档管理增强与架构扩充) — EXECUTING
Plan: 1 of 1
Status: Phase complete — ready for verification
Last activity: 2026-06-13

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-13)

**Core value:** 用户可以用自然语言直接控制 Photoshop，AI 自动理解意图并执行对应的 PS 操作。
**Current focus:** Phase 01 — 文档管理增强与架构扩充

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
- 采用双引擎共存架构 (COM & UXP)，根据客户端在线状态进行运行时透明路由与自动平滑回退，实现前后端解耦
- 统一制定 UXP 开发 4 大铁律，并通过 .planning/GEMINI.md 将其作为全局 AI Guardrails 硬约束以规范后续开发
- 引入 DoJavaScript 注入通道，允许 Python COM 后端直接调用 JSX 脚本以执行高级/底层 Photoshop 操作
- 在 PhotoshopContext 中解耦 get_app() 接口以隔离文档和应用层操作，在没有打开文档的情况下支持新建画布和打开置入
- 色彩模式转换工具 (change_color_mode) 前置屏蔽警告弹框 (DisplayDialogs = 3)，并依靠 docstring 强契约实现在调用前由大模型向用户做人机交互授权确认
- 文档保存工具 (save_document) 在文档未曾存盘时自动以时间戳形式另存至用户的系统桌面

### Blockers

(none)

### Todos

(none)
