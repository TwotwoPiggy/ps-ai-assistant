# UXP API 字典全景与精简清单

## 1. UXP API 全领域能力摸底全景图
本节梳理 UXP 目前暴露的所有领域能力，涵盖基础操作与高级进阶操作。

### 1.1 基础文档与画布操作 (Document & Canvas)
*   **文档管理**：新建文档、打开文档、保存/另存为、关闭文档。
*   **画布调整**：裁剪画布 (`crop`)、调整画布大小 (`resizeCanvas`)、调整图像大小 (`resizeImage`)。
*   **视图控制**：缩放 (`zoom`)、平移 (`pan`)。
*   **历史记录**：撤销 (`undo`)、重做 (`redo`)、跳转到历史状态。

### 1.2 图层与选区基础操作 (Layers & Selections)
*   **图层树获取**：获取当前文档中所有的图层及其层级关系 (`get_layer_tree`)。
*   **图层基本管理**：新建图层 (`create_layer`)、删除图层 (`delete_layer`)、重命名图层 (`rename_layer`)、隐藏/显示图层 (`set_layer_visibility`)。
*   **图层属性管理**：调整图层不透明度 (`opacity`)、混合模式 (`blendMode`)。
*   **图层排序与移动**：重新排序图层 (`reorder_layer`)、移动图层元素 (`translate`)。
*   **选区操作**：全选、取消选择、反选、基于路径/像素创建选区。

### 1.3 图像处理与调整 (Image Adjustments)
*   **色彩调整**：亮度/对比度 (`adjust_brightness_contrast`)、色相/饱和度、曲线 (`curves`)、色阶 (`levels`)、色彩平衡。
*   **图像变换**：翻转图像 (`flip_image`)、自由变换 (`freeTransform`)、旋转 (`rotate`)。

### 1.4 高级与扩展功能 (Advanced Features)
*   **滤镜 (Filters)**：高斯模糊、锐化、液化、杂色、渲染滤镜等。*(注：部分滤镜只能通过 batchPlay 触发，且参数极其复杂)*
*   **智能对象 (Smart Objects)**：转换为智能对象、栅格化图层、编辑智能对象内容。
*   **文本操作 (Text)**：创建文本图层、修改文本内容、调整字体、字号与段落样式。
*   **矢量与路径 (Vectors & Paths)**：钢笔工具路径绘制、形状图层生成、图层蒙版、矢量蒙版。
*   **3D 与动画 (3D & Animation)**：管理 3D 模型图层、时间轴关键帧操作（由于逐渐从 PS 中剥离，UXP 对 3D 支持逐步减弱）。

---

## 2. 核心高频工具精简清单
为了提供给大模型高效的上下文且不超出 Token 限制，我们从上方的全景图中提取出 **11 个核心高频操作**，作为 AI 助手首批支持的能力体系。

这些工具的调用策略：**DOM API 优先**，遇到DOM API 不支持或者性能过慢的情况再降级使用 **batchPlay**。

| 工具名称 | 功能描述 | 推荐调用策略 | 适用场景 |
| :--- | :--- | :--- | :--- |
| `get_layer_tree` | 获取当前文档图层树 | **DOM API** (`app.activeDocument.layers`) | UI 刷新、大模型需要理解当前图层上下文时 |
| `get_canvas_snapshot` | 获取画布当前状态快照 | **batchPlay** (执行保存，通过沙盒导流 Base64) | 视觉多模态大模型需观察当前画面时 |
| `create_layer` | 创建新图层 | **DOM API** (`document.createArtLayer()`) | 需要在画布上添加新元素前 |
| `delete_layer` | 删除指定图层 | **DOM API** (`layer.delete()`) | 移除不需要的元素 |
| `rename_layer` | 重命名图层 | **DOM API** (`layer.name = newName`) | 结构化管理图层堆栈时 |
| `set_layer_visibility` | 设置图层可见性 | **DOM API** (`layer.visible = bool`) | 快速查看修改前后的对比 |
| `reorder_layer` | 重新排列图层顺序 | **DOM API** (`layer.move()`) | 调整元素前后遮挡关系时 |
| `adjust_brightness_contrast` | 调整亮度/对比度 | **batchPlay** (DOM 尚未完整暴露 Adjustment Layer) | 进行图像基础明暗修正时 |
| `crop_canvas` | 裁剪画布 | **DOM API** (`document.crop()`) 或 **batchPlay** | 构图调整时 |
| `resize_canvas` | 调整画布大小 | **DOM API** (`document.resizeCanvas()`) | 扩图或修改画幅比例时 |
| `flip_image` | 翻转图像(水平/垂直) | **batchPlay** | 调整图像朝向或镜像处理时 |

> 详情参见 `docs/uxp_tools_schema.json` 中定义的 Function Calling Schema。
