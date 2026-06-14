# Phase 06 Plan: 高级滤镜与人像美化 (Filters & Retouching)

## Goal
实现模糊与锐化滤镜、液化形体处理、Camera Raw 滤镜预设、神经网络滤镜触发、商业磨皮宏动作以及带选区防御的生成式填充 (Generative Fill) API。

## Threat Model
<threat_model>
### 1. 生成式填充恶意敏感词注入 (Prompt Injection)
- **威胁**: 恶意用户可能通过前端发送敏感/违规关键词的提示词，导致 Adobe Account 封禁。
- **缓解措施**: 在 `apply_generative_fill` API 前置增加简单的关键词过滤，若检测到违法违规英文或中文关键词，直接拦截报错返回。

### 2. 本地文件路径遍历攻击 (Path Traversal)
- **威胁**: `apply_camera_raw_preset` 接收自定义 XMP 路径，如果不加校验可能被遍历读取系统敏感文件。
- **缓解措施**: 在 Python 侧进行路径规范化（`os.path.abspath`），仅允许加载以 `.xmp` 结尾的文件，并在读取前验证其文件结构。

### 3. JSX ExtendScript 任意代码执行
- **威胁**: `execute_jsx` 可以运行任意脚本。
- **缓解措施**: 本接口不直接对前端暴露任意拼接执行，所有 API 函数内的 JSX 脚本均使用参数化占位（如通过 string formatting 替换具体数值），防止拼接注入风险。
</threat_model>

## Files Modified
- `backend/tools/ps_tools.py`
- `backend/tools/registry.py`

## Tasks

### Wave 0 — Infrastructure & Test Setup
#### Task 06-01-01: 创建测试用例与存根 (Stubs)
- **read_first**:
  - `backend/tools/ps_tools.py` (现有接口风格)
  - `.planning/phases/06-filters-retouching/06-VALIDATION.md` (验证映射)
- **action**:
  - 创建测试文件 `tests/test_phase06_filters.py`，实现基本测试套件架构与所有 6 个核心用例的 pytest 存根函数。
- **acceptance_criteria**:
  - `tests/test_phase06_filters.py` 成功创建并包含对 6 个核心功能（模糊锐化、液化、Camera Raw、神经元滤镜、商业磨皮、生成式填充）的测试框架。
  - 运行 `pytest tests/test_phase06_filters.py` 全部用例可通过（或显示 pytest.skip / pending 状态）。

---

### Wave 1 — Basic Filters & Liquify
#### Task 06-01-02: 实现基础模糊与锐化滤镜接口
- **read_first**:
  - `backend/tools/ps_tools.py` (参考 zoom_view 等 JSX 注入执行模式)
  - `.planning/phases/06-filters-retouching/06-CONTEXT.md` (参考决策 D-01, D-03)
- **action**:
  - 在 `backend/tools/ps_tools.py` 中编写 `apply_blur_sharpen` 函数。
  - 参数包含：`filter_type` (gaussian/surface/usm), `radius` (float, 可选), `threshold` (int, 可选), `amount` (float, 可选), `clear_selection` (bool, 默认 False)。
  - 若 `clear_selection` 为 `True`，在执行滤镜前注入 JSX 执行清空选区操作。
  - 对于 `surfaceBlur`，使用 ActionManager JSX 脚本（半径 radius, 阈值 threshold）运行；高斯模糊和 USM 锐化可直接调用 `applyGaussianBlur()` 和 `applyUnsharpMask()`。
- **acceptance_criteria**:
  - `apply_blur_sharpen` 被正确实现并抛出语义化异常。
  - 运行测试 `pytest tests/test_phase06_filters.py -k test_gaussian_blur` 等，高斯模糊、表面模糊及 USM 锐化可运行通过。

#### Task 06-01-03: 实现智能液化滤镜接口 (Face-Aware Liquify)
- **read_first**:
  - `backend/tools/ps_tools.py`
  - `.planning/phases/06-filters-retouching/06-CONTEXT.md` (参考决策 D-05)
- **action**:
  - 在 `backend/tools/ps_tools.py` 中编写 `apply_liquify` 函数。
  - 函数不接收详细面部控制点（遵循区域 5 语义简化设计）。
  - 在应用液化前，自动检测当前图层类型；如果是普通图层 (`doc.ActiveLayer.typename == "ArtLayer"` 且不是 `smartObject`)，则首先调用 `convert_to_smart_object()` 转换，以实现无损滤镜。
  - 注入 JSX 并以 `DialogModes.ALL` 触发 `"LqFy"` (液化命令)，使用户能在弹出液化窗口内交互调整。
- **acceptance_criteria**:
  - `apply_liquify` 正确调用，并能触发智能对象转换。
  - 运行 `pytest tests/test_phase06_filters.py -k test_liquify_smart_object` 断言无损对象成功转型。

---

### Wave 2 — Advanced Retouching & AI
#### Task 06-01-04: 实现 Camera Raw 预设加载与神经元滤镜接口
- **read_first**:
  - `backend/tools/ps_tools.py`
  - `.planning/phases/06-filters-retouching/06-CONTEXT.md` (参考决策 D-05, D-09, D-10)
- **action**:
  - 在 `backend/tools/ps_tools.py` 中实现 `apply_camera_raw_preset`：
    - 参数：`preset_path` (str, 可选，代表 XMP 文件路径)，`show_dialog` (bool, 默认 False)。
    - 若 `preset_path` 为空，自动解析映射到本地 `./backend/resources/presets/film.xmp` (内置胶片风格)。
    - 执行前自动将图层转换为智能对象以实现无损智能滤镜。
    - 读取 XMP 文件纯文本，作为 String 传给 JSX，使用 ActionManager `"Adobe Camera Raw Filter"` 与 `"Sett"` 键进行注入并执行。
  - 实现 `apply_neural_filter`：
    - 参数：`filter_type` (str), `parameters` (dict, 可选)。
    - 注入 JSX 以 `DialogModes.ALL` 唤起 `"neuralFiltersCmd"` 或 `"neuralFilters"` 面板。
    - 在 JSX 和 Python 侧引入 `try...except` 强异常捕捉。若本地环境缺失神经元滤镜抛出错误，返回特定标志以便大模型引导用户降级使用商业磨皮动作。
- **acceptance_criteria**:
  - `apply_camera_raw_preset` 可加载预设并挂载为智能滤镜。
  - `apply_neural_filter` 在环境不可用时优雅捕捉报错。
  - 运行 `pytest tests/test_phase06_filters.py -k test_camera_raw_preset` 等通过。

#### Task 06-01-05: 实现自适应经典商业磨皮动作流接口
- **read_first**:
  - `backend/tools/ps_tools.py`
  - `.planning/phases/06-filters-retouching/06-CONTEXT.md` (参考决策 D-02, D-04)
- **action**:
  - 在 `backend/tools/ps_tools.py` 中编写 `apply_commercial_retouch`：
    - 参数：`opacity` (float, 默认 100.0 代表磨皮图层不透明度)。
    - 在 Python 侧首先获取当前画布的分辨率（DPI）与尺寸基准，以 1920 宽度为基准动态缩放计算高反差半径 (`hpRadius`) 和表面模糊半径 (`sbRadius`) 与阈值。
    - 注入高频/低频分离 JSX：复制图层重命名为 `[原图层名]_磨皮`，设置混合模式为 `LINEARLIGHT`，执行反相，并以此应用高反差保留和表面模糊。
    - 在 JSX 中利用 ActionManager 创建黑色全隐图层蒙版（`HdAl` 模式），默认隐藏磨皮层，供用户后续在 Photoshop 中用白画笔涂抹擦出。
- **acceptance_criteria**:
  - 运行磨皮工具后，图层树多出 `[原图层名]_磨皮` 图层，且图层混合模式为线性光、带黑色蒙版。
  - 运行 `pytest tests/test_phase06_filters.py -k test_commercial_retouch` 断言图层树、混合模式和蒙版存在正确。

#### Task 06-01-06: 实现生成式填充接口与选区强防御
- **read_first**:
  - `backend/tools/ps_tools.py`
  - `.planning/phases/06-filters-retouching/06-CONTEXT.md` (参考决策 D-06, D-07, D-08)
- **action**:
  - 在 `backend/tools/ps_tools.py` 中编写 `apply_generative_fill`：
    - 参数：`prompt` (str, 待填充描述文本，英文)。
    - **选区强防御**：在 JSX 内通过 `doc.selection.bounds` 进行选区校验，若无选区，终止并返回报错 `ERROR: NO_SELECTION`。Python 侧捕捉此结果，返回对大模型友好的中文错误：“内容识别填充/生成式填充被拦截：请先框选一个选区再调用生成式填充。”
    - 调用 ActionManager `"syntheticFill"` 描述符执行生成式填充，并下发提示词。
  - **大模型提示词策略 (D-07)**：在大模型 system prompt 或 agent.py 预处理时，将用户的中文要求翻译为英文（如“飞船” -> "a futuristic spaceships"），并在 API 传参前进行 Prompt 优化扩展修饰。
- **acceptance_criteria**:
  - 在无选区时，调用 `apply_generative_fill` 返回 `success=False` 及没有选区拦截提示。
  - 在有选区时，调用成功，图层树增加生成图层。
  - 运行 `pytest tests/test_phase06_filters.py -k test_generative_fill` 各断言通过。

#### Task 06-01-07: 注册所有新工具
- **read_first**:
  - `backend/tools/registry.py`
- **action**:
  - 在 `backend/tools/registry.py` 中将上述 6 个新函数注册到全局 `ToolRegistry`：
    - `apply_blur_sharpen`
    - `apply_liquify`
    - `apply_camera_raw_preset`
    - `apply_neural_filter`
    - `apply_commercial_retouch`
    - `apply_generative_fill`
- **acceptance_criteria**:
  - 全局 `registry` 成功注册了 6 个新 API 实体。
  - 运行 `pytest` 全量测试无工具解析和 Schema 错误。

---

## Verification Plan

### Automated Tests
- `pytest tests/test_phase06_filters.py` (快速自动化全量校验)

### Manual Verification
- 启动本地前端，连接 Photoshop 客户端。
- 发送口令“把背景高斯模糊一下”，确保大模型自适应下发合理半径像素。
- 发送口令“帮我磨个皮”，校验图层多出 `_磨皮` 备份且带黑色蒙版，无报错弹窗。
- 发送口令“在脸上生成一副眼镜”，确保在无选区时大模型会友好提示“请先框选脸部”，在框选后生成成功。
