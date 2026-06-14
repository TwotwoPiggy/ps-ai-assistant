---
phase: 01-架构与接口重构
plan: 01
subsystem: api
tags: [openai, gemini-sdk, python, refactoring, security]

# Dependency graph
requires: []
provides:
  - BaseProvider abstraction for multiple AI LLM backends
  - OpenAICompatProvider for DeepSeek, Qwen, MiMo and custom compatibility
  - GeminiProvider wrapper for native Google GenAI SDK
  - PhotoshopContext sharing state across pure functions and agent
  - ToolRegistry dynamically generating tool schemas and executing tools
  - Secure API configuration endpoint with API key masking
affects:
  - frontend UI configuration panel
  - backend server session management

# Tech tracking
tech-stack:
  added: [openai>=2.41.1]
  patterns: [Adapter Pattern, Strategy Pattern, Command/Pure-Function Registry]

key-files:
  created:
    - backend/tools/ps_tools.py
    - backend/tools/schema.py
    - backend/tools/registry.py
    - backend/tools/__init__.py
    - backend/providers/base.py
    - backend/providers/gemini.py
    - backend/providers/openai_compat.py
    - backend/providers/registry.py
    - backend/providers/__init__.py
  modified:
    - backend/requirements.txt
    - backend/config.py
    - backend/agent.py
    - backend/server.py

key-decisions:
  - "统一内部使用 OpenAI Chat Completion 格式的消息与工具参数，简化 Provider 各自的对接逻辑。"
  - "对 API Key 在网络传输中进行掩码脱敏 (mask)，保护敏感隐私；同时在保存时若收到掩码格式则忽略，防覆写已配置数据。"

patterns-established:
  - "Pattern 1: 纯函数工具解耦，利用 Context 跨线程传递共享 Photoshop COM 对象状态。"
  - "Pattern 2: 自动生成 JSON Schema，省去手动编写大块工具定义的时间和错误率。"

requirements-completed: []

# Metrics
duration: 45min
completed: 2026-06-12
---

# Phase 1 Plan 1: 架构与接口重构 Summary

**实现统一的 BaseProvider 接口抽象，解耦并迁移 11 个 Photoshop 工具为纯函数并自动生成 Schema，支持安全脱敏的 API 配置管理。**

## Performance

- **Duration:** 45 min
- **Started:** 2026-06-12T22:22:15Z
- **Completed:** 2026-06-12T23:07:00Z
- **Tasks:** 5
- **Files modified:** 13

## Accomplishments
- **多提供商适配器模式落地**：建立 `BaseProvider` 类，通过 `GeminiProvider` 保留高性能原生 Google SDK 交互，通过 `OpenAICompatProvider` 覆盖 DeepSeek、通义千问等所有兼容 OpenAI 规范的平台，且内置多模态视觉降级保护。
- **Photoshop COM 工具集轻量化解耦**：将原 `PhotoshopAgent` 类中的 11 个特定 COM 操作方法剥离到 `ps_tools.py` 纯函数中，基于 `PhotoshopContext` 维护线程状态。
- **自动工具 Schema 生成器**：设计 `schema.py` 借助 Python 内置的 `inspect` 和类型提示，自动从纯函数的 docstring 和参数中生成符合 OpenAPI 规范的 tools JSON 描述，确保高一致性与极简维护。
- **核心代理重构为瘦协调层**：将原先臃肿的 `PhotoshopAgent` 重构为简单的对话生命周期控制器，集中式维护 OpenAI 会话格式，并通过 `ToolRegistry` 分发操作。
- **隐私掩码与安全落盘**：对 API Key 信息通过 `server.py` 实现掩码脱敏（如 `gemi****2345`），避免抓包与日志明文泄露，并自动防范无改动提交时的 Key 被覆盖清空。

## Task Commits

Each task was committed atomically:

1. **Task 1: Requirements and Config Refactoring** - `1805d44` & `f67d5e4` (build/feat)
2. **Task 2: PS Tools Decoupling and Schema Generator** - `07f3f59` (feat)
3. **Task 3: BaseProvider & Adapter implementation** - `ce4982c` (feat)
4. **Task 4: PhotoshopAgent Slim Orchestrator** - `cb43915` (refactor)
5. **Task 5: Server config routing and masking** - `089dc8f` (feat)

**Plan metadata:** `pending_commit` (docs: complete Phase 1 Plan 1 summary)

## Files Created/Modified
- `backend/requirements.txt` - 添加 openai>=2.41.1 依赖。
- `backend/config.py` - 多 Provider 新配置格式设计，向下兼容旧版 key/model 升级迁移。
- `backend/tools/ps_tools.py` - 将 11 个 Photoshop 操作（如 get_layer_tree、crop_canvas）改造成接收 context 的纯函数。
- `backend/tools/schema.py` - 提取纯函数说明及形参类型映射成规范的 OpenAI tools JSON schema。
- `backend/tools/registry.py` - 管理纯函数工具的批量注册与统一异常捕获执行入口。
- `backend/providers/base.py` - 规定所有 Provider 的统一 `chat` 格式和视觉标志。
- `backend/providers/gemini.py` - 接入 Google 原生 Client 并进行格式互转。
- `backend/providers/openai_compat.py` - 标准 OpenAI 适配器，包含无视觉模型自动过滤图片占位符降级。
- `backend/providers/registry.py` - 依据全局配置工厂化派生不同的适配器实例。
- `backend/agent.py` - 清空全部工具方法，重构为基于 list[dict] 和 Provider/Tool 注册表的轻巧代理。
- `backend/server.py` - 拦截 `ai_config` 获取与保存事件，对密钥脱敏并实现安全的合并保存。

## Decisions Made
- 统一使用标准 OpenAI 格式作为全系统内部的消息流与工具描述，最大化减少非必要的数据多态性，由 Provider 各自适配底层。
- 面对不支持 Vision 图像多模态的模型（如 DeepSeek-V3），在 Provider chat 层面做自动降级，剥离 base64 数据为占位文本，提高多提供商部署的可靠性。

## Deviations from Plan
None - plan executed exactly as written.

## Issues Encountered
None - All integration tests and server dry-runs passed on first try.

## User Setup Required
None - no external service configuration required (will use local store).

## Next Phase Readiness
- 核心后端服务架构重构圆满完成，支持随时接入不同平台。
- 准备好进入 Phase 2 进行前端 UI 的改版，使其拥有切换 Provider 并为各 Provider 单独输入 API Key / Base URL / 模型的表单。

---
*Phase: 01-架构与接口重构*
*Completed: 2026-06-12*
