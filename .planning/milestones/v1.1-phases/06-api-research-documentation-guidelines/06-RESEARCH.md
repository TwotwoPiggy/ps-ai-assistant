# Phase 06 Research: API Research & Documentation Guidelines

## 1. 目标与背景解读
Phase 06 的核心任务是将前一阶段 (Phase 05) 的 UXP 验证成果转化为**项目级系统资产**。要成功规划 (PLAN) 此阶段，必须理解以下关键目标：
- **输出全景清单 (CAP-04)**：从现有前端代码中梳理所有支持的 UXP API（如滤镜、图层等），并将其提炼为大模型可加载的 JSON Schema 工具集。
- **确立开发规范 (GUIDE-01)**：总结防陷阱开发指南，形成独立的 Markdown 文档，并将核心“铁律”同步写入 `.planning/GEMINI.md`（或 `GEMINI.md`），确保大模型在未来写代码时不会踩坑。

## 2. 现有 UXP 架构与能力基座 (依赖信息)
通过调研 `frontend/src` 中的代码及 Phase 05 的 `05-CAPABILITY-MATRIX.md` 报告，总结如下核心机制，这些是规范撰写的基础：

1. **统一串行队列 (`modalQueue.ts`)**：
   所有的 Photoshop 文档状态修改操作都必须包装在 `photoshop.core.executeAsModal` 中。为防冲突，前端实现了一个 `ModalQueue` 进行串行化调度。
2. **混合调用策略 (`uxpTools.ts` & `batchPlayTools.ts`)**：
   经 Phase 05 测试证实，系统采用混合策略 (Mixed Strategy)：
   - **优先 DOM API (UXP v2)**：如创建图层 (`create_layer`)、删除图层、画布调整等 CRUD 数据获取操作。
   - **动态降级 batchPlay**：通过 `_use_batchplay` 标志，在遇到复杂滤镜（如 `adjust_brightness_contrast`）等 DOM API 覆盖不完整的情况时，采用 `batchPlay` 实现。若 batchPlay 报错（如 `fallback:`），仍能平滑回退至 DOM API。
3. **已验证的核心工具清单**：
   目前已有 `get_layer_tree`, `get_canvas_snapshot`, `create_layer`, `delete_layer`, `rename_layer`, `set_layer_visibility`, `reorder_layer`, `adjust_brightness_contrast`, `crop_canvas`, `resize_canvas`, `flip_image` 这 11 种核心方法作为基石，它们将是清单文档的核心部分。

## 3. 防陷阱开发指南的核心内容 (Guide Topics)
在编写防陷阱规范时，必须涵盖且不限于以下四个方面：
- **存储沙盒与快照获取**：UXP 无法直接读取硬盘，像获取画布快照 (`get_canvas_snapshot`) 时，只能利用 `uxp.storage.localFileSystem.getTemporaryFolder()` 导出到临时文件，再转化为 `ArrayBuffer` 与 Base64，且必须清理临时文件。
- **状态同步与事件防抖**：监听 Photoshop 事件（如图层选中、文档开闭）推送给 Python 时，可能产生事件风暴。文档必须指出并规范**防抖 (Debounce)** 的实现原则，防止堵塞 Socket.IO 队列。
- **`executeAsModal` 死锁与阻塞**：规范什么场景必须进入 Modal 队列，什么场景（纯查询）可以避免 Modal，以防卡顿。
- **混合策略的 API 封装准则**：规范以后新增 PS 功能时，优先寻找 UXP DOM API，无 API 则通过 Action 监听抓取 batchPlay Descriptor 进行封装。

## 4. PLAN 阶段的落地步骤建议
结合以上研究，在 `gsd-plan-phase` 生成执行计划时，建议划分为以下几个具体步骤：
1. **提炼与编写工具清单**：创建 `docs/UXP-API-DICTIONARY.md`（或类似位置），并将这 11 个工具的使用方式及其 `tools_schema.json` 抽取并沉淀。
2. **编写开发指南文档**：创建 `docs/UXP-GUIDELINES.md`，深度梳理上述防陷阱策略。
3. **固化大模型上下文**：创建/更新项目全局提示词文件 `.planning/GEMINI.md`，将关于 `executeAsModal` 必选、Storage API 限制等几条致命的 UXP 铁律以精简指令形式注入，作为未来里程碑开发的基础上下文约束。
