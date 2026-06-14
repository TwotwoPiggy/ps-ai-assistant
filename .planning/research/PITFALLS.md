# UXP 扩展研究与集成避坑指南 (PITFALLS.md)

## 概述
本文档专注于在现有的基于 COM 接口 (pywin32) 的 Photoshop AI 助手中引入 UXP (Unified Extensibility Platform) 功能时可能遇到的典型陷阱。内容专门针对架构演进过程中的功能叠加，侧重预警信号、预防策略以及应在哪个开发阶段重点解决这些问题。

---

## 1. 模态执行状态冲突 (Modal Execution Context Collision)
**陷阱描述：**
UXP 严格要求所有可能修改文档状态（DOM 操作或 `batchPlay`）的操作必须被包裹在 `executeAsModal` 中。而现有系统基于 COM，通常不受此限制，这会导致旧有的操作思维在迁移到 UXP 时引发频繁的 API 拒绝。此外，若长时间占据 Modal 状态，将严重阻断用户的手动操作。

**下游消费者关注点：**
- **Warning signs (预警信号):**
  - 控制台频发 `Error: document requires modal state`。
  - AI 任务在并发触发时随机失败或卡死。
  - 用户抱怨在 AI "思考" 或执行任务时，Photoshop 界面完全锁死，无法使用工具。
- **Prevention strategy (预防策略):**
  - 建立统一的操作队列管理器，强制隔离“只读状态获取”与“写入操作”，只有写操作才申请 Modal。
  - 配置 `executeAsModal` 的进度条反馈与可取消 (cancellation) 策略。
- **Which phase (应在哪个阶段解决):** UXP 基础架构设计阶段 (UXP Infrastructure Design)

---

## 2. API 断层与过度依赖 BatchPlay
**陷阱描述：**
UXP 的高级 DOM API (如 `app.activeDocument`) 虽然易用，但覆盖率远低于旧版 ExtendScript 或 COM 原生能力（尤其是智能滤镜、复杂选区和混合模式操作）。开发者往往会被迫大量使用录制的 `batchPlay` JSON 动作，导致代码极难维护且容易因 PS 版本更新而损坏。

**下游消费者关注点：**
- **Warning signs (预警信号):**
  - 代码库中快速堆积大量晦涩难懂的未注释 JSON `batchPlay` 调用。
  - API 升级后某些滤镜或特定图层操作静默失败。
- **Prevention strategy (预防策略):**
  - 实施严格的 "DOM 优先" 原则，只有在确信 DOM 不支持时才使用 `batchPlay`。
  - 将所有 `batchPlay` 调用隔离在专门的中间层（Repository Pattern），并附带 Alchemist 录制时的元数据或注释。
  - 强制解析 `batchPlay` 返回的数组对象，捕获并抛出所有非成功状态码。
- **Which phase (应在哪个阶段解决):** API 能力测试与封装阶段 (API Wrappers & Testing Phase)

---

## 3. 双系统状态不同步与 IPC 冲突
**陷阱描述：**
保留原有 COM 通道的同时新增 UXP 插件（前端/宿主），意味着项目中将存在两个都可以修改和读取 PS 状态的“大脑”。如果是将 FastAPI 后端与 UXP 插件通过 WebSocket 连接，极易发生端口冲突、跨域网络拦截或者状态读取的竞态条件。

**下游消费者关注点：**
- **Warning signs (预警信号):**
  - UXP 尝试向本地 Python 服务发送 HTTP/WS 请求时报 Network Error 或 CORS 错误。
  - AI 根据过期的图层树信息做出错误的画布调整决策。
- **Prevention strategy (预防策略):**
  - 明确“单一真相来源 (Single Source of Truth)”。当启用 UXP 通道时，禁用 COM 的写操作权限，将其降级为只读或备用通道。
  - 采用事件驱动模型代替轮询：利用 UXP 事件侦听器在图层变动时主动向后端推送状态快照。
  - WebSocket 必须在 UXP 端做好断线重连和心跳保活逻辑。
- **Which phase (应在哪个阶段解决):** 通信架构与集成阶段 (Communication Architecture Phase)

---

## 4. 文件系统沙盒隔离 (Sandbox File System Limits)
**陷阱描述：**
现有的 COM 通道可以通过 Python 无阻碍地对全盘进行读写（如保存截图至系统临时目录）。但 UXP 是沙盒化的，默认只能访问插件内部目录和临时文件夹。任何外部文件的读写如果不经过显式的用户交互（弹窗授权），都会直接报错。

**下游消费者关注点：**
- **Warning signs (预警信号):**
  - 截图发送、导出图像等自动化工作流被中断，弹出需要用户手动选择文件夹的对话框。
  - 控制台报 `Permission Denied` 或无法找到指定路径。
- **Prevention strategy (预防策略):**
  - 使用 `localFileSystem.temporaryFolder` 作为 UXP 与外部/后端的临时文件交换中转站。
  - 如果必须访问特定用户目录，在插件首次运行时向用户请求一次授权，并利用 `createPersistentToken` 保存令牌，避免反复弹窗。
- **Which phase (应在哪个阶段解决):** 快照与文件 IO 迁移阶段 (Snapshot & File I/O Phase)

---

## 5. UI 线程拥塞处理不当
**陷阱描述：**
UXP 的 JS 引擎与 PS 的主 UI 共享计算资源。当需要解析非常庞大、嵌套极深的图层树，或者尝试通过 Base64 在 JS 内存中传递大型画布截图时，会导致 Photoshop 界面出现明显的掉帧或短暂冻结。

**下游消费者关注点：**
- **Warning signs (预警信号):**
  - 解析含有数百个图层/组的文档时，光标变更为等待状态，界面无法响应。
  - 插件占用内存激增，影响绘画性能。
- **Prevention strategy (预防策略):**
  - 避免深度的递归图层遍历，或者在遍历中加入 `await new Promise(r => setTimeout(r, 0))` 来让出线程时间片。
  - 对于图像快照，摒弃 Base64 内存流，改为通过 UXP 生成文件到临时目录，再由 Python 后端读取和处理的方式。
- **Which phase (应在哪个阶段解决):** 性能优化与前端适配阶段 (Performance & UI Adaptation Phase)

---

## 6. Manifest 权限配置遗漏
**陷阱描述：**
UXP 强制要求所有的外部网络通信、跨域访问、本地文件访问甚至是剪贴板访问都在 `manifest.json` 中预先声明。这在开发阶段（使用 UDT 挂载）可能不明显，但一旦打包成成品，功能将立刻失效。

**下游消费者关注点：**
- **Warning signs (预警信号):**
  - 在 UDT 调试模式下一切正常，但在独立安装 `.ccx` 插件后，网络通信中断或无法获取剪贴板数据。
  - 打包工具报出 Manifest 配置验证失败。
- **Prevention strategy (预防策略):**
  - 维护一份《权限检查清单》，并在 `manifest.json` 中的 `requiredPermissions` 详细声明（如 `localFileSystem`，网络域名如 `localhost` 或具体的 API 网址）。
  - 在 CI 或构建脚本中增加检查，确保打包前 Manifest 正确无误。
- **Which phase (应在哪个阶段解决):** 打包部署与环境配置阶段 (Deployment & Release Planning Phase)
