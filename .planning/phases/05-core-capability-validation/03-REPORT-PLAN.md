---
wave: 3
depends_on:
  - 02-TEST-PLAN.md
files_modified:
  - .planning/phases/05-core-capability-validation/05-CAPABILITY-MATRIX.md
autonomous: true
---

# Phase 5: 验证核心功能与事件机制 - Reporting

## Goal
依据对比测试数据与事件机制的开发成果，生成最终的核心能力矩阵评估报告，指导后续的架构大迁徙。

## requirements
CAP-01, CAP-02, CAP-03

## must_haves
- 输出格式化好的 `.planning/phases/05-core-capability-validation/05-CAPABILITY-MATRIX.md` 文件
- 报告中必须明确每一个被测工具推荐采用的方案（DOM、batchPlay 或是 混合）

## Tasks

### [ ] Task 1: 汇总测试结果并生成评估矩阵
**requirements**: CAP-01, CAP-02, CAP-03

<read_first>
- .planning/phases/05-core-capability-validation/05-RESEARCH.md
- tests/capability_results.json
</read_first>

<action>
1. 读取并在内存中解析 `tests/capability_results.json` 中的执行日志与表现数据（如果测试脚本没有自动获取到数据，则根据代码和测试情况进行合理的推断总结）。
2. 在 `.planning/phases/05-core-capability-validation/` 目录下创建 `05-CAPABILITY-MATRIX.md` 文档。
3. 按照 Phase 5 的要求，编写对比表格，表格列包括：
   - 工具名
   - COM 方案状态
   - UXP DOM 方案测试状态
   - batchPlay 方案测试状态
   - 推荐落地方案（混合策略评估结论）
   - 备注与限制（沙盒、性能）
4. 在文档最后增加一个独立段落记录“PS 事件反向推送”的验证结论（CAP-03），说明监听 `select`, `open`, `close` 等事件的可靠性及后续计划。
</action>

<acceptance_criteria>
- `.planning/phases/05-core-capability-validation/05-CAPABILITY-MATRIX.md` 文档成功生成且排版符合 Markdown 规范。
- 文档内部含有 11 个工具在三种方案（COM/DOM/batchPlay）下的明细对比表格，并给出了明确的“推荐方案”。
- 文档中包含了事件机制测试验证的结论总结。
</acceptance_criteria>
