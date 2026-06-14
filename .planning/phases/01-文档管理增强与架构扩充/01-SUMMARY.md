---
phase: 01-文档管理增强与架构扩充
plan: 01
subsystem: api
tags: [python, pywin32, win32com, photoshop-com]

# Dependency graph
requires:
  - phase: v1.1-phases/04-infrastructure-setup
    provides: 双引擎适配器模式与 JSX/DoJavaScript 通道
provides:
  - 8 个新增 Photoshop 文档管理和底层 JSX 执行工具函数
  - PhotoshopContext 类支持 get_app 获取 app 应用实例
affects: [02-图层进阶操作补全, 03-AI 认知升级与集成测试]

# Tech tracking
tech-stack:
  added: [pywin32]
  patterns: [COM DoJavaScript 注入执行, app 与 doc 层级解耦]

key-files:
  created: []
  modified: [backend/tools/ps_tools.py, backend/tools/registry.py]

key-decisions:
  - "在 PhotoshopContext 中抽取 get_app 隔离文档级与应用级操作"
  - "利用 DoJavaScript 在 Python COM 接口中直接运行 JSX ExtendScript，绕过 DOM 层次限制"
  - "为 change_color_mode 加设强制允许确认的铁律，在模式转换前拦截弹窗并需要聊天提示确认"
  - "对于 save_document 在无物理文件名情况下自动以时间戳回退保存至用户的系统桌面"

patterns-established:
  - "DoJavaScript 注入执行模式"
  - "应用级与文档级 API 独立调用策略"

requirements-completed: [DOC-01, DOC-02, DOC-03, DOC-04, DOC-05, DOC-06, DOC-07, ARC-01]

# Metrics
duration: 15min
completed: 2026-06-13
---

# Phase 1: 文档管理增强与架构扩充 Summary

**在 ps_tools 中成功改造并引入了 8 个全新的文档与视图管理 COM 工具，底层原生支持 DoJavaScript 注入，并在 registry 中全量注册**

## Performance

- **Duration:** 15 min
- **Started:** 2026-06-13T10:13:41Z
- **Completed:** 2026-06-13T10:15:15Z
- **Tasks:** 7
- **Files modified:** 2

## Accomplishments
- 成功解耦 `PhotoshopContext` 得到 `get_app()` 接口，现在能够在没有打开文档的情况下支持各种应用级和文档级初始化操作。
- 实现了通用的 `execute_jsx()` 脚本注入通道，支持使用 `DoJavaScript` 运行任意 ActionManager/JavaScript 语句。
- 补全了 `create_document`, `open_and_place` 等应用级操作，确保其在无文档时也能稳定调用不抛异常。
- 为 `save_document` 制定了优雅的物理路径及桌面 PSD 回退兜底规则，防止未存盘文档丢失。
- 实现了 `resize_image` 与 `change_color_mode`，且针对色彩模式转换添加了警告框自动屏蔽（`DisplayDialogs = 3`）以及聊天强制允许校验机制。
- 通过 JSX/ActionManager 完成了 `history_control` (撤销) 和 `zoom_view` (视图实际像素及自适应)。
- In `registry.py` 中全量注册了上述 8 项新工具，完成了 OpenAI Schema 自动生成与映射。

## Task Commits

Each task was committed atomically:

1. **Task 1: 改造 PhotoshopContext 添加 get_app 方法** - `e15f518` (feat)
2. **Task 2: 实现 execute_jsx 底层脚本执行支持 (ARC-01)** - `bd2a347` (feat)
3. **Task 3: 实现 create_document 和 open_and_place 工具 (DOC-01, DOC-02)** - `b7eecd1` (feat)
4. **Task 4: 实现 save_document 默认路径规则 (DOC-03)** - `4d43cfa` (feat)
5. **Task 5: 实现 resize_image 和 change_color_mode (DOC-04, DOC-05)** - `f12a56f` (feat)
6. **Task 6: 使用 ActionManager/JSX 实现 history_control 与 zoom_view (DOC-06, DOC-07)** - `9748c48` (feat)
7. **Task 7: 注册 8 个新工具** - `74a88c3` (feat)

## Files Created/Modified
- [backend/tools/ps_tools.py](file:///d:/Computers/AIDevelop/Tools/Photos/ps-ai-assistant/backend/tools/ps_tools.py) - 实现了 get_app 方法、execute_jsx 以及 7 个核心文档和视图操作工具函数。
- [backend/tools/registry.py](file:///d:/Computers/AIDevelop/Tools/Photos/ps-ai-assistant/backend/tools/registry.py) - 补充注册了 8 项新工具，增加了全局可用 tools 数量。

## Decisions Made
- 统一将 JSX 脚本在执行前通过 `logger.debug` 进行打印，便于控制台调试与跟踪注入代码。
- 色彩模式转换可能弹出警告框导致 Windows COM 挂起，故执行前强制设置 `DisplayDialogs = 3` 屏蔽，并依靠 docstring 契约强化大模型在前端的人机交互确认流程。

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- 8 个文档视图类基础 API 已经全部通过静态验证 and 注册，可以在后端正确暴露。
- 架构已能够无缝支持 JSX 的混合注入。
- 已经准备好进入 **Phase 2: 图层进阶操作补全**，开发所有针对图层和图层组的高级操控、合并等接口。
