# Roadmap: v1.2 补全 COM 接口基础能力

**3 phases** | **17 requirements mapped** | All covered ✓

| # | Phase | Goal | Requirements | Success Criteria |
|---|-------|------|--------------|------------------|
| 1 | 文档管理增强与架构扩充 | 在 `ps_tools` 中新增底层脚本执行支持，并实现所有文档级操作 | DOC-01, DOC-02, DOC-03, DOC-04, DOC-05, DOC-06, DOC-07, ARC-01 | 7 |
| 2 | 图层进阶操作补全 | 全面实现所有针对图层和图层组的高级操控、编组、合并与转化接口 | LYR-01, LYR-02, LYR-03, LYR-04, LYR-05, LYR-06, LYR-07, LYR-08 | 8 |
| 3 | AI 认知升级与集成测试 | 在大模型提示词中全面暴露这 15 个新接口并进行整体连贯性对话测试 | ARC-02 | 1 |

### Phase Details

**Phase 1: 文档管理增强与架构扩充**
Goal: 在 `ps_tools` 中新增底层脚本执行支持，并实现所有文档级操作
Requirements: DOC-01, DOC-02, DOC-03, DOC-04, DOC-05, DOC-06, DOC-07, ARC-01
Success criteria:
1. `execute_jsx` 可以成功向 PS 注入 JS 脚本。
2. 能够按需创建新空白画布。
3. 能够正常打开本地图像并置入当前画布。
4. 可以触发 PSD 或 JPG 保存/导出功能。
5. 图像整体缩放和色彩模式切换正常运行。
6. 历史记录撤销重做功能有效。
7. 画布视图比例可正常调整。

**Phase 2: 图层进阶操作补全**
Goal: 全面实现所有针对图层和图层组的高级操控、编组、合并与转化接口
Requirements: LYR-01, LYR-02, LYR-03, LYR-04, LYR-05, LYR-06, LYR-07, LYR-08
Success criteria:
1. 可新建图层组并容纳指定图层。
2. 能调节任意图层的透明度和填充值。
3. 可正确修改图层混合模式。
4. 可按绝对坐标或相对位移移动图层。
5. 向下合并、合并可见和拼合图像这 3 个合并能力均正常。
6. 图层复制操作有效。
7. 栅格化文字/智能对象图层有效。
8. 普通图层转化为智能对象操作成功（依赖 JSX）。

**Phase 3: AI 认知升级与集成测试**
Goal: 在大模型提示词中全面暴露这 15 个新接口并进行整体连贯性对话测试
Requirements: ARC-02
Success criteria:
1. `backend/agent.py` 中注册的 tools 结构完整包含 15 个新 API。
2. 大模型能正确区分 `resize_canvas` 和 `resize_image` 的使用场景。
3. 连贯自然语言指令可一次性成功触发多个新接口完成复合操作（如：置入图片并转智能对象）。
