# UXP Operations Research Stack

## 概述
本文档定义了为在现有应用中开展 "Photoshop UXP 操作研究"（里程碑 v1.1）所需引入的技术栈、开发工具以及相关约束。本次研究旨在探索 UXP 支持的图层、画布及文档等操作边界，现有的 Python COM 及大模型对接方案保持不变。

## 开发工具 (新增)

*   **Adobe UXP Developer Tool (UDT)**
    *   **版本:** 最新版 (通过 Adobe Creative Cloud 桌面端管理和更新)
    *   **Rationale (原因):** 官方提供的桌面端调试工具，是在 Photoshop 中加载、调试和热重载 UXP 测试插件的必备环境。
    *   **集成点:** 作为独立桌面应用运行，通过 UDT 直接将本地测试代码注入到 Photoshop 实例中。

*   **Alchemist 插件 (`jardicc/alchemist`)**
    *   **版本:** 开发者版本 (v2.5.0 或以上)
    *   **Rationale (原因):** UXP 操作研究阶段 **最核心** 的工具。它可以直接拦截 Photoshop 的 Action Manager (AM) 事件，审查内部 DOM 结构，并自动转换为对应的 `batchPlay` 代码。
    *   **注意:** 必须从 GitHub 仓库下载其源码（开发者版本）。由于 Adobe 的安全策略，插件市场的发行版限制了事件监听能力。

## 依赖库与框架 (新增)

*   **`@types/photoshop`**
    *   **版本:** `^25.0.4`
    *   **Rationale (原因):** 提供 Photoshop UXP API (`require('photoshop')`) 的 TypeScript 类型定义。这对于在 VSCode 等 IDE 中实现代码补全和探索 API 边界至关重要。
    *   **集成点:** 仅作为研究用 UXP 测试项目的 `devDependencies` 引入，不影响现有 Python 主应用的代码。

## 架构与集成考量

*   **沙箱测试环境:** 本次操作研究将在独立的 UXP 插件沙箱中进行，以验证各种图像和图层处理 API 的能力，代码不会直接合入当前的 Python 主服务。
*   **通信接口预研:** 考虑到现有架构基于 FastAPI + Socket.IO 实现，UXP 插件未来需要能与本地 Python 后端进行双向通信。研究阶段可直接利用 UXP 原生支持的 `WebSocket` API 或 `fetch` API 来验证通信可行性，而无需引入额外的第三方 npm 包（如 socket.io-client，避免引入浏览器特定依赖导致的兼容性问题）。

## 禁忌清单 (What NOT to Add)

*   **🚫 切勿引入 Node.js 核心模块 (如 `fs`, `path`, `os`):** UXP 运行在 V8 引擎上，但 **并非 Node.js 环境**。它有自己独立的安全沙箱和文件系统 (`require('uxp').storage`)。试图引入或 Polyfill Node.js 原生模块会导致不可预知的错误。
*   **🚫 切勿在当前阶段修改现有 `pywin32` 逻辑:** 本里程碑的目标是 **纯粹的 UXP API (DOM & batchPlay) 能力调研**。不要为了扩展新功能而在 Python 后端强行添加新的 COM 接口依赖，保持现有的 COM 方案（v1.0）稳定运行。
*   **🚫 切勿引入重型前端 UI 框架:** 既然目标是“操作研究”，测试插件的 UI 应该保持极简（原生 JS/HTML 即可）。禁止为了测试零碎的 `batchPlay` 脚本而引入庞大的框架或组件库（如完整配置 Spectrum Web Components），以减少调试过程中的干扰变量。
