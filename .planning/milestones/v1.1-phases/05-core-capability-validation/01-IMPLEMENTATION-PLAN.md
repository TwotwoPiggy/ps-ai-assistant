---
wave: 1
depends_on: []
files_modified:
  - frontend/src/batchPlayTools.ts
  - frontend/src/uxpTools.ts
  - frontend/src/socket.ts
  - backend/server.py
autonomous: true
---

# Phase 5: 验证核心功能与事件机制 - Implementation

## Goal
准备用于对比测试的 batchPlay 实现，并完成 UXP 事件的反向监听与推送功能开发。

## requirements
CAP-01, CAP-03

## must_haves
- 提供 11 个工具的 batchPlay 替代实现
- UXP 前端能够监听 'select', 'open', 'close' 原生事件并通过 Socket.IO 推送给后端
- FastAPI 后端能够成功接收并打印 `ps_event`

## Tasks

### [ ] Task 1: 编写 batchPlay 测试基准代码
**requirements**: CAP-01

<read_first>
- frontend/src/uxpTools.ts
- frontend/src/modalQueue.ts
</read_first>

<action>
1. 创建新文件 `frontend/src/batchPlayTools.ts`，使用 `require('photoshop').action.batchPlay` 实现 11 个对应工具的操作逻辑（get_layer_tree, get_canvas_snapshot, create_layer, delete_layer, rename_layer, set_layer_visibility, reorder_layer, adjust_brightness_contrast, crop_canvas, resize_canvas, flip_image）。如果某些操作如 snapshot 无 batchPlay 方案，可退化为复用 DOM 或抛出不支持。
2. 修改 `frontend/src/uxpTools.ts`，导入 `batchPlayTools`，并修改 `executeUXPTool` 函数：检查 `args._use_batchplay` 标志，如果为 true，则路由调度到 `batchPlayTools` 中的实现，否则使用原有的 `uxpTools` 实现。
</action>

<acceptance_criteria>
- `frontend/src/batchPlayTools.ts` 存在并导出了对应的工具函数字典。
- `frontend/src/uxpTools.ts` 的 `executeUXPTool` 支持接收 `_use_batchplay` 参数并正确完成分支调度。
- TypeScript 编译无报错。
</acceptance_criteria>

### [ ] Task 2: 实现 PS 反向事件监听与推送
**requirements**: CAP-03

<read_first>
- frontend/src/socket.ts
- backend/server.py
</read_first>

<action>
1. 在 `frontend/src/socket.ts` 的 `if (isUXP)` 分支内，引入 `require('photoshop').action`。
2. 调用 `action.addNotificationListener(['select', 'open', 'close'], callback)`，在回调中提取事件名称和数据，并通过 `socket.emit('ps_event', { event, data })` 实时发送给后端服务器。
3. 修改 `backend/server.py`，新增 `@sio.event async def ps_event(sid, payload)` 处理函数，函数内部使用 `print` 打印接收到的事件详细日志（例如 `[PS-AI] 收到 UXP 事件: ...`）。
</action>

<acceptance_criteria>
- `frontend/src/socket.ts` 包含了 `addNotificationListener` 并有 `socket.emit('ps_event')` 调用。
- `backend/server.py` 中存在 `@sio.event async def ps_event` 的定义及对应的 print 逻辑。
- 启动服务并在 Photoshop 中切换图层时，服务端控制台会打印出 `[PS-AI] 收到 UXP 事件:` 的相关日志。
</acceptance_criteria>
