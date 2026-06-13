# Requirements

## Active

### 文档管理 (Document)
- [ ] **DOC-01**: 实现 `create_document` 工具，允许 AI 指定宽高和背景色新建白板。
- [ ] **DOC-02**: 实现 `open_and_place` 工具，允许 AI 打开指定本地路径的图像。
- [ ] **DOC-03**: 实现 `save_document` 工具，允许 AI 保存 PSD 或导出常用图片格式。
- [ ] **DOC-04**: 实现 `resize_image` 工具，允许 AI 有损/无损缩放图像本身（非画布尺寸）。
- [ ] **DOC-05**: 实现 `change_color_mode` 工具，允许 AI 在 RGB/CMYK/灰度间切换。
- [ ] **DOC-06**: 实现 `history_control` 工具，允许 AI 回退撤销操作。
- [ ] **DOC-07**: 实现 `zoom_view` 工具，允许 AI 改变画布缩放比例（100%、适应屏幕）。

### 图层进阶 (Layers)
- [ ] **LYR-01**: 实现 `group_layers` 工具，允许 AI 将特定图层建立分组。
- [ ] **LYR-02**: 实现 `set_layer_opacity_and_fill` 工具，允许 AI 单独修改不透明度或填充。
- [ ] **LYR-03**: 实现 `set_layer_blend_mode` 工具，允许 AI 切换正片叠底、滤色等混合模式。
- [ ] **LYR-04**: 实现 `translate_layer` 工具，允许 AI 将图层沿 X/Y 轴移动指定像素。
- [ ] **LYR-05**: 实现 `merge_layers` 工具，提供向下合并、合并可见、拼合图像三种选项。
- [ ] **LYR-06**: 实现 `duplicate_layer` 工具，允许 AI 直接复制指定图层。
- [ ] **LYR-07**: 实现 `rasterize_layer` 工具，允许 AI 栅格化图层。
- [ ] **LYR-08**: 实现 `convert_to_smart_object` 工具，允许 AI 将图层转为智能对象（使用 JSX 后门）。

### 架构适配 (Architecture)
- [ ] **ARC-01**: 在后端 `ps_tools` 中添加 `execute_jsx()` 包装层用于执行 ActionManager 级代码。
- [ ] **ARC-02**: 在提示词和 Schema 中精准暴露所有这 15 个能力，消除语义重叠。

## Future Requirements
(None)

## Out of Scope
- UXP 架构迁移 (由于目标免安装环境兼容性极差，已全面废弃，坚守 Web+COM)。

## Traceability

| Requirement | Phase |
|---|---|
| DOC-01 | Phase 1 |
| DOC-02 | Phase 1 |
| DOC-03 | Phase 1 |
| DOC-04 | Phase 1 |
| DOC-05 | Phase 1 |
| DOC-06 | Phase 1 |
| DOC-07 | Phase 1 |
| LYR-01 | Phase 2 |
| LYR-02 | Phase 2 |
| LYR-03 | Phase 2 |
| LYR-04 | Phase 2 |
| LYR-05 | Phase 2 |
| LYR-06 | Phase 2 |
| LYR-07 | Phase 2 |
| LYR-08 | Phase 2 |
| ARC-01 | Phase 1 |
| ARC-02 | Phase 3 |
