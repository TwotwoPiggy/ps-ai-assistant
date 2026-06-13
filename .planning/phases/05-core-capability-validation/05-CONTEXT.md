# Phase 5 Context: 验证核心功能与事件机制

## Domain

在 Phase 4 已搭建好的 UXP 基础架构之上，实际验证核心 Photoshop 操作在 UXP 环境中的可行性。梳理 DOM API 与 batchPlay 的能力边界，逐一测试现有全部 11 个工具的 UXP 等效实现，并测试由 UXP 主动推送 PS 事件到后端的反向通信机制。

## Decisions Captured

### DOM API 与 batchPlay 的边界划分策略
- **混合策略**：在本次 PoC 中，对每个被测工具同时尝试 DOM API 和 batchPlay 两种实现。最终产出一张对比表，为后续里程碑的全面迁移提供依据。
- **DOM 用于简单操作**：图层 CRUD、重命名、可见性等简单操作预期 DOM API 可以直接覆盖。
- **batchPlay 用于复杂操作**：亮度对比度调整、裁剪、滤镜等操作很可能需要 batchPlay (ActionDescriptor) 来实现。
- **PoC 结束后再锁定最终方案**：不在本阶段做最终的 DOM-vs-batchPlay 决策，而是通过实际测试数据来驱动后续决策。

### 核心操作 PoC 验证的范围与深度
- **全量测试全部 11 个工具**：`get_layer_tree`、`get_canvas_snapshot`、`create_layer`、`delete_layer`、`rename_layer`、`set_layer_visibility`、`reorder_layer`、`adjust_brightness_contrast`、`crop_canvas`、`resize_canvas`、`flip_image`。
- **每个工具分别尝试 DOM API 和 batchPlay 两种方案**（在适用时），记录成功/失败、API 调用方式、注意事项和限制。
- **产出完整的能力/兼容性对照表**，作为 Phase 6 全量 API 清单的重要输入。

### PS 事件反向推送的目标范围
- **本阶段测试两类事件**：
  1. **图层选择变化** — 用户在 PS 中手动切换活动图层时，UXP 捕获事件并通过 WebSocket 推送到后端。这是 AI 助手最依赖的上下文信息。
  2. **文档打开/关闭** — 用户新建、打开或关闭文档时通知后端更新状态，防止对已关闭文档发送指令导致报错。
- **Deferred Ideas（后续阶段按需添加）**：
  - 画布尺寸变更事件
  - 历史记录步进 (Undo/Redo) 事件
  - 其他 PS 内部操作事件

### 测试结果的输出与记录方式
- **完整对照表文档**：每个工具产出一行记录，列包括：工具名 / COM 方案状态 / UXP DOM 方案状态 / batchPlay 方案状态 / 推荐方案 / 备注限制。
- **最终产出一份结构化的 Markdown 文档**（如 `05-CAPABILITY-MATRIX.md`），作为 Phase 6 的核心输入。

## Canonical References
- `.planning/phases/04-infrastructure-setup/04-CONTEXT.md` — Phase 4 双引擎、多端共存的架构决策
- `.planning/phases/04-infrastructure-setup/04-SUMMARY.md` — Phase 4 执行总结
- `frontend/src/uxpTools.ts` — Phase 4 已实现的 11 个 UXP DOM v2 工具（本阶段的验证基线）
- `frontend/src/modalQueue.ts` — executeAsModal 串行队列（本阶段 PoC 执行时必须经过此队列）
- `backend/tools/ps_tools.py` — 原始 COM 工具实现（对照参考）

## Code Context
- Phase 4 的 `uxpTools.ts` 已经用 UXP DOM v2 API 实现了全部 11 个工具的初始版本。本阶段的任务是在真实 Photoshop UXP 环境中逐一验证这些实现，识别出哪些需要用 batchPlay 替代，并测试事件推送机制。
- `modalQueue.ts` 中的 `ModalQueue` 类已经实现了 `executeAsModal` 的串行队列，所有 PoC 测试的 DOM 修改操作都必须通过此队列执行。
- `socket.ts` 中已配置了 UXP 端的 Socket.IO 连接和 `execute_tool` 监听器，事件推送需要在此基础上新增事件监听和 emit 逻辑。
