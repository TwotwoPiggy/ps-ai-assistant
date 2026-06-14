# Phase 05 Plan: 专业调色与光影实现 (Color Correction)

## Goal
实现前背景色控制、智能填充、无损调整图层以及破坏性调色的 COM API。拦截所有不规范操作（如无选区时的 CAF），并支持细分通道的全量参数。

## Files Modified
- `backend/tools/ps_tools.py`
- `backend/tools/registry.py`

## Tasks

1. **Implement `set_color` tool** [COLOR-01]
   - **File:** `backend/tools/ps_tools.py`
   - **Details:** 
     - Parameters: `target` (foreground/background), `color_format` (hex/rgb/hsb/cmyk), `color_value` (str/list/dict depends on format).
     - 大模型多模态支持：在 `docstring` 中明确标注，当用户给出模糊颜色描述且有参考图时，大模型应当优先利用视觉能力提取出 Hex 传入此方法。
   - **Logic:** 
     - 解析 `color_value` 并映射至 `Photoshop.SolidColor`。
     - 若 `target` 为 `foreground`，设置 `app.ForegroundColor = color_obj`。

2. **Implement `fill_selection` tool** [COLOR-02]
   - **File:** `backend/tools/ps_tools.py`
   - **Details:** 
     - Parameters: `fill_type` (foreground/background/color/content_aware/pattern/black/white/gray).
   - **Logic:** 
     - 对于 `content_aware`，使用 `try/except` 探测 `app.ActiveDocument.Selection.Bounds`，如触发异常，严格返回明确中文提示：“当前没有有效选区，内容识别填充已被拦截，请先创建选区。”
     - 执行 `doc.Selection.Fill()` 或者对应的 ActionManager `Fl  ` 命令。

3. **Implement `color_correction` tool** [COLOR-03]
   - **File:** `backend/tools/ps_tools.py`
   - **Details:** 
     - Parameters: `correction_type` (levels/color_balance/hue_saturation), `is_adjustment_layer` (bool, default True), `params` (dict, 支持 master 及 rgb 各子通道)。
     - 在 `docstring` 中建立契约：要求大模型优先使用主通道（master），且针对模糊修图指令必须向用户确认是否使用调整图层。
   - **Logic:** 
     - 如果 `is_adjustment_layer` 为 True，拼接 `Mk  ` 和 `AdjL` 的 JSX 脚本，并嵌入 `Usng` 对应的调整参数。
     - 如果为 False，拼接并直接针对图层执行 `Lvls` 等破坏性命令。

4. **Implement `stroke_selection` tool** [COLOR-04]
   - **File:** `backend/tools/ps_tools.py`
   - **Details:** 
     - Parameters: `width` (int), `location` (inside/center/outside), `color` (hex/rgb)。
   - **Logic:** 
     - 使用 `doc.Selection.Stroke()` 并将 `color` 参数转为 `SolidColor` 对象。

5. **Register Tools**
   - **File:** `backend/tools/registry.py`
   - **Details:** Register `set_color`, `fill_selection`, `color_correction`, `stroke_selection` in the ToolRegistry.

## Dependencies
- Phase 04 (Selection & Mask) 提供的图层和选区前置逻辑。

## Verification
- 确保 `content_aware` 在无选区时成功报错而不是抛出底层 COM_Error。
- 确保子通道和主通道调色均能正确生成对应的 ActionManager Descriptor。
