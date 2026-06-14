---
gsd_state_version: 1.0
milestone: v1.3
milestone_name: COM 接口高级能力实现
status: planned
last_updated: "2026-06-14T10:26:00.000Z"
last_activity: 2026-06-14
progress:
  total_phases: 4
  completed_phases: 2
  total_plans: 3
  completed_plans: 2
  percent: 50
---

## Current Position

Phase: 06 (高级滤镜与人像美化) — READY_TO_EXECUTE
Plan: 0 of 1
Status: Phase 06 planned, ready to execute
Last activity: 2026-06-14 — Completed planning for Phase 06


## Project Reference

See: .planning/PROJECT.md (updated 2026-06-13)

**Core value:** 用户可以用自然语言直接控制 Photoshop，AI 自动理解意图并执行对应的 PS 操作。
**Current focus:** Defining requirements

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
- Phase 05: 模糊调色指令必须向用户前置询问“是否使用无损调整图层”以及“是否将选区转为蒙版”。
- Phase 05: 后端颜色 API 仅接收严谨数值（RGB/Hex/HSB等），由大模型使用多模态视觉或语义能力自行换算中文色彩词。
- Phase 05: 高级调色提供子通道级参数支持，但大模型应默认优先调节主通道。
- Phase 05: CAF 严禁无选区运行，必须被拦截并引导用户绘制或智能创建选区。

### Blockers

(none)

### Todos

(none)
