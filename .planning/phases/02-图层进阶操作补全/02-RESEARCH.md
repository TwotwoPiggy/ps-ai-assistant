# Phase 02: 图层进阶操作补全 - Research

## Objective
研究如何高质量地规划与实施 Phase 02，补全对 Photoshop 图层和图层组的高级操控、编组、合并与转化接口，并直接回答：“What do I need to know to PLAN this phase well?”

## 核心认知与设计准则

### 1. 目标图层指定机制 (Target Layer Strategy)
相较于 Phase 1 严格依赖 `get_layer_tree` 提供的内部 `layer_identify` (如 `layer_1`)，Phase 2 已在决策中明确了**“默认操作当前层，支持可选层名检索”**的规则。
- **What you need to know**: 在规划代码时，所有新增的 Phase 2 工具（除极少特例外）都需要新增一个可选参数 `layer_name: str = None`。
- **底层实现模式**: 需要在 `ps_tools.py` 中抽取一个类似 `_activate_layer(doc, layer_name: str = None)` 的私有辅助函数。
  - 传入了 `layer_name`，则递归遍历 `doc.Layers` 找到同名图层，执行 `doc.ActiveLayer = target_layer`（找不到则报错）。
  - 未传入则直接返回当前的 `doc.ActiveLayer`。
  - 通过这种方式对齐人类直觉操作：先选中目标，再施加动作。

### 2. 八个核心工具的实现路径解析
通过对 Python `win32com` 及 Photoshop ExtendScript (JSX) 的能力核对，你需要了解以下实现细节来规划好接口：

*   **LYR-01: `group_layers` (编组)**
    *   **参数**: `layer_names: list`, `group_name: str`
    *   **方案**: 使用 COM API 的 `new_group = doc.LayerSets.Add()` 创建新组，接着遍历 `layer_names`，将它们逐个激活后通过 `layer.Move(new_group, 2)` (psPlaceInside) 移入组中。注意 Schema 注册器已自动支持将 `list` 映射为 `array`。
*   **LYR-02: `set_layer_opacity_and_fill` (不透明度与填充)**
    *   **参数**: `opacity: float = None`, `fill: float = None`, `layer_name: str = None`
    *   **方案**: 对找到的 layer，分别判断如果参数存在，则赋值给 `layer.Opacity` 和 `layer.FillOpacity`。
    *   **注意点**: 对于 `LayerSet` (文件夹/图层组)，Photoshop 可能不存在 FillOpacity 属性，必须使用 `try/except` 进行包裹防崩。
*   **LYR-03: `set_layer_blend_mode` (混合模式)**
    *   **参数**: `blend_mode: str`, `layer_name: str = None`
    *   **方案**: 因为 COM 的混合模式常量（魔术数字）易读性差且不好映射，**建议采用 JSX 注入**的方式。在 Python 端维护一套字符串到 JS 枚举的映射（例如 `"multiply": "BlendMode.MULTIPLY"`），然后调用已有的 `execute_jsx` 执行赋值。
*   **LYR-04: `move_layer` (移动位移)**
    *   **参数**: `x: float = None`, `y: float = None`, `dx: float = None`, `dy: float = None`, `layer_name: str = None`
    *   **方案**: 内部根据参数推断。如果提供 `x`, `y`，读取当前层的 `bounds` 属性，计算出 `dx = x - bounds[0]` 和 `dy = y - bounds[1]`；如果只提供 `dx`, `dy` 则直接使用。统一调用 COM 的 `layer.Translate(dx, dy)`。
*   **LYR-05: `merge_layers` (图层合并)**
    *   **参数**: `merge_type: str = "mergeDown"`, `layer_name: str = None`
    *   **方案**:
        *   `mergeDown` -> `layer.Merge()`
        *   `mergeVisible` -> `doc.MergeVisibleLayers()`
        *   `flattenImage` -> `doc.Flatten()`
*   **LYR-06: `duplicate_layer` (复制图层)**
    *   **参数**: `layer_name: str = None`, `new_name: str = None`
    *   **方案**: 使用 COM 的 `dup = layer.Duplicate()`，如果存在 `new_name` 则立即设置 `dup.Name = new_name`。
*   **LYR-07: `rasterize_layer` (栅格化)**
    *   **方案**: 必须贯彻“幂等与静默成功”决策。推荐全用 JSX：
        ```javascript
        var layer = app.activeDocument.activeLayer;
        if (layer.kind != LayerKind.NORMAL) {
            layer.rasterize(RasterizeType.ENTIRELAYER);
        }
        ```
*   **LYR-08: `convert_to_smart_object` (转智能对象)**
    *   **方案**: 因为 COM 不支持此操作，依决策使用 JSX ActionManager 后门，并做幂等判断：
        ```javascript
        var layer = app.activeDocument.activeLayer;
        if (layer.kind != LayerKind.SMARTOBJECT) {
            executeAction(stringIDToTypeID("newPlacedLayer"), undefined, DialogModes.NO);
        }
        ```

### 3. 工具暴露与提示词防冲突
- Phase 1 的工具依赖于 `layer_identify` 参数；Phase 2 的工具改用可选的 `layer_name`。在编写工具的 docstring（用于 Schema 生成）时，**必须明确写清**：“如果不指定层名，则对当前活动层生效”，这能极大提升 AI 的推理成功率，减少幻觉并达成“语义无重叠”。

## 结论 (Conclusion)
你现在已经具备了实现 Phase 2 所需的所有底层知识储备（COM API 与 JSX 注入边界的选择）、参数设计策略（可选 layer_name 适配活动层）以及应对极端情况的处理方案（幂等性检查、填充异常兜底）。接下来的 Plan 步骤只需逐个落实到 `ps_tools.py`，并在 `registry.py` 中挂载这些接口即可。
