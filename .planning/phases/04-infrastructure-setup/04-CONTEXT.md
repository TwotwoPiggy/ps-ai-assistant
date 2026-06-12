# Phase 4 Context

## Domain
构建 UXP 插件的底层基础脚手架，实现与后端的双向通信，并建立统一的模态操作队列以防止界面阻塞。

## Decisions Captured
### UXP 骨架定位与架构
- **纯粹的测试与研究载体**: 用户明确表示当前不需要发布真正的插件，核心诉求是“研究和整理 UXP 支持的所有操作”。因此，Phase 4 搭建的脚手架不包含任何生产级的产品 UI。
- **双引擎共存策略 (Adapter Pattern)**: 为兼容现有架构，决定采用策略/适配器模式。现有的 `pywin32` 封装为 `COMEngine`，本次脚手架作为 `UXPEngine` 的端点。大模型输出的 Function Calling 数据不感知底层差异，通过抽象引擎层自动路由。
- **技术选型**: 采用最轻量的纯原生 JS (Vanilla JS) 搭建。无需引入 React，无需配置复杂的 Vite/Webpack 打包。现存的 React 聊天面板保留在浏览器外运行即可。
- **最小化通信**: WebSocket (Socket.IO) 与后端的通信仅为了满足自动化测试脚本派发与结果收集，不追求生产级的复杂容错处理。
- **UI 呈现**: 插件面板仅保留最低限度的测试执行按钮和日志输出区即可。

## Canonical References
None

## Code Context
- 本阶段代码为独立的原生 JS UXP 插件脚手架，与现有的 React 项目解耦，不会对现有系统的架构造成破坏。
