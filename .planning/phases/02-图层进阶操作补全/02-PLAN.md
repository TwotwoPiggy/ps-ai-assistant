---
phase: 02
plan: 1
type: feature
wave: 1
depends_on: []
files_modified:
  - backend/tools/ps_tools.py
  - backend/tools/registry.py
autonomous: true
requirements:
  - LYR-01
  - LYR-02
  - LYR-03
  - LYR-04
  - LYR-05
  - LYR-06
  - LYR-07
  - LYR-08
---

# Phase 02: 图层进阶操作补全 - 执行计划

<objective>
全面实现所有针对图层和图层组的高级操控、编组、合并与转化接口（共 8 个工具）。以支持大模型通过自然语言执行更复杂的图像编辑意图。所有新增工具将采用“默认操作当前活动层，支持可选层名检索”的机制，并在系统注册表中暴露。注意：计划将需求 LYR-04 中的 translate_layer 重新设计并命名为 move_layer 接口，以统一处理相对与绝对坐标位移。
</objective>

<tasks>
  <task>
    <id>1</id>
    <type>code</type>
    <action>在 `ps_tools.py` 中实现核心图层工具与 `_activate_layer` 辅助函数</action>
    <read_first>
      - backend/tools/ps_tools.py
    </read_first>
    <acceptance_criteria>
      - `ps_tools.py` 中包含 `_activate_layer(doc, layer_name: str = None)` 私有辅助函数。如果提供 `layer_name`，则递归遍历 `doc.Layers` 查找指定图层并设置为 `doc.ActiveLayer`（未找到时抛出异常）；若未提供则直接返回 `doc.ActiveLayer`。
      - 成功实现并导出以下 8 个图层操作工具：`group_layers`、`set_layer_opacity_and_fill`、`set_layer_blend_mode`、`move_layer` (对应并替代需求 LYR-04 的 translate_layer)、`merge_layers`、`duplicate_layer`、`rasterize_layer`、`convert_to_smart_object`。
      - 这些工具函数的第一个参数必须是 `ctx: PhotoshopContext`。除 `group_layers` 外，其余 7 个工具均提供 `layer_name: str = None` 参数。
      - `group_layers` 工具作为例外，须提供 `layer_names: list` 和 `group_name: str` 参数，以支持对多个图层进行编组。
      - 所有新增工具的 `docstring` 都必须详细清晰，明确写明：“如果不指定层名，则对当前活动层生效”，确保后续 Schema 生成语义准确无重叠。
      - 对于 `set_layer_opacity_and_fill`，涉及 `FillOpacity` 的部分必须用 `try...except` 包裹以防在操作图层组（LayerSet）时崩溃。
      - `set_layer_blend_mode`、`rasterize_layer`、`convert_to_smart_object` 这三个功能通过 `execute_jsx(ctx, jsx_code)` 拼接执行。特别是后两者的实现需包含防重复执行的幂等判断条件（如果已经是普通图层则不栅格化，如果是智能对象则不再转换）。
      - 其他工具使用 COM API 原生调用完成（如 `layer.Duplicate()`，`layer.Translate(dx, dy)`，`doc.MergeVisibleLayers()` 等）。
    </acceptance_criteria>
  </task>

  <task>
    <id>2</id>
    <type>code</type>
    <action>在 `registry.py` 中注册 8 个新图层工具</action>
    <read_first>
      - backend/tools/registry.py
    </read_first>
    <acceptance_criteria>
      - 将 `ps_tools.py` 中新增的 8 个函数全部导入。
      - 使用 `registry.register()` 依次注册 `group_layers`, `set_layer_opacity_and_fill`, `set_layer_blend_mode`, `move_layer`, `merge_layers`, `duplicate_layer`, `rasterize_layer`, `convert_to_smart_object`。
      - 保存文件后代码没有语法或导入错误。
    </acceptance_criteria>
  </task>
</tasks>

<verification>
  <must_haves>
    - `backend/tools/ps_tools.py` 内部包含了新增的 8 个函数。
    - 所有新增工具函数都拥有完整的 Python 类型注解及中文 docstring 描述。
    - 针对 `layer_name` 的处理统一调用了底层的寻找并激活逻辑；`group_layers` 适配了对 `layer_names` 列表的遍历激活逻辑。
    - `backend/tools/registry.py` 的工具列表中已全数注册新增接口。
  </must_haves>
  <step>1. 检查代码，确认 `ps_tools.py` 没有任何缩进和语法错误。</step>
  <step>2. 检查 `ps_tools.py`，确认 JSX 的拼接字符串没有明显的 JavaScript 语法错误，且依赖 `app.activeDocument.activeLayer` 获取上下文图层。</step>
  <step>3. 检查 `registry.py`，确保新引入的 8 个函数都被通过 `registry.register` 注册成功。</step>
</verification>

<threat_model>
  <threats>
    <threat>
      <component>backend/tools/ps_tools.py</component>
      <description>JSX 注入风险 (JSX Injection Vulnerability)。如果允许大模型输入恶意字符串直接拼接到 JavaScript 执行字符串中，可能引发系统层面的意外调用。</description>
      <impact>可能在 Photoshop 环境下执行未授权代码甚至影响宿主机安全。</impact>
      <severity>Low</severity>
      <mitigation>所有 JSX 工具操作均固定对 `app.activeDocument.activeLayer` 施加影响。唯一可能传入的用户数据是 `layer_name`，但我们在 Python COM 端进行查找匹配，并不将该参数直接注入到后续拼接的 JSX 脚本代码中，有效隔离了注入入口。</mitigation>
    </threat>
  </threats>
</threat_model>
