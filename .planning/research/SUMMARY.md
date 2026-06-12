# 摘要：Photoshop AI 助手架构演进与 UXP 研究总结

> 自动生成自 `STACK.md`, `FEATURES.md`, `ARCHITECTURE.md`, `PITFALLS.md` 综合研究报告。

## 1. 核心目标与方向
本次研究聚焦于 Photoshop AI 助手的下一代架构演进（里程碑 v1.1），核心目标包括：
1. **多模型能力整合**：引入基于 OpenAI 兼容的 Function Calling 标准格式，评估并适配 Qwen、MiMo、DeepSeek 等大模型，突破当前对单一 Gemini 模型的依赖。
2. **底层执行引擎重构 (UXP 迁移)**：探索并逐步使用现代化的 UXP (Unified Extensibility Platform) 架构取代传统受限于 Windows 平台的 Python COM (`pywin32`) 接口，从而实现跨平台支持（Windows & macOS）、内嵌面板的沉浸式体验以及更快速稳定的异步事件处理。

## 2. 大模型与 Function Calling 策略
- **多提供商能力评估**：
  - **Qwen (通义千问) / MiMo**：能够完美支持视觉多模态输入与工具调用的同时处理（如 Qwen-VL 系列），是本项目实现截图分析与复杂函数调用的最佳选择。
  - **DeepSeek (V3/R1)**：逻辑推理能力极强，但主力模型原生不支持图片与工具调用的混合输入。若使用需引入视觉分析模型作降级预处理。
- **实施方案**：建立统一的消息格式适配器和 Provider 路由器，将现有基于 Gemini 专用 SDK 的逻辑改造为支持 OpenAI JSON Schema 标准。

## 3. UXP 技术栈与架构演进
- **核心开发工具**：
  - **Adobe UDT (UXP Developer Tool)**：用于桌面端的本地调试与热重载。
  - **Alchemist 插件** (开发者版)：用于监听和拦截 Action Manager 事件并逆向生成 `batchPlay` 脚本，是探索高级 API 边界的核心利器。
- **架构与数据流转变**：
  - 执行权限下放：后端的 FastAPI 完全解绑本地进程，转型为纯粹的会话中枢和 AI 网关。
  - 通信方式：利用 UXP 原生支持的 WebSocket 构建 IPC 双向通信。FastAPI 将模型生成的 Tool Call 下发至 UXP 客户端执行并等待回调响应。
- **演进路线图**：采取五阶段迁移策略：脚手架搭建 -> WebSocket 通信打通 -> 核心功能 PoC -> 全量 COM 逻辑替换 -> 最终前端 React UI 嵌入。

## 4. 关键风险与避坑指南 (Pitfalls)
在 UXP 的研发与集成过程中，需重点规避以下技术陷阱：
1. **模态上下文冲突**：文档状态修改必须包裹在 `executeAsModal` 中。需要构建统一的操作队列，严格隔离“只读请求”与“写入操作”，防止 Photoshop 界面无响应。
2. **过度依赖 `batchPlay`**：应当坚持“DOM 优先”原则。难以避免的 `batchPlay` 调用必须被隔离封装，避免代码恶化。
3. **双系统状态不同步**：当 UXP 与原有 COM 接口共存时极易产生竞态冲突。需确立 UXP 为单一真相来源（Single Source of Truth），改用事件驱动推送状态。
4. **沙盒隔离与线程拥堵**：
   - UXP 虽采用 V8 引擎但并非 Node.js，**严禁引入** `fs`/`path` 等系统模块。
   - 避免在 UI 线程执行深度的大图层树递归解析；对于快照抓取，应使用临时文件（`localFileSystem.temporaryFolder`）中转，避免通过 Base64 内存流传递大图导致 UI 卡顿。
5. **Manifest 权限限制**：一切网络访问、文件存取等行为均需在 `manifest.json` 中事先声明，否则在生产打包后将直接失效。
