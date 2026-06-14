# UXP 开发防坑指南 (UXP Development Guidelines)

在基于 Adobe UXP (Unified Extensibility Platform) 为 Photoshop 开发插件时，存在一些与传统 Web 前端不同的底层限制和机制。为了保证插件稳定性、性能以及与外围大模型系统 (Python 后端等) 的顺畅通信，所有后续开发 **必须** 严格遵守以下四大核心铁律。

## 1. 存储沙盒限制 (Storage Sandbox Restriction)
UXP 具有极其严格的文件 I/O 沙盒机制，插件无法随意访问用户操作系统的绝对路径。
*   **铁律**：所有需要将 PS 画布内容或图像数据传递给外部系统的操作（例如生成快照传给多模态大模型），必须先通过 UXP API（如 `fs.getDataFolder()` 或 `fs.getTemporaryFolder()`）将文件保存到 UXP 允许的沙盒临时目录。
*   **规范**：文件保存后，读取其内容并转化为 Base64 字符串或其他序列化格式再通过网络协议（如 WebSocket）发送给后端。
*   **清理**：传递完成后，**必须** 立即调用文件删除接口清理临时文件，防止由于磁盘占用的隐性堆积导致插件异常。

## 2. 事件防抖机制 (Event Debounce)
UXP 可以监听 Photoshop 的各种底层事件（如选取图层、工具切换、属性修改等）。但某些事件（例如拖动滑动条调整不透明度）会在极短时间内触发成百上千次。
*   **铁律**：任何需要通过 WebSocket / Socket.IO 反向推送至外部后端（如状态同步）的事件监听，**绝对禁止** 裸调推送接口。
*   **规范**：必须在前端实现防抖（Debounce）或节流（Throttle）机制（例如 200ms~500ms 延迟）。
*   **风险**：如果不加限制地直接发送，将瞬间导致 WebSocket 队列积压（Event Storm），最终引发插件界面卡死或后端服务端崩溃。

## 3. executeAsModal 模态队列调度
Photoshop 对文档具有强锁机制。任何试图修改文档状态（图层增删改、应用滤镜、调整像素等）的操作，如果在非模态下执行将直接抛出异常。
*   **铁律**：所有修改 PS 状态的操作，必须通过 `require("photoshop").core.executeAsModal(async () => { ... })` 执行。
*   **规范**：由于 `executeAsModal` 不能并发执行（即在一个 Modal 执行期间，不能启动另一个 Modal），必须在插件层面实现一个 **全局的任务队列 (Modal Queue)**。
*   **架构要求**：来自大模型的指令应当 push 进此队列，排队逐个执行，防止并发导致锁冲突或界面假死。

## 4. API 混合调用策略 (Hybrid API Strategy)
UXP 目前提供两套 API 来控制 Photoshop：
1. **DOM API v2**（如 `app.activeDocument.layers`）：具备对象化封装、类型支持（TS 友好）、语法易读。
2. **batchPlay**（ActionJSON）：通过底层描述符直接操作，语法晦涩（常由 Alchemist 生成），但覆盖率高达 99%。

*   **铁律**：在封装工具（Tools）或开发新业务时，**必须优先使用 DOM API v2**。
*   **规范**：只有当明确确认 DOM API v2 缺失该功能或性能无法满足需求时，才允许降级使用 `batchPlay` 进行兜底开发。使用 `batchPlay` 时，应将其封装在具有清晰类型声明（TypeScript）的独立函数中，并添加注释说明降级原因。
