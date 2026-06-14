# Phase 3: 前端配置面板改造 - Plan

**Status:** Ready to execute
**Created:** 2026-06-12

## Tasks

### 1. 前端配置面板交互改造
- [ ] 在 `frontend/src/ChatPanel.tsx` 中引入多提供商的状态结构：
  - 维护 `currentProvider` 字符串状态。
  - 维护 `providers` 状态对象，保存所有提供商对应的表单属性：
    ```typescript
    interface ProviderConfig {
        api_key: string;
        base_url: string;
        model: string;
    }
    ```
- [ ] 改造 `useEffect` 配置拉取逻辑：反序列化后端返回的配置，分发到 `providers` 状态。
- [ ] 重构配置面板配置区域的 HTML 布局：
  - 提供 `currentProvider` 下拉选择框。
  - 提供 API Key 密码输入框，绑定 `onFocus` 自动清空掩码逻辑。
  - 动态渲染 `base_url`（仅 Custom 与 MiMo 专属）。
  - 根据选中的提供商，动态显示对应的预置模型下拉选择菜单（或 Custom 时的文本输入框）。
- [ ] 改造配置保存逻辑，向后端发送新结构的保存荷载。

### 2. 流式思维链 (Thinking Process) 的监听与渲染
- [ ] 在 `frontend/src/ChatPanel.tsx` 的 `useEffect` 中监听 `ai_chat_thinking` 流式 WebSocket 事件，并将实时累积的字符动态追加到 `currentThinking` 状态中。
- [ ] 在 `handleSend` 方法中，清空旧的 `currentThinking` 缓存。
- [ ] 在 `handleResponse` 回调中，将当前累积的 `currentThinking` 永久存入新生成的 Assistant 消息对象的 `thinkingText` 属性。
- [ ] 构建独立的可折叠 `<ThinkingBox>` 组件：
  - 接收 `text`，默认为展开状态。
  - 包含折叠状态的 toggle 点击切换，支持折叠图标（▴/▾）过渡。
- [ ] 在消息渲染区，若 Assistant 消息含有 `thinkingText` 或正在生成时 `currentThinking` 不为空，在气泡最上方渲染该折叠面板。

### 3. Vanilla CSS 样式润色
- [ ] 在 `frontend/src/styles.css` 中为新表单组件及输入框编写现代化的 Vanilla CSS 样式。
- [ ] 为可折叠思维链面板设计半透明或微虚线浅灰边框背景，使其与对话气泡有明显的质感和层次区隔。
- [ ] 添加手风琴折叠展开平滑的 CSS 过渡与动画。

## Verification Plan

### Automated Verification
- 运行前端项目的编译 `npm run build`（在 `frontend` 目录下），验证 TypeScript 检查与静态打包是否能够 100% 无错通过。

### Manual Verification
1. 打开浏览器控制面板，进入 Photoshop 扩展面板。
2. 展开配置框，验证是否可通过下拉框自由切换 5 家不同的 AI 提供商，且表单字段（如 `base_url`）能按需显隐。
3. 点击已配置的 Provider 密钥输入框，聚焦时验证掩码（如 `gemi****2345`）是否自动清空供再次录入；若直接移开，应自动恢复为脱敏格式。
4. 切换为 DeepSeek 渠道，并选择 `deepseek-reasoner` (R1) 开展聊天，验证在响应生成时是否有折叠面板展示流式的思考词，且完成时思考链是否依然驻留且可点击折叠/展开。
