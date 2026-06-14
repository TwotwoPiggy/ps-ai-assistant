# Phase 04 Context: 选区与蒙版控制 (Selection & Mask)

## Domain
实现基础与智能选区、蒙版以及通道控制相关的全部操作 API。重点在于设计稳定的交互机制与边界容错处理。

## Canonical References
- [COM-CAPABILITIES-REFERENCE.md](../../../docs/COM-CAPABILITIES-REFERENCE.md)

## Decisions Captured
- **选区叠加机制**: 支持组合操作。API 需要增加 `selection_mode` 参数，支持 `replace` / `add` / `subtract` / `intersect`，默认值为 `replace`。
- **智能选区超时与容错**: 必须明确捕获异常并反馈给 AI。如果“选择主体”或“移除背景”找不到明确主体，底层应捕获异常并向大模型返回明确的错误结果，由大模型负责组织文案向用户反馈。
- **通道存取命名机制**: 由 AI 负责语义化命名，同时包含后备机制。API 需要提供 `channel_name` 参数；如果不传，则底层自动以时间戳或默认名称命名。
- **蒙版应用保护**: 提供破坏性的“应用蒙版”功能，但进行限制拦截。大模型必须显式传入类似 `force_apply: true` 的参数才能成功执行，以防止 AI 误操作导致像素永久丢失。

## Code Context
- 本阶段所有涉及 DOM 无法直接支持的操作（如智能选择、通道转化等），应复用前序 Phase 跑通的 `DoJavaScript` 注入模式实现。
- 错误抛出与处理，可复用现有的基础 `PhotoshopContext` COM 异常处理机制。
