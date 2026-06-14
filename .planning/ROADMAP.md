# Roadmap

## Proposed Roadmap

**4 phases** | **19 requirements mapped** | All covered ✓

| # | Phase | Goal | Requirements | Success Criteria |
|---|-------|------|--------------|------------------|
| 04 | 选区与蒙版控制 (Selection & Mask) | 实现基础与智能选区、蒙版以及通道控制相关的全部操作 API | SEL-01, SEL-02, SEL-03, MASK-01, CHAN-01 | 5 |
| 05 | 专业调色与光影实现 (Color Correction) | 实现基础调色、色彩修正、调整图层以及填充描边的 API | ADJ-01, ADJ-02, ADJ-03, COL-01, COL-02 | 5 |
| 06 | 高级滤镜与人像美化 (Filters & Retouching) | 实现常见滤镜、液化、Camera Raw、神经元滤镜以及生成式填充 API | FIL-01, FIL-02, FIL-03, AI-01, AI-02, AI-03 | 6 |
| 07 | 自动化与动作集成 (Automation & Actions) | 支持直接调用录制动作、执行本地扩展脚本以及切片导出 API | AUTO-01, AUTO-02, AUTO-03 | 3 |

### Phase Details

**Phase 04: 选区与蒙版控制 (Selection & Mask)**
Goal: 实现基础与智能选区、蒙版以及通道控制相关的全部操作 API
Requirements: SEL-01, SEL-02, SEL-03, MASK-01, CHAN-01
Success criteria:
1. 用户可通过自然语言完成矩形/椭圆选区等基础操作。
2. 支持羽化、平滑、扩展等选区修饰操作。
3. 支持通过 "选择主体" 等 AI 功能智能创建选区。
4. 可以顺利为指定图层添加或删除蒙版，并支持启用禁用。
5. 通道与选区可相互转换而不报错。

**Phase 05: 专业调色与光影实现 (Color Correction)**
Goal: 实现基础调色、色彩修正、调整图层以及填充描边的 API
Requirements: ADJ-01, ADJ-02, ADJ-03, COL-01, COL-02
Success criteria:
1. 用户可以通过指令调整亮度/对比度和色阶等曝光参数。
2. 可实现色相/饱和度及黑白、色彩平衡等直接色彩调整。
3. 可支持新建无损调整图层并赋予对应调色效果。
4. 能够动态设置 PS 的前景色和背景色。
5. 能够对指定选区进行纯色或内容识别填充。

**Phase 06: 高级滤镜与人像美化 (Filters & Retouching)**
Goal: 实现常见滤镜、液化、Camera Raw、神经元滤镜以及生成式填充 API
Requirements: FIL-01, FIL-02, FIL-03, AI-01, AI-02, AI-03
Success criteria:
1. 能够执行常见模糊与锐化滤镜（支持参数传递）。
2. 可调用液化参数对画面进行形体处理。
3. 能够套用 Camera Raw 滤镜预设。
4. 支持触发 PS 2024/2026 的神经元滤镜。
5. 通过宏脚本自动化实现商业磨皮流程。
6. 支持 Generative Fill，基于选中区域与文字提示生成内容。

**Phase 07: 自动化与动作集成 (Automation & Actions)**
Goal: 支持直接调用录制动作、执行本地扩展脚本以及切片导出 API
Requirements: AUTO-01, AUTO-02, AUTO-03
Success criteria:
1. 可以通过动作名称和动作集名称执行动作面板中的录制动作。
2. 能够加载本地 JSX 文件并由底层通过 `DoJavaScript` 直接执行。
3. 能够自动切片并以 Web 所用格式进行导出。
