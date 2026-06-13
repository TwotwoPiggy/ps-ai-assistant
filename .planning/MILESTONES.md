# Milestones

## v1.2 Photoshop 核心功能全面 UXP 迁移与重构 (Shipped: 2026-06-13)

**Phases completed:** 3 phases, 3 plans, 7 tasks

**Key accomplishments:**

- 在 ps_tools 中成功改造并引入了 8 个全新的文档与视图管理 COM 工具，底层原生支持 DoJavaScript 注入，并在 registry 中全量注册

---

## v1.1 研究并整理uxp支持的所有操作有哪些 (Shipped: 2026-06-13)

**Phases completed:** 3 phases, 5 plans, 0 tasks

**Key accomplishments:**

- Plan
- Plan
- Plan

---

## v1.0 多 Provider 支持 (Shipped: 2026-06-12)

**Phases completed:** 3 phases, 3 plans, 10 tasks

**Key accomplishments:**

- 实现统一的 BaseProvider 接口抽象，解耦并迁移 11 个 Photoshop 工具为纯函数并自动生成 Schema，支持安全脱敏的 API 配置管理。
- 完成流式客户端改造以实时提取并推送 DeepSeek R1 推理思维链，实现连接超时时自适应降级回退至 Gemini 的安全兜底，并修正了并行工具的队列排列顺序以完全符合 OpenAI 标准。
- Completed:

---
