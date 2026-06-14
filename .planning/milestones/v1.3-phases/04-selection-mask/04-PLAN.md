# Phase 04 Plan: 选区与蒙版控制 (Selection & Mask)

## Goal
实现基础与智能选区、蒙版以及通道控制相关的全部操作 API。

## Files Modified
- `backend/tools/ps_tools.py`
- `backend/tools/registry.py`

## Tasks

1. **Implement `basic_selection` tool** [SEL-01]
   - **File:** `backend/tools/ps_tools.py`
   - **Details:** Parameters: `action` (rect/ellipse/all/invert/deselect), `bounds` (optional array), `selection_mode` (replace/add/subtract/intersect, default 'replace').
   - **Logic:** Map `selection_mode` to PS constant (1, 2, 3, 4). Call `doc.Selection.Select`, `SelectAll`, `Invert`, or `Deselect`.

2. **Implement `modify_selection` tool** [SEL-02]
   - **File:** `backend/tools/ps_tools.py`
   - **Details:** Parameters: `action` (feather/expand/contract/smooth/border), `value` (int).
   - **Logic:** Map to `doc.Selection.Feather()`, `Expand()`, `Contract()`, `Smooth()`, `MakeWorkPath() / Border()`.

3. **Implement `smart_selection` tool** [SEL-03]
   - **File:** `backend/tools/ps_tools.py`
   - **Details:** Parameters: `action` (subject/remove_bg).
   - **Logic:** Generate JSX ActionManager code for autoCutout. Wrap `execute_jsx` in `try/except`. If it fails, return `{"success": False, "error": "智能选择失败或未找到主体，请确认图像内容"}`.

4. **Implement `mask_control` tool** [MASK-01]
   - **File:** `backend/tools/ps_tools.py`
   - **Details:** Parameters: `layer_identify` (str), `action` (add/apply/delete/enable/disable), `force_apply` (bool, default False).
   - **Logic:** 
     - If `action == 'apply'` and not `force_apply`: return error.
     - Execute ActionManager JSX for the mask operations.

5. **Implement `channel_control` tool** [CHAN-01]
   - **File:** `backend/tools/ps_tools.py`
   - **Details:** Parameters: `action` (save_selection/load_selection), `channel_name` (optional str).
   - **Logic:** If `channel_name` is empty when saving, use `"Selection_" + timestamp`. Call `doc.Selection.Store` and `doc.Selection.Load`.

6. **Register Tools**
   - **File:** `backend/tools/registry.py`
   - **Details:** Register all 5 new tools in the ToolRegistry.

## Dependencies
- Phase 01 & 02 complete (Context and DoJavaScript).

## Verification
- Ensure Python syntax is correct.
- Verify Schema generation logic (docstrings).
