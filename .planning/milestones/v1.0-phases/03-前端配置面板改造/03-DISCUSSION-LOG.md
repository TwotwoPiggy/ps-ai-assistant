# Phase 3: 前端配置面板改造 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-12
**Phase:** 03-前端配置面板改造
**Areas discussed:** 多 Provider UI 表单设计, 实时思维链渲染设计, 安全掩码与编辑覆盖交互

---

## 多 Provider UI 表单设计

| Option | Description | Selected |
|--------|-------------|----------|
| 方案 A | (推荐) 使用一个下拉选择框来切换当前 Provider，在下方仅动态渲染该 Provider 对应的 API Key、Base URL (Custom/MiMo专属) 和 Model 选择/输入框。 | ✓ |
| 方案 B | 采用并排或折叠式卡片展示所有 Provider 的配置面板，并在每个 Provider 旁边提供一个单选框（Radio）来标记“当前激活的 Provider”。 | |

**User's choice:** 方案 A
**Notes:** 用户同意推荐的方案 A，这种方式界面清爽，符合 Photoshop Panel 空间受限的特点。

---

## 实时思维链渲染设计

| Option | Description | Selected |
|--------|-------------|----------|
| 方案 A | (推荐) 在助手回复气泡上方渲染一个独立的可折叠面板（Collapsible Accordion）。默认展开显示流式思维链，模型开始输出正文时允许手动收起。 | ✓ |
| 方案 B | 作为一个特殊的淡色虚线框或独立区块嵌入在助手回复气泡的顶部，不可折叠，始终完整展示。 | |

**User's choice:** 方案 A
**Notes:** 用户同意推荐的方案 A。通过折叠手风琴面板可以极大地节省聊天区域，防止超长的推理链让用户在对话时感到视觉疲劳。

---

## 安全掩码与编辑覆盖交互

| Option | Description | Selected |
|--------|-------------|----------|
| 方案 A | (推荐) 输入框使用密码类型，初次载入展示掩码（如 gemi****2345）。用户点击聚焦时如果是掩码则清空供重新输入（若不输入则后端自动忽略掩码，不覆写原Key）。 | ✓ |
| 方案 B | 提供“眼睛”图标可切换明暗文。如果是掩码，用户必须手动点击旁边的“清除/编辑”按钮才能重新输入，避免聚焦时误触清空。 | |

**User's choice:** 方案 A
**Notes:** 用户倾向于使用聚焦时自动清空掩码的极简输入体验。结合后端已实现的安全防覆写逻辑，可以在无需额外按钮的情况下完成输入覆盖。

---

## the agent's Discretion
- 界面过渡动画细节以及具体折叠箭头的 SVG 样式设计。
- 各个特定提供商支持的预设模型列表。

## Deferred Ideas
None.
