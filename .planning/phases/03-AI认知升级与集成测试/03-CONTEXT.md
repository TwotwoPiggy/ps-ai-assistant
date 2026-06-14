# Phase 03: AI 认知升级与集成测试 - Context

**Gathered:** 2026-06-13 (assumptions mode)
**Status:** Ready for planning

<domain>
## Phase Boundary

在大模型提示词中全面暴露 15 个新接口，分离硬编码的提示词，并进行整体连贯性对话测试。
</domain>

<decisions>
## Implementation Decisions

### 系统提示词外置化
- **D-01:** 将 `backend/agent.py` 中硬编码的 `system_instruction` 外置为独立的 Markdown 或文本文件（如 `backend/prompts/system_prompt.md`），在运行时动态读取。

### 接口语义与能力升级
- **D-02:** 在提示词中明确 `resize_canvas`（调整画布工作区大小，不缩放图像像素）与 `resize_image`（缩放整个图像及其所有图层像素）的区别与具体使用场景。
- **D-03:** 增加复合操作指导：指导大模型在处理复合自然语言指令时（如“置入图片并转智能对象”），通过合理的步骤链顺次执行多个 Tool 调用。
- **D-04:** 明确大模型当前的图层高级操控能力（编组、合并、模式切换、透明度调节、移动等），以及文档/画布操作能力。

### the agent's Discretion
- 具体外部提示词文件存放的路径名和后缀名可由执行阶段决定，但需保证打包/部署可用。
- 集成测试将通过纯文本会话或者前端 UI 界面完成，不引入额外的单元测试框架。
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

- `backend/agent.py`
- `backend/tools/registry.py`
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `registry.get_openai_schemas()` 已经能够全自动抽取并暴露所有挂载了 `@registry.register` 的工具。

### Established Patterns
- 工具的调用和收集已经在 `agent.py` 中完成，且支持多步并行的 Tool Calls 以及自动回退机制。

### Integration Points
- `agent.py` 在实例化 Provider 和准备对话历史时，将原有的硬编码变量替换为文件读取机制即可。
</code_context>

<specifics>
## Specific Ideas

- 用户明确指定：**必须将系统提示词外置为一个单独的 markdown/text 文件，而不是硬编码在 agent.py 里**。
</specifics>

<deferred>
## Deferred Ideas

None — analysis stayed within phase scope
</deferred>
