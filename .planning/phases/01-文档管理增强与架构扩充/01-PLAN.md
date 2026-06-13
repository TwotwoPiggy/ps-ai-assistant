---
wave: 1
depends_on: []
files_modified:
  - backend/tools/ps_tools.py
  - backend/tools/registry.py
autonomous: true
---

# Phase 1: 文档管理增强与架构扩充 - Plan

## Goal
在 `ps_tools` 中新增底层脚本执行支持，并实现所有基础文档级操作，支持无打开文档状态下的调用。

## Requirements Mapped
DOC-01, DOC-02, DOC-03, DOC-04, DOC-05, DOC-06, DOC-07, ARC-01

## Tasks

```xml
<task>
  <id>1</id>
  <description>改造 PhotoshopContext 添加 get_app 方法</description>
  <read_first>
    <file>backend/tools/ps_tools.py</file>
  </read_first>
  <action>
    在 `PhotoshopContext` 类中抽取 `get_app()` 方法。
    将原先 `get_doc()` 中的 `pythoncom.CoInitialize()` 和 `win32com.client.Dispatch("Photoshop.Application")` 逻辑移入 `get_app()`，并直接返回 `ps_app`。
    修改 `get_doc()`，使其首先调用 `self.get_app()` 获取 `ps_app`，然后再执行 `ps_app.Documents.Count == 0` 的断言检查，最后返回 `ps_app.ActiveDocument`。
  </action>
  <acceptance_criteria>
    `PhotoshopContext` 存在 `get_app` 方法且返回应用实例，`get_doc` 基于 `get_app` 工作并保留了无文档报错逻辑。
  </acceptance_criteria>
</task>

<task>
  <id>2</id>
  <description>实现 execute_jsx 底层脚本执行支持 (ARC-01)</description>
  <read_first>
    <file>backend/tools/ps_tools.py</file>
    <file>.planning/phases/01-文档管理增强与架构扩充/01-RESEARCH.md</file>
  </read_first>
  <action>
    在 `backend/tools/ps_tools.py` 顶部引入 `logging` 模块，配置基础 logger（如 `logger = logging.getLogger(__name__)`）。
    新增 `execute_jsx(ctx: PhotoshopContext, jsx_code: str) -> dict` 工具函数。
    函数内部使用 `logger.debug` 打印 `jsx_code` 字符串内容。
    调用 `ctx.get_app().DoJavaScript(jsx_code)` 执行脚本。
  </action>
  <acceptance_criteria>
    `execute_jsx` 函数在执行前通过 `logger.debug` 输出注入的代码内容，且使用了 `DoJavaScript`。
  </acceptance_criteria>
</task>

<task>
  <id>3</id>
  <description>实现 create_document 和 open_and_place 工具 (DOC-01, DOC-02)</description>
  <read_first>
    <file>backend/tools/ps_tools.py</file>
  </read_first>
  <action>
    在 `backend/tools/ps_tools.py` 新增 `create_document(ctx: PhotoshopContext, width: int, height: int, resolution: float = 72.0, name: str = "New Document") -> dict`，使用 `ctx.get_app().Documents.Add(width, height, resolution, name)`。
    新增 `open_and_place(ctx: PhotoshopContext, file_path: str) -> dict`，使用 `ctx.get_app().Open(file_path)`。
    这两个工具必须调用 `ctx.get_app()` 而不是 `ctx.get_doc()`，以规避严格的文档检查。
  </action>
  <acceptance_criteria>
    在没有打开文档的情况下（即 `Documents.Count == 0` 时），调用 `create_document` 或 `open_and_place` 能够成功执行而不抛出断言异常。
  </acceptance_criteria>
</task>

<task>
  <id>4</id>
  <description>实现 save_document 默认路径规则 (DOC-03)</description>
  <read_first>
    <file>backend/tools/ps_tools.py</file>
    <file>.planning/phases/01-文档管理增强与架构扩充/01-CONTEXT.md</file>
  </read_first>
  <action>
    新增 `save_document(ctx: PhotoshopContext, file_path: str = None) -> dict` 工具函数。
    当 `file_path` 为空时，首先尝试访问 `ctx.get_doc().FullName`。
    如果访问 `FullName` 抛出异常，则使用 `os.path.expanduser("~/Desktop")` 获取桌面路径，并结合 `time.time()` 或其他时间戳生成默认文件名（如 `ps_ai_export_{timestamp}.psd`）作为兜底保存路径。
  </action>
  <acceptance_criteria>
    调用 `save_document` 时若未提供路径且文档未曾存盘，可自动将其保存到用户的桌面目录下并带有时间戳文件名。
  </acceptance_criteria>
</task>

<task>
  <id>5</id>
  <description>实现 resize_image 和 change_color_mode (DOC-04, DOC-05)</description>
  <read_first>
    <file>backend/tools/ps_tools.py</file>
    <file>.planning/phases/01-文档管理增强与架构扩充/01-RESEARCH.md</file>
  </read_first>
  <action>
    新增 `resize_image(ctx: PhotoshopContext, width: int, height: int) -> dict` 工具函数，调用 `ctx.get_doc().ResizeImage(width, height)`。
    新增 `change_color_mode(ctx: PhotoshopContext, mode: str) -> dict` 工具函数。
    在 `change_color_mode` 函数内部执行模式转换前，强行设置 `ctx.get_app().DisplayDialogs = 3` 拦截警告弹窗。
    在 `change_color_mode` 的 docstring 中必须逐字包含这段铁律声明："执行此工具前，必须先在聊天界面提示用户即将进行色彩转换，等待用户明确回复『允许 (allow)』后才可调用。"
  </action>
  <acceptance_criteria>
    `change_color_mode` 源代码中显式存在 `DisplayDialogs = 3` 赋值；docstring 中精确包含要求的允许用户确认的铁律描述字符串。
  </acceptance_criteria>
</task>

<task>
  <id>6</id>
  <description>使用 ActionManager/JSX 实现 history_control 与 zoom_view (DOC-06, DOC-07)</description>
  <read_first>
    <file>backend/tools/ps_tools.py</file>
    <file>.planning/phases/01-文档管理增强与架构扩充/01-RESEARCH.md</file>
  </read_first>
  <action>
    新增 `history_control(ctx: PhotoshopContext) -> dict` 工具函数，在内部通过 `ctx.get_app().DoJavaScript("app.runMenuItem(charIDToTypeID('undo'));")` 执行撤销。
    新增 `zoom_view(ctx: PhotoshopContext, action: str) -> dict` 工具函数，根据 action 是 '100%' 还是 'fit'，通过 `ctx.get_app().DoJavaScript(...)` 注入 `app.runMenuItem(stringIDToTypeID('actualPixels'));` 或 `app.runMenuItem(stringIDToTypeID('fitOnScreen'));`。
  </action>
  <acceptance_criteria>
    `history_control` 和 `zoom_view` 均依赖 `DoJavaScript` 和 ActionManager 的标识符（`undo`, `actualPixels`, `fitOnScreen`）来间接完成操作。
  </acceptance_criteria>
</task>

<task>
  <id>7</id>
  <description>注册 8 个新工具</description>
  <read_first>
    <file>backend/tools/registry.py</file>
  </read_first>
  <action>
    修改 `backend/tools/registry.py`，在文件底部补充注册新添加的 8 个函数。
    对应的注入语句应为：
    `registry.register(ps_tools.execute_jsx)`
    `registry.register(ps_tools.create_document)`
    `registry.register(ps_tools.open_and_place)`
    `registry.register(ps_tools.save_document)`
    `registry.register(ps_tools.resize_image)`
    `registry.register(ps_tools.change_color_mode)`
    `registry.register(ps_tools.history_control)`
    `registry.register(ps_tools.zoom_view)`
  </action>
  <acceptance_criteria>
    `registry.get_all_tools()` 的返回值数量比原先增加 8 个，且这 8 个新工具的名字能在大模型的 OpenAI tools schema 中查找到。
  </acceptance_criteria>
</task>
```

## Verification

### must_haves
- [ ] `PhotoshopContext` 暴露了 `get_app()` 接口，无文档也可调用 COM 方法。
- [ ] 注册了 8 个新工具并在 Schema 中可用。
- [ ] `change_color_mode` 包含拦截弹窗逻辑 `DisplayDialogs = 3` 且带有交互要求的 Prompt 注释。
- [ ] `save_document` 具备无名文档回退至桌面的容错逻辑。

### Verify execution
1. 检查代码：`backend/tools/ps_tools.py` 是否有 8 个新的 def 并包含对应的正确逻辑。
2. 检查注册表：`backend/tools/registry.py` 的文件底部是否完整注册了上述 8 个工具函数。
