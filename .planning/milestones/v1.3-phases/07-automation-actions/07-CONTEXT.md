# Phase 07: 自动化与动作集成 (Automation & Actions) Context

This document captures implementation decisions and domain constraints for Phase 07. It is consumed by the planner and executor to ensure work aligns with user expectations.

## Domain
**What this phase delivers:**
支持直接调用录制动作、执行本地扩展脚本以及切片导出 API

**Canonical refs:**
- .planning/ROADMAP.md

## Decisions

### D-01: 自定义扩展脚本 (JSX/JSXBIN) 路径与权限策略
**Decision:** 采用结合白名单与用户授权的混合模式。
**Rationale:** 默认允许无缝执行 `backend/resources/scripts/` 目录下的可信脚本。当 AI/前端需要执行用户电脑其它绝对路径下的脚本时，必须在前端弹窗询问用户 (Allow/Deny)，保障安全性的同时不失灵活性。

### D-02: 动作 (Actions) 执行的容错与交互机制
**Decision:** 状态指引 + 允许挂起（不强制静默）。
**Rationale:** 像之前的液化滤镜一样，在触发可能会产生原生对话框或报错的 PS Action 前，AI 需先在聊天界面提示“请在 PS 内完成交互”。允许 Action 弹出原生交互界面，靠用户的手动干预完成工作流，避免通过静默模式一刀切导致功能中断。

### D-03: 切片导出的默认参数与保存机制
**Decision:** 采用智能预设并反馈结果的策略。
**Rationale:** 当指令未提供明确参数时，AI 将自动设置最为通用且高质量的参数（如 PNG-24），并将文件导出至常用路径（如系统桌面）。导出完毕后，必须在对话回复中明确告知用户文件所在的绝对路径。

## Code Context
- `backend/tools/ps_tools.py` — 已有的 `execute_jsx` 可以作为执行扩展脚本的基础，但需增加路径鉴权机制。
- `backend/agent.py` — 已有模态操作 UI 提示词机制，可复用于 PS Actions 的调用提示。
- `frontend/src/...` (待定) — 前端需新增针对危险操作 (执行任意外部 JSX) 的用户授权二次确认弹窗逻辑。
