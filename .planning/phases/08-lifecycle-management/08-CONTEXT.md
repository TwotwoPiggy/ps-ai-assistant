# Phase 08 Context: 客户端生命周期管理 (Lifecycle Management)

## Domain
为应用提供一键式的独立安装、平滑更新与干净的卸载流程。

## Canonical Refs
- ROADMAP.md

## Code Context
- 后端 Python (fastapi/socketio)，前端 React (vite)。需要兼顾双端环境的配置。

## Decisions

### 运行环境部署
- **决策**: 编写 bat/ps1 安装脚本，自动为用户安装 Python/Node 并拉取依赖（保持源码结构，利于后续热更新代码）。

### 版本更新机制
- **决策**: 在 Web UI 面板中增加“检查更新”按钮，点击后由后端触发更新流。

### 卸载数据保留
- **决策**: 彻底清理所有内容（包括配置文件、API Key 等），不留残余。

### 快捷方式放置
- **决策**: 仅在桌面生成快捷方式。

## Deferred Ideas
无
