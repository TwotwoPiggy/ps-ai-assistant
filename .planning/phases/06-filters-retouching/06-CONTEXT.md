# Phase 06: 高级滤镜与人像美化 (Filters & Retouching) - Context

**Gathered:** 2026-06-14
**Status:** Ready for planning

<domain>
## Phase Boundary

本阶段（Phase 06）目标是实现常见模糊与锐化滤镜、液化形体处理、Camera Raw 滤镜预设、神经元滤镜触发、商业磨皮宏脚本，以及生成式填充 (Generative Fill) API 的高级滤镜与人像美化能力。

</domain>

<decisions>
## Implementation Decisions

### 1. 滤镜参数与自适应策略 (Filter Parameters & Adaptation)
- **D-01 (滤镜参数控制与默认值)**：API 暴露完整细分参数并标记为可选。大模型根据用户口令强弱动态计算具体数值（如“稍微模糊” vs “强模糊”），缺省时使用安全默认值（如高斯模糊半径 5.0 像素）。
- **D-02 (分辨率自适应)**：后端磨皮等滤镜半径根据文档分辨率/画布尺寸动态等比缩放换算。大模型仍可传入可选的 `custom_radius` 显式覆盖。
- **D-03 (滤镜选区边界)**：滤镜默认局限在活动选区内应用。但 API 提供可选的 `clear_selection` 参数，若大模型判断是全局滤镜且存在非预期选区，可清空选区，减少 Tool 交互往返。

### 2. 修图流程与安全性保护 (Retouching Safety & Layer Protection)
- **D-04 (商业磨皮安全机制)**：为保证图层安全，自动执行静默新建备份图层（复制当前图层为 `[原图层名]_磨皮`）或检测如果是智能对象则直接应用智能滤镜。无需前置频繁反问确认。
- **D-05 (Camera Raw 安全保护)**：应用 Camera Raw 滤镜前，若图层为普通像素图层，后端自动将其转换为“智能对象” (Smart Object)，以保证滤镜作为可反复双击调整的“智能滤镜”挂载，实现无损修图流程。

### 3. AI 生成式与智能滤镜接口 (Generative & Intelligent Filters)
- **D-06 (生成式填充选区防御)**：无选区时强行拦截并报错，引导用户用选区工具进行选取或用 AI “选择主体”框选后再触发填充。
- **D-07 (生成式填充提示词优化)**：大模型自动将用户的中文提示词翻译为英文，并进行适当的 Prompt 扩充（Prompt Expansion）修饰，以提升 PS 侧生成的精细度与环境契合度。
- **D-08 (生成式填充变体交互)**：只在 PS 侧生成图层，不尝试在 Web 界面提取或切换变体，完全交由用户在 PS 原生面板中挑选变体。Web 侧进行友好文案引导。
- **D-09 (Camera Raw 预设文件加载)**：支持传入外部自定义 `.xmp` 预设绝对路径，也支持内置默认常用预置（如胶片、日系清新等），若路径为空则默认映射到内置路径。
- **D-10 (神经元滤镜参数与降级)**：支持传递非结构化的 `parameters` 参数字典实现细分微调，若神经元滤镜在本地未激活或报错，在 Python 侧以 `try...catch` 严格捕捉异常，并由大模型优雅引导降级到传统磨皮或滤镜流程。

### the agent's Discretion
- 滤镜（高斯模糊/USM锐化）的默认参数取值、具体翻译的提示词扩充格式规范、磨皮比例缩放系数细节均由 AI 根据最佳技术实践进行自由裁量。

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

- [ps_tools.py](file:///D:/Computers/AIDevelop/Tools/Photos/ps-ai-assistant/backend/tools/ps_tools.py) — 核心 Photoshop COM 函数库与执行上下文定义
- [REQUIREMENTS.md](file:///D:/Computers/AIDevelop/Tools/Photos/ps-ai-assistant/.planning/REQUIREMENTS.md) — 项目核心功能需求 Traceability
- [PROJECT.md](file:///D:/Computers/AIDevelop/Tools/Photos/ps-ai-assistant/.planning/PROJECT.md) — 整个项目的架构背景与技术约束

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `PhotoshopContext`: 提供对 win32com `Photoshop.Application` 的调用与 `resolve_layer()` 的路径映射，用以定位活动图层。
- `execute_jsx()`: JSX 注入管道。在底层复用该方法，通过 ActionManager 触发复杂的滤镜动作（包括液化和 Neural Filters 的执行）。

### Established Patterns
- 复用 COM 异常捕获机制，将任何底层报错通过 `PhotoshopContext` 包装并返回语义化错误。
- 遵循 `DoJavaScript` 管道，所有涉及高级或底层 ActionManager 的复杂滤镜功能通过 JSX 安全串行运行。

### Integration Points
- 所有新增的高级滤镜、磨皮、ACR 预设应用以及生成式填充等工具都必须注册在 `backend/tools/ps_tools.py` 内部，并通过 `backend/tools/registry.py` 添加到工具注册表。

</code_context>

<specifics>
## Specific Ideas
- 商业磨皮（高反差保留 + 表面模糊）的图层操作可以采用图层组或命名为 `[原图层名]_磨皮` 的新图层挂载，并在磨皮宏脚本中引入不透明度选项以实现强度调整。

</specifics>

<deferred>
## Deferred Ideas
- 暂无 deferred ideas — 本次讨论的所有重点决策均完美契合 Phase 06 的范围。

</deferred>

---

*Phase: 06-filters-retouching*
*Context gathered: 2026-06-14*
