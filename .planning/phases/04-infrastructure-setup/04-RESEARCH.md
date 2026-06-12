# Phase 4 Research: UXP 基础环境与通信

## Objective
明确如何构建 UXP 插件的底层基础脚手架，实现与后端的 WebSocket 通信，建立统一的模态操作队列，并设计出兼容当前 `pywin32` 的双引擎解耦方案。

## 1. UXP 插件骨架与构建 (INFRA-01)
- **多端构建策略**: 我们现有一个完整的 React SPA 位于 `frontend`。为了实现“多端共存”，不应破坏现有的 Web 版本，建议新增一个入口（如 `uxp_main.tsx`）和专门的构建配置（如 `vite.uxp.config.ts`）。
- **Manifest**: 必须在根目录生成 `manifest.json`，核心需要：
  - `host`: 指定 Photoshop（`app: "PS"`）。
  - `entrypoints`: 注册面板端点，并指明 JS 入口文件。
  - `requiredPermissions`: 尤其是 `"network": {"domains": "all"}`，否则 WebSocket 无法连接后端。
- **React 挂载**: UXP 通过 `entrypoints.setup({ panels: { id: { show(event) {...} } } })` 提供挂载点，可以在 `show` 生命周期中通过 `createRoot(event.node)` 挂载复用的 `<App />`。

## 2. UXP 与 FastAPI 的双向通信 (INFRA-02)
- **前端 (Socket.io-client)**: 
  - UXP 虽支持 WebSocket，但环境异于标准浏览器，为防 fallback 导致连接失败，连接参数应显式指定 `transports: ["websocket"]`。
  - 需向后端发送标志（如连接时带上 `auth: { client_type: 'uxp' }`），以便后端识别当前连接是 UXP 端点，可接收操作指令。
- **后端 (python-socketio)**:
  - 后端向 UXP 派发任务需要**等待执行结果**再返回给 LLM。`python-socketio` 的 `AsyncServer` 自带 RPC 风格的 `call()` 方法（`await sio.call('execute_tool', data, to=sid)`），前端事件监听回调可直接将执行结果返回。这能极大地简化通信模型。

## 3. UXP 统一模态队列 (INFRA-03)
- **机制与冲突**: UXP 中对文档修改必须包含在 `require("photoshop").core.executeAsModal(taskFn)` 内。并且，若当前已有操作处于 Modal 状态，再次调用会引发 Error。
- **设计 `ModalQueue`**: 
  - 前端需维护一个 Promise 队列管理器。
  - 后端下发 `execute_tool` 事件时，事件处理器需通过 `ModalQueue.enqueue(() => executeAsModal(task))` 将任务排队。队列保证上一任务 `resolve/reject` 后再弹出执行下一任务，彻底规避界面阻塞和状态冲突。

## 4. 双引擎解耦架构 (INFRA-04)
为了兼容后续既能走旧版 Python COM 调用，又能走新版 UXP 调用，需要在后端进行重构：
- **引入 `PSEngine` 接口 (Strategy Pattern)**:
  - 定义抽象类 `PSEngine`，包含 `async execute_tool(self, tool_name: str, args: dict) -> dict` 核心方法。
- **具体实现 (Adapters)**:
  - **`COMEngine`**: 包装现有的 `ps_tools.py` 与 `PhotoshopContext`。当前的代码逻辑原封不动移至此处。
  - **`UXPEngine`**: 注入客户端连接对象 (`sid`, `sio`)，其 `execute_tool` 实现为 `await self.sio.call('execute_tool', {'tool': tool_name, 'args': args}, to=self.sid)`。
- **路由分发**: `PhotoshopAgent` 处理用户的自然语言聊天时，根据发送消息的客户端连接状态或全局配置（`get_ai_config()`）动态实例化对应的 `PSEngine`。LLM 生成 function calling 后，统一调用 `engine.execute_tool(name, args)`，后端不再关心底层是 COM 还是 UXP。

## Next Steps for Planning
- 在 PLAN.md 中划分四个步骤：1. 后端双引擎重构；2. UXP Vite 构建与 Manifest 配置；3. 前端 UXP ModalQueue 与 Socket 事件绑定；4. 端到端测试。
