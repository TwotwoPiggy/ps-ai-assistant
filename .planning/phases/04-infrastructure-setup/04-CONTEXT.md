# Phase 4 Context

## Domain
构建 UXP 插件的底层基础脚手架，实现与后端的双向通信，并建立统一的模态操作队列以防止界面阻塞。

## Decisions Captured
### UXP 骨架定位与架构
- **一步到位引入 React (多端共存)**: 经过重新讨论，用户决定一步到位在 UXP 中引入 React。由于现存有一个运行在浏览器中的 React 前端，我们将采用**多端共存**策略：为 UXP 新建一个入口点并配置专属的打包构建（如 Vite/Webpack），使其能复用现有的大部分 React UI 组件。
- **双引擎共存策略 (Adapter Pattern)**: 为兼容现有架构，决定采用策略/适配器模式。现有的 `pywin32` 封装为 `COMEngine`，本次脚手架作为 `UXPEngine` 的端点。大模型输出的 Function Calling 数据不感知底层差异，通过抽象引擎层自动路由。
- **通信与职责**: UXP 面板此时具有双重身份。一方面，它是用户的聊天界面（通过后端与大模型通信）；另一方面，它是底层的代码执行器（接收后端传回的操作指令并通过 `executeAsModal` 执行）。
- **技术选型**: 需要配置 Vite/Webpack 等构建工具，并处理 UXP 沙盒环境的特有报错（如缺少 Node 环境或特定的 Polyfill）。

## Canonical References
None

## Code Context
- 本阶段代码为独立的原生 JS UXP 插件脚手架，与现有的 React 项目解耦，不会对现有系统的架构造成破坏。
