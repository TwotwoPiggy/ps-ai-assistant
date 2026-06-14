---
phase: 07-automation-actions
plan: 07
type: implementation
wave: 1
depends_on: [06]
files_modified: [backend/tools/ps_tools.py, backend/tools/registry.py, backend/agent.py, tests/test_phase07_automation.py]
autonomous: true
requirements: [AUTO-01, AUTO-02, AUTO-03]
---

# Phase 07 Plan: 自动化与动作集成 (Automation & Actions)

## Goal
支持直接调用录制动作 (Actions)、执行本地扩展脚本 (JSX) 以及自动切片导出 API，增强 PS AI 助手的批处理与工作流自动化能力。

## Threat Model
<threat_model>
### 1. 任意代码执行 (RCE)
- **威胁**: 恶意用户或提示词通过请求执行敏感路径下的外部 JSX 脚本，读取或破坏系统数据。
- **缓解措施**: 实现 `execute_local_jsx` 函数。脚本路径必须在 `backend/resources/scripts/` 白名单下。若属于其他绝对路径，则拦截并产生受控状态，要求前端二次询问用户获取明确的 Allow 授权。

### 2. 导出路径遍历攻击
- **威胁**: 切片导出时指定恶意相对或绝对路径，覆盖重要系统文件。
- **缓解措施**: 如果前端指定了导出绝对路径，通过 `os.path.abspath` 与白名单目录校验；如果前端未指定，强制回退至用户桌面或安全缓存区（如 `os.path.expanduser("~/Desktop")`）。
</threat_model>

## Tasks

### Wave 0 — Test Setup & Validation Infrastructure
#### Task 07-01-01: 创建 Phase 07 自动化测试框架与存根
- **read_first**:
  - `.planning/phases/07-automation-actions/07-VALIDATION.md`
- **action**:
  - 创建 `tests/test_phase07_automation.py`，包含 3 个需求 (AUTO-01, AUTO-02, AUTO-03) 的 mock/存根测试。
- **verify**: `pytest tests/test_phase07_automation.py`

### Wave 1 — Implementation
#### Task 07-01-02: 实现动作录制调用 API (`play_action`)
- **read_first**:
  - `backend/tools/ps_tools.py`
  - `backend/agent.py`
- **action**:
  - 在 `ps_tools.py` 中编写 `play_action(action_name, action_set_name)`。
  - 使用 ActionManager (DoAction 描述符) 实现播放动作。
  - **重要**: 为避免带有阻塞性交互的动作（如调色弹窗）导致假死，采用**状态指引 + 允许挂起**模式（决策 D-02）。即：向前端注入状态提示（参考之前的液化滤镜），不强制使用 `DialogModes.NO`，允许原生对话框弹出供用户干预。
- **verify**: 补充对应 Action API 的单元测试断言。

#### Task 07-01-03: 实现本地脚本执行 API (`execute_local_jsx`)
- **read_first**:
  - `backend/tools/ps_tools.py`
- **action**:
  - 实现 `execute_local_jsx(script_path, user_confirmed=False)`。
  - **安全逻辑 (D-01)**：若 `script_path` 不在 `backend/resources/scripts/` 白名单内，且 `user_confirmed` 为 `False`，返回明确的中断错误给大模型：“执行外部脚本有风险，请先询问用户是否允许执行此路径”。并要求模型下次调用时带上 `user_confirmed=True`。
  - 若验证通过，读取文件并传入现有的 `execute_jsx` 引擎中。
- **verify**: 测试白名单内无感通过、白名单外被拦截。

#### Task 07-01-04: 实现 Web 导出 API (`export_for_web`)
- **read_first**:
  - `backend/tools/ps_tools.py`
- **action**:
  - 实现 `export_for_web(format="PNG-24", export_path="")`。
  - **默认预设 (D-03)**：若未提供参数，默认输出到系统桌面。导出时组装 JSX 脚本执行 `ExportDocument` 与 `ExportOptionsSaveForWeb`。
  - **避坑**: 注意如果文档宽度超过 8192px 可能会触发 SaveForWeb 的内部限制，需捕获并抛出清晰错误。
  - 在 Python 侧向大模型返回成功导出的完整绝对路径。
- **verify**: 测试默认导出配置时返回正确的桌面路径，并能够创建测试空文件。

#### Task 07-01-05: 注册新增工具并配置 Agent 提示词
- **read_first**:
  - `backend/tools/registry.py`
  - `backend/agent.py`
- **action**:
  - 在 `registry.py` 中注册 `play_action`, `execute_local_jsx`, `export_for_web`。
  - 在 `agent.py` 的 `interactive_tools` 或相似管控列表中注册 `play_action` 和 `execute_local_jsx`（当其涉及授权弹窗时），保证前端 UX 的一致性。
- **verify**: 全局工具链测试全部加载无误。

## Verification Plan
1. **自动化**: 运行 `pytest` 全量通过。
2. **交互性验证**: 运行前端 UI，发口令 "运行一个叫'黑白胶片'的动作"，观察界面是否有 "请在 PS 内完成操作" 的弹窗提示。
3. **安全性验证**: 试图执行 "C:\Windows\System32\malicious.jsx"，确认其能抛出报错并弹出安全询问。
4. **功能性验证**: 发口令 "帮我把这张图导出成网页切片"，检查桌面是否生成相应的图片并确认大模型给出了反馈。
