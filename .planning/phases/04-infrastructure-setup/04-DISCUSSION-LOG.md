# Phase 4 Discussion Log

**Area:** UXP 脚手架架构
**Question:** 倾向于纯原生 JS 还是直接引入 React + Vite？
**User Selection:** 实话, 我目前不太需要插件, 我只是想先研究和整理uxp支持的所有操作有哪些
**Notes:** 用户的这一回答极大地改变了本阶段的实施重点。UXP 脚手架的定位从“下一代插件产品形态”降级为“用于研究 API 边界的测试执行容器 (Testbed)”。一切基础设施搭建均应以最轻量、最快跑通测试脚本为唯一目的。

---

**Area:** UXP 脚手架架构（重新讨论）
**Question:** 如何处理现有的前端代码？是否要在 UXP 中引入 React？
**User Selection:** [多端共存] 外部浏览器界面依然可用，同时构建一个全新的 UXP 版本入口，两者复用底层的 React UI 组件。
**Notes:** 重新讨论后，用户决定推翻之前的极简测试容器方案，改为“一步到位”在 UXP 中引入 React。但这并非完全抛弃旧前端，而是采用多端共存架构。因此，Phase 4 必须解决 Vite/Webpack 等现代构建工具在 UXP 沙盒环境下的打包与兼容问题。
