# Phase 3: 前端配置面板改造 - Context

**Gathered:** 2026-06-12
**Status:** Ready for planning

<domain>
## Phase Boundary

改造前端 API 配置面板以支持多提供商切换、单独的 API Key/Base URL/Model 字段表单、明文掩码防覆盖交互，以及在聊天区域监听并优雅渲染流式 R1 推理思维链的气泡。

</domain>

<decisions>
## Implementation Decisions

### 1. 多 Provider UI 表单设计
- **D-01:** 在前端配置面板展开时，采用下拉选择框（Dropdown）来切换当前的 Provider，并在下方仅动态渲染该 Provider 对应的特定字段：
  - `gemini`: 显示 API Key, Model（下拉菜单）。Base URL 不显示或只读。
  - `deepseek`: 显示 API Key, Model（下拉菜单）。Base URL 不显示或只读。
  - `qwen`: 显示 API Key, Model（下拉菜单）。Base URL 不显示或只读。
  - `mimo`: 显示 API Key, Base URL（输入框，可编辑）, Model（下拉菜单）。
  - `custom`: 显示 API Key, Base URL（输入框，可编辑）, Model（输入框，可编辑）。
- **D-02:** 所有 Provider 的字段均独立于状态管理，当切换下拉框时，仅保存和更新当前选中 Provider 的本地表单状态，点击“保存”时一次性通过 Socket.IO 发送至后端。

### 2. 实时思维链渲染设计
- **D-03:** 前端添加对 Socket.IO 消息 `ai_chat_thinking` 的监听，用来接收实时推送的 DeepSeek-R1 推理思维链。
- **D-04:** 在助手回复气泡顶部上方渲染一个独立的可折叠面板（Collapsible Accordion）。此面板在思考阶段默认展开并随着流式词包实时追加内容，模型开始输出最终正文后（或完成思考后）允许用户手动折叠收起。
- **D-05:** 思考气泡的样式应与最终正文气泡有明显的视觉区隔。使用 Vanilla CSS 设计轻量、现代的淡灰色虚线框或半透明背景，配合微小的过度动画和伸缩手风琴效果。

### 3. 安全掩码与编辑覆盖交互
- **D-06:** 各 Provider API Key 的 input 输入框类型设为 `password`。
- **D-07:** 初次载入时显示脱敏掩码（如 `gemi****2345`）。当输入框被点击聚焦（onFocus）且内容包含掩码（含有 `*` 字符）时，自动清空输入框内容以供用户直接重新输入新 Key。
- **D-08:** 如果用户失焦时没有修改内容，则输入框恢复为原掩码；若用户直接以原掩码提交保存，后端在处理时会识别并自动忽略，防止覆盖已保存的真实值。

### the agent's Discretion
- 伸缩面板的动画持续时间和缓动函数。
- 思维链展开/折叠箭头的具体微图标（例如 ▾/▸ 或 自定义 SVG）。
- 表单在加载中的禁用状态和加载指示器的样式。

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Roadmap
- `.planning/ROADMAP.md` — 规定了 Phase 3 的目标为“改造前端 API 配置面板，支持多提供商切换、单独字段表单、掩码编辑覆盖交互以及 R1 推理思维链气泡”
- `.planning/STATE.md` — 项目当前状态。

### Codebase Implementations
- `frontend/src/ChatPanel.tsx` — 前端聊天与配置核心面板。
- `frontend/src/styles.css` — 样式定义文件，需在此新增 Vanilla CSS 样式。

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/src/ChatPanel.tsx` 里的 `socket.emit("ai_config", { action: "get" })` 和 `socket.emit("ai_config", { action: "save", ... })` 交互流程。
- `frontend/src/styles.css` 中的全局设计基调，新的组件和动画应与当前现代暗黑/透光磨砂玻璃微动画风格一致。

### Established Patterns
- 使用 Socket.IO 监听 `ai_chat_response` 和 `ai_chat_status`。同样模式用来监听 `ai_chat_thinking`。

</code_context>

<specifics>
## Specific Ideas
- 需确保当切换 Provider 时，模型下拉列表或输入框内容与后端支持的模型选项完美匹配。

</specifics>

<deferred>
## Deferred Ideas
None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-前端配置面板改造*
*Context gathered: 2026-06-12*
