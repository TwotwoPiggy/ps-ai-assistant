---
wave: 2
depends_on:
  - 01-IMPLEMENTATION-PLAN.md
files_modified:
  - tests/test_05_capabilities.py
autonomous: true
---

# Phase 5: 验证核心功能与事件机制 - Testing

## Goal
执行 11 个核心操作在 DOM 和 batchPlay 两种实现下的自动化测试验证，收集成功率、报错信息及性能表现，用于后续输出评估报告。

## requirements
CAP-02

## must_haves
- 必须实际触发并验证所有 11 个工具的 DOM 和 batchPlay 双版本执行情况
- 记录执行成功与否、错误内容，以供 Phase 6 参考

## Tasks

### [ ] Task 1: 编写并执行自动化能力验证脚本
**requirements**: CAP-02

<read_first>
- backend/server.py
- frontend/src/uxpTools.ts
</read_first>

<action>
1. 在项目根目录或 `tests` 目录下创建验证脚本 `tests/test_05_capabilities.py`。
2. 脚本需作为 Socket.IO 客户端（可使用 `python-socketio`）连接至本地运行的后端服务器（默认端口 18919）。
3. 向后端发送（或通过 REST 接口/内部调用触发）针对所有 11 个工具的测试请求，每个工具分别测试 `_use_batchplay: false` 和 `_use_batchplay: true`。
4. 由于需要真实 Photoshop 环境响应，测试脚本需在确保 Photoshop 已打开文档且 UXP 插件已连接的前提下执行。
5. 脚本需将各个调用的返回结果（成功与否、错误信息）记录到一个临时 JSON 文件 `tests/capability_results.json`，供报告生成任务使用。
</action>

<acceptance_criteria>
- `tests/test_05_capabilities.py` 脚本被成功创建。
- 运行脚本 `python tests/test_05_capabilities.py` 后，在有 PS 客户端配合的情况下，成功输出包含 22 个测试用例结果（11工具 * 2模式）的 `tests/capability_results.json` 文件。
- 收集到的 JSON 文件内字段需清晰标明工具名称、模式以及 success 状态。
</acceptance_criteria>
