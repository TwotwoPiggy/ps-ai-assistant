# Phase 4 Plan: 搭建 UXP 基础环境与通信

## Steps

### Step 1: 后端双引擎架构重构 (INFRA-04)
- **Subtasks:**
  - [ ] 定义抽象的 `PSEngine` 基类（或接口），包含核心的异步执行方法，例如 `execute_tool(self, tool_name: str, args: dict) -> dict`。
  - [ ] 将当前的 `PhotoshopContext` 及 `pywin32` COM 调用逻辑包装为 `COMEngine`，确保现有流程稳定平移。
  - [ ] 编写新的 `UXPEngine` 实现类，需注入当前的 Socket.IO server `sio` 实例以及对应的客户端 `sid`，使用 `await self.sio.call('execute_tool', {...}, to=self.sid)` 来派发指令至前端。
  - [ ] 在处理大模型生成的 function calling 的调度逻辑（如 `PhotoshopAgent`）中，根据客户端连接信息或全局配置动态路由，决定使用 `COMEngine` 还是 `UXPEngine` 处理工具调用。
- **Verification:**
  - 运行后端并使用现有的浏览器端发送命令，验证基于 `COMEngine` 的原有工作流仍然正常，未遭到破坏。

### Step 2: UXP Vite 构建配置与 Manifest (INFRA-01)
- **Subtasks:**
  - [ ] 在前端代码（如 `frontend` 目录）中新增 UXP 专用入口文件（例如 `uxp_main.tsx`），使用 UXP 的 `entrypoints.setup` 注册挂载生命周期，并在 `show(event)` 时执行 React `createRoot` 挂载现有根组件 `<App />`。
  - [ ] 新建专属的打包配置（如 `vite.uxp.config.ts`），设置 `outDir`（例如 `dist_uxp`），并根据 UXP 限制配置必要的 polyfill 或外部依赖忽略规则。
  - [ ] 生成 UXP 插件必须的 `manifest.json`，声明 Photoshop 作为 `host` (`app: "PS"`)，配置正确的入口文件映射，并且声明网络权限 `"network": { "domains": "all" }`。
  - [ ] 在 `package.json` 添加专属构建脚本（如 `build:uxp`），并将其纳入工程 CI 或日常运行流。
- **Verification:**
  - 执行 UXP 打包脚本成功，并在 Photoshop 内通过 UXP Developer Tool (UDT) 成功加载开发目录，成功显示包含当前 React 应用的插件面板。

### Step 3: 前端 UXP ModalQueue 与 Socket 通信对接 (INFRA-02, INFRA-03)
- **Subtasks:**
  - [ ] 在前端构建 `ModalQueue` 管理器，通过 Promise 队列将任务封装入 `require('photoshop').core.executeAsModal` 中串行执行，避免发生 "Modal state is active" 的报错冲突。
  - [ ] 配置 `socket.io-client` 连接 FastAPI 后端，强制使用 `transports: ["websocket"]`，并在连接的 auth 信息中携带特征标识 `auth: { client_type: 'uxp' }` 以便后端准确识别其身份。
  - [ ] 在 UXP 前端挂载全局 Socket 事件监听（如 `execute_tool`），接收指令后推送入 `ModalQueue` 进行执行，并在 Promise 解决后触发 Socket acknowledge 返回给后端执行结果。
- **Verification:**
  - 插件启动后，后端能接收并识别 UXP Socket 建立连接；触发一个模拟的报错操作时，队列能够捕获错误并通过 ack 将失败结果正确反馈给后端。

### Step 4: 端到端集成测试
- **Subtasks:**
  - [ ] 编写基础的测试代码或利用一个简单的现存功能（例如新建文本层或调整图层名称），走完整链路进行调用。
  - [ ] 调用流程：大模型解析出指令 -> 后端识别 `UXPEngine` -> `sio.call` 发给 UXP -> `ModalQueue` 接管执行 -> `executeAsModal` 驱动 PS -> `sio ack` 返回结果 -> 后端响应给大模型。
- **Verification:**
  - 提供视频或截图证明 UXP 通道走通了一个真实的 PS 修改动作，且通信链路不阻塞界面，不产生并发异常。
