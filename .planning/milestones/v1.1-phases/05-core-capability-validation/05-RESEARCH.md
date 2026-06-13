# Phase 5: 验证核心功能与事件机制 - Research & Planning Guide

## 1. 现有上下文与现状分析
在 Phase 4 中，我们已经实现了 UXP 基础环境与基于 Socket.IO 的双向通信，并在 `modalQueue.ts` 中完成了对 `executeAsModal` 串行队列的封装。
对于本阶段 (Phase 5) 需要测试的 11 个核心操作，目前已经在 `frontend/src/uxpTools.ts` 中完全使用了 **UXP DOM API v2** 实现了基础版本（如 `layer.adjustBrightnessContrast`、`doc.crop` 等）。
目前尚未实现任何这些工具的 `batchPlay` 版本，且前端的 `socket.ts` 和后端的 `server.py` 均尚未实现由 UXP 主动向服务端推送 Photoshop 事件的反向通信通道。

## 2. 梳理 CAP-01 & CAP-02 (batchPlay 边界与能力验证)
为了全面完成对 11 个操作的 DOM API 与 `batchPlay` 效果对比，需要在计划中包含以下工作：
- **获取 ActionDescriptors**: 针对这 11 个操作，使用 Alchemist 或 UXP Developer Tools 抓取对应的 `batchPlay` JSON 描述符。
- **编写 batchPlay 替代实现**: 在 `uxpTools.ts` (或独立的测试文件) 中增加并行测试函数（例如 `create_layer_batchplay`）。需要确保 batchPlay 调用同样经过 `modalQueue.enqueue` 进行 `executeAsModal` 调度。
- **验证并记录指标**: 逐一在真实的 Photoshop UXP 环境中运行 DOM API 和 batchPlay 版本的代码，收集：
  - 接口是否调用成功、执行速度、是否报错或存在沙盒限制。
  - 对于简单操作（如图层可见性、重命名等），评估 DOM API 的健壮性。
  - 对于复杂操作（如亮度对比度、裁剪等），评估 batchPlay 对比 DOM API v2 的优缺点和灵活性。
- **输出成果文件**: 生成 `05-CAPABILITY-MATRIX.md` 文档，记录完整的对比表（包含工具名、COM方案状态、UXP DOM方案状态、batchPlay方案状态、推荐方案及备注限制）。

## 3. 梳理 CAP-03 (事件反向推送机制)
在 UXP 中监听 Photoshop 原生事件，必须调用 `photoshop` 模块下的事件监听器接口。
- **前端 (UXP) 侧工作**: 
  - 使用 `require('photoshop').action.addNotificationListener(['select', 'open', 'close'], callback)`。
  - 在回调事件中，识别并提取事件的关键数据（如变动的被选中图层 ID、文档的变更状态）。
  - 在 `frontend/src/socket.ts` 中新增逻辑，通过 `socket.emit("ps_event", payload)` 主动向 FastAPI 服务器推送。
- **后端 (FastAPI) 侧工作**:
  - 在 `backend/server.py` 中新增 `@sio.event async def ps_event(sid, payload)` 事件处理，用于接收 UXP 推送的事件并打印日志。验证后端是否能够正确感知前端 Photoshop 状态的变化。
- **事件过滤目标**:
  - **图层选择变化**: 主要拦截 `select` 事件，并识别其 target 是否为图层 (layer)。
  - **文档打开/关闭**: 主要拦截 `open` 和 `close` 事件。

## 4. 给 Plan 阶段的明确建议 (What you need to PLAN)
基于以上调研，在接下来的计划（Plan）步骤中，你需要创建以下核心 Tasks 以平稳交付此阶段：
1. **Task 1: 准备 batchPlay 调用的测试基准代码**
   在 UXP 端补充 11 个操作对应的 `batchPlay` 实现以供 PoC 验证。
2. **Task 2: 实现 PS 反向事件监听与 WebSocket 推送**
   修改 `socket.ts` 注册 UXP Notification Listener 并使用 socket.emit 发送 `ps_event`；修改 `server.py` 新增相应的接收处理和日志打印。
3. **Task 3: 执行双引擎对比测试与收集数据**
   实际部署插件并运行测试，通过界面或终端触发 11 个工具的 DOM 和 batchPlay 双通道，同时测试文档变更和图层点击事件的推送是否成功，记录实际表现。
4. **Task 4: 生成评估矩阵与总结报告**
   汇总数据结果，编写 `.planning/phases/05-core-capability-validation/05-CAPABILITY-MATRIX.md` 交付物，并根据测试结果为 Phase 6 的全面迁移决定出每项工具的推荐落地方案（混合策略）。
