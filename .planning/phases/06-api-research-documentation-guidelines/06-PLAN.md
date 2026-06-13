# Phase 06: API Research & Documentation Guidelines Plan

## Context
本阶段目标是汇总 Phase 05 的技术探索成果，并采取“先宽后窄”的策略输出全景 UXP 接口能力字典，同时制定开发防踩坑指南，为后续里程碑的架构重构和业务开发奠定基础，并将其部分转化为大模型系统的开发上下文。

## Requirements
- **CAP-04**: 输出全量 UXP 支持的 API 操作清单与评估。
- **GUIDE-01**: 制定 UXP 开发陷阱的防范规范 (沙盒限制、性能卡顿)。

## Execution Steps

### 1. 基础设施准备
- [ ] 创建 `docs/` 目录，用于归档系统技术文档。

### 2. 梳理全量 UXP API 清单 (CAP-04)
- [ ] 摸底并汇总全量 UXP API 功能全景图：在 `docs/UXP-API-DICTIONARY.md` 中梳理并记录 UXP 当前暴露的所有领域能力（涵盖基础图层、选区操作，以及滤镜、3D、动画等高级功能），形成完整的全景清单。
- [ ] 提炼核心高频工具：从上述全景清单中筛选出大模型最常用的高频操作（包括 Phase 05 已验证的 11 个核心操作：`get_layer_tree`, `get_canvas_snapshot`, `create_layer`, `delete_layer`, `rename_layer`, `set_layer_visibility`, `reorder_layer`, `adjust_brightness_contrast`, `crop_canvas`, `resize_canvas`, `flip_image`），详细标注其推荐调用策略（DOM API 优先或 batchPlay 降级）及适用场景。
- [ ] 生成精简版工具 Schema：创建 `docs/uxp_tools_schema.json` 文件，仅针对精简后的高频核心工具定义符合大模型 Function Calling 标准的 JSON Schema。

### 3. 输出 UXP 防陷阱开发指南 (GUIDE-01)
- [ ] 创建 `docs/UXP-GUIDELINES.md` 文件，详细论述以下四个核心开发铁律：
  1. **存储沙盒限制**: 文件 I/O 必须遵循 UXP 安全沙盒机制，获取快照时须导出至临时文件夹转化为 Base64，且必须清理临时文件。
  2. **事件防抖 (Debounce)**: 注册 PS 回调（如选中图层）推送至 Python 时必须实现防抖，以防高频事件风暴堵塞 Socket.IO 队列。
  3. **`executeAsModal` 调度**: 凡涉及修改文档状态的操作必须进入统一的 Modal 队列（`modalQueue`），防止锁冲突死锁。
  4. **API 混合策略**: 业务封装优先选用具备类型的 UXP DOM API v2，未覆盖的功能才使用 batchPlay 兜底。

### 4. 固化大模型全局开发上下文
- [ ] 创建/更新 `.planning/GEMINI.md` 文件。
  - [ ] 将上述 `UXP-GUIDELINES.md` 中的 4 条核心铁律精炼为强制性的 AI 编码指令（System Prompt Context），确保未来由 AI 辅助开发 UXP 功能时自动规避以上陷阱。

### 5. 验收环节 (Verification)
- [ ] 确认 `docs/UXP-API-DICTIONARY.md` 是否完成了对 UXP 全量支持功能（含滤镜、高级功能等）的全景梳理与能力评估。
- [ ] 确认 `docs/UXP-API-DICTIONARY.md` 是否明确标识并详细说明了精简出的核心高频基础操作。
- [ ] 确认 `docs/uxp_tools_schema.json` 是否为合法的 JSON Schema 格式，且只包含针对高频精简工具的定义。
- [ ] 确认 `.planning/GEMINI.md` 是否包含 4 项核心开发铁律，能够为 AI 提供准确的防坑指引。

<threat_model>
No significant security boundaries crossed in this phase. The tasks exclusively involve generating internal documentation, metadata schemas, and AI coding guidelines without introducing new runtime behavior, handling external inputs, or modifying the application architecture.
</threat_model>
