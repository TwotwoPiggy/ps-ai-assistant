# Phase 1: 文档管理增强与架构扩充 - Research Notes

## 1. 核心需求与目标回顾
本阶段旨在扩充基础架构，使 AI 助手不仅能操作已打开文档内部的图层，还能对整个应用层级和文档生命周期进行控制。
需实现以下需求标识：
- **DOC-01**: `create_document` (新建白板)
- **DOC-02**: `open_and_place` (打开本地图像)
- **DOC-03**: `save_document` (保存或导出)
- **DOC-04**: `resize_image` (调整图像尺寸)
- **DOC-05**: `change_color_mode` (切换色彩模式)
- **DOC-06**: `history_control` (撤销历史)
- **DOC-07**: `zoom_view` (画布缩放)
- **ARC-01**: `execute_jsx` (底层 ExtendScript 注入支持)

## 2. 现有架构基建改造建议
通过查阅 `backend/tools/ps_tools.py`，当前的 `PhotoshopContext` 类仅提供了 `get_doc()` 方法，并且内建了严格的检查：
```python
if ps_app.Documents.Count == 0:
    raise Exception("当前 Photoshop 中没有打开的文档，请先在 Photoshop 中打开或创建一个文档。")
```
**阻点**：`create_document` 和 `open_and_place` 这两个工具本身就是要在**没有文档**的初始状态下被调用的。如果强行依赖 `get_doc()` 会直接抛错。
**对策**：需要在 `PhotoshopContext` 中新增一个 `get_app()` 方法。该方法仅初始化并返回 `win32com.client.Dispatch("Photoshop.Application")`，不再进行 `Documents.Count` 断言。`create_document` 等工具将使用 `get_app()` 而不是 `get_doc()`。

## 3. 落地实现的决策对齐 (Context 约束)

1. **ARC-01 (`execute_jsx`) 的日志注入**：
   - 根据决策，此工具需使用 `ps_app.DoJavaScript(jsx_code)` 将代码传给底层执行。
   - 必须在 Python 顶部引入 `logging`，并在 `execute_jsx` 内加入 `logger.debug(...)` 直接打印要执行的 JS 字符串代码，以便排查黑盒报错。

2. **DOC-05 (`change_color_mode`) 的静默与安全提示**：
   - **静默执行**：在执行前，需设置 `ps_app.DisplayDialogs = 3` (3 对应 psDisplayNoDialogs)，强制阻断原生报错与确认弹窗。
   - **提示词护栏**：在对应 Python 工具函数的 docstring (将被 `schema.py` 转化为 prompt) 中，必须明确声明：“执行此工具前，必须先在聊天界面提示用户即将进行色彩转换，等待用户明确回复『允许 (allow)』后才可调用。”

3. **DOC-03 (`save_document`) 的默认路径推断**：
   - 当调用参数不传 `file_path` 时，需根据决策：
     - 首先尝试获取 `doc.FullName`（已存盘过的内容）。
     - 若 `doc.FullName` 抛出异常（即这是个“无标题”新建文档），则使用 `os.path.expanduser("~/Desktop")` 获取用户的桌面路径，自动生成包含当前时间戳的默认文件名（如 `ps_ai_export_12345.psd` 或 `.png`）。

## 4. COM API / JSX 的黑魔法应用
部分工具使用原生 DOM 封装并不容易，结合 `ARC-01` 我们可以在底层巧妙应用 JS/ActionManager：
- **`history_control`**: 利用 `DoJavaScript` 直接抛入 `app.runMenuItem(charIDToTypeID('undo'));` 甚至操作 `historyStates` 会比 Python 的 COM 遍历更健壮。
- **`zoom_view`**: 同样使用 `DoJavaScript` 注入 `app.runMenuItem(stringIDToTypeID('actualPixels'));` (100%) 和 `app.runMenuItem(stringIDToTypeID('fitOnScreen'));` (适应屏幕) 即可，Python 的 COM 并未直接开放 Zoom。

## 5. Schema 生成机制的协同
`backend/tools/schema.py` 是依赖 Python 的 `docstring` 来提取描述并转化为大模型的 Tools Object 的。因此，在实现这些函数时，必须严格遵守以下注释范式：
```python
def example_tool(ctx, param1: str):
    """描述工具的作用。
    可以在这里放置前置规则与铁律约束。
    
    Args:
        param1: 参数的详细说明，以及可能的枚举值。
    """
```
并且在完成这些函数后，必须到 `backend/tools/registry.py` 的底部注册新加的 8 个函数。

## 总结
我已了解所有需要实施的技术细节与项目上下文规则。通过拓展 Context 以支持全局应用级操作，借助 DoJavaScript 跨越 DOM 缺陷，并严格控制文档保存路径与安全护栏，即可平稳且高质量地开展接下来的 Plan 阶段。
