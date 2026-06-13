# Phase 3: AI 认知升级与集成测试 - Discussion Log (Assumptions Mode)

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions captured in CONTEXT.md — this log preserves the analysis.

**Date:** 2026-06-13
**Phase:** 03-AI认知升级与集成测试
**Mode:** assumptions
**Areas analyzed:** 自动暴露工具, 系统提示词升级策略, 连贯性与复合操作指导

## Assumptions Presented

### 自动暴露工具
| Assumption | Confidence | Evidence |
|------------|-----------|----------|
| `registry.py` 的设计已经天然支持了新接口的自动暴露，无需再修改接口结构。 | Confident | `backend/agent.py` 中 `tools_schema = registry.get_openai_schemas()` 的自动加载机制 |

### 系统提示词升级策略
| Assumption | Confidence | Evidence |
|------------|-----------|----------|
| 需要修改 `agent.py` 中的 `system_instruction`，补全针对新能力的约束规则。 | Confident | `backend/agent.py` 中目前硬编码的简短提示词，且 Phase 3 的目标要求区分相似功能 |

### 连贯性与复合操作指导
| Assumption | Confidence | Evidence |
|------------|-----------|----------|
| 我们会在提示词里加入“多步规划”的指导：遇到复合意图时，先拉取图层树，再顺次执行。 | Confident | Phase 3 的复合操作连贯性要求 |

## Corrections Made

### 系统提示词外置化
- **Original assumption:** 修改 `agent.py` 中的 `system_instruction` 字符串。
- **User correction:** 将系统提示词外置为一个单独的 markdown/text 文件，而不是硬编码在 agent.py 里。
- **Reason:** 方便集中管理和迭代，避免在核心代码中混入大段文字。
