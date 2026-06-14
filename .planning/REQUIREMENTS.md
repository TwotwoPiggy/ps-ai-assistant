# Requirements

## Active

### 选区与蒙版 (Selection & Mask)
- [ ] **SEL-01**: AI 助手可执行基础选区操作 (矩形、椭圆、全选、反选、取消)
- [ ] **SEL-02**: AI 助手可修饰选区 (羽化、扩展、收缩、平滑、边界)
- [ ] **SEL-03**: AI 助手可调用智能选择 (选择主体、移除背景、色彩范围)
- [ ] **MASK-01**: AI 助手可控制图层蒙版 (添加、应用、删除、启用/禁用)
- [ ] **CHAN-01**: AI 助手可控制通道 (载入为选区、选区存为通道)

### 专业调色与光影 (Color Correction)
- [ ] **ADJ-01**: AI 助手可进行基础曝光调色 (亮度对比度、色阶、曲线、曝光度)
- [ ] **ADJ-02**: AI 助手可进行基础色彩调色 (色相饱和度、色彩平衡、自然饱和度、黑白等)
- [ ] **ADJ-03**: AI 助手可创建无损调整图层
- [ ] **COL-01**: AI 助手可设置前景色/背景色 (HEX/RGB)
- [ ] **COL-02**: AI 助手可执行填充与描边 (颜色填充、内容识别填充、描边)

### 高级滤镜与人像美化 (Filters & Retouching)
- [x] **FIL-01**: AI 助手可应用模糊与锐化滤镜 (高斯模糊、表面模糊、USM 锐化等)
- [x] **FIL-02**: AI 助手可唤起并应用液化滤镜参数 (瘦脸、形体调整)
- [x] **FIL-03**: AI 助手可调用 Camera Raw 滤镜进行专业后期套用
- [x] **AI-01**: AI 助手可触发 Neural Filters (神经元滤镜)
- [x] **AI-02**: AI 助手可自动执行经典商业磨皮动作流 (高反差保留+表面模糊)
- [x] **AI-03**: AI 助手可触发生成式填充 (Generative Fill) 并传递提示词

### 自动化与动作集成 (Automation & Actions)
- [ ] **AUTO-01**: AI 助手可直接调用 PS 内部已录制好的动作集合 (Actions)
- [ ] **AUTO-02**: AI 助手可加载并运行本地任意 `.jsx` 扩展脚本
- [ ] **AUTO-03**: AI 助手可将设计图自动切片并导出 Web 所用格式

## Future Requirements
(None)

## Out of Scope
- UXP 相关的迁移操作已明确废弃

## Traceability
- **Phase 04**: SEL-01, SEL-02, SEL-03, MASK-01, CHAN-01
- **Phase 05**: ADJ-01, ADJ-02, ADJ-03, COL-01, COL-02
- **Phase 06**: FIL-01, FIL-02, FIL-03, AI-01, AI-02, AI-03
- **Phase 07**: AUTO-01, AUTO-02, AUTO-03
