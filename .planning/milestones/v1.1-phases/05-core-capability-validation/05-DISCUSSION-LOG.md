# Phase 5 Discussion Log: 验证核心功能与事件机制

**Date:** 2026-06-13
**Phase:** 5 — Core Capability Validation
**Areas Discussed:** 4

---

## Area 1: DOM API 与 batchPlay 的边界划分策略

**Options Presented:**
1. DOM 优先 — 尽可能用 DOM API，只在 DOM 不支持时才降级到 batchPlay
2. batchPlay 优先 — 所有文档修改操作用 batchPlay，DOM 仅用于读取属性
3. 混合策略 — 在本次 PoC 中每个工具同时测试 DOM 和 batchPlay 两种实现，比较后再决定

**User Selection:** 采纳了 Agent 推荐的混合策略

**Notes:** Agent 推荐混合策略的理由：(1) DOM API 覆盖不全，部分复杂操作可能不支持；(2) batchPlay 是万能底线；(3) PoC 阶段正好适合做对比，为后续全面迁移提供数据支撑。

---

## Area 2: 核心操作 PoC 验证的范围与深度

**Options Presented:**
1. 全量测试 11 个工具
2. 按分层抽样（每层挑 1-2 个代表）
3. 只测复杂层 + 中间层

**User Selection:** 采纳了 Agent 推荐的全量测试 11 个工具

**Notes:** Agent 推荐全量测试的理由：(1) 研究里程碑本身目标就是全面梳理能力；(2) 11 个工具数量不多，简单层验证很快；(3) 完整对照表的价值远大于抽样推断。

---

## Area 3: PS 事件反向推送的目标范围

**Options Presented:**
1. 图层选择变化
2. 文档打开/关闭
3. 画布尺寸变更
4. 历史记录步进 (Undo/Redo)
5. 仅测试图层选择变化

**User Selection:** 采纳了 Agent 推荐的图层选择变化 + 文档打开/关闭

**Notes:** Agent 推荐两类事件的理由：(1) 图层选择变化是 AI 助手最依赖的上下文；(2) 文档打开/关闭对系统健壮性有直接价值；(3) 画布尺寸和历史步进目前价值有限，可后续按需添加。

**Deferred Ideas:**
- 画布尺寸变更事件
- 历史记录步进 (Undo/Redo) 事件

---

## Area 4: 测试结果的输出与记录方式

**Options Presented:**
1. 完整对照表 — 结构化 Markdown 文档，每工具一行对比 COM/DOM/batchPlay
2. 简洁日志 — 仅记录通过/失败和关键注意事项

**User Selection:** 完整对照表

**Notes:** 用户直接选择了完整对照表方案。产出文件为 `05-CAPABILITY-MATRIX.md`。
