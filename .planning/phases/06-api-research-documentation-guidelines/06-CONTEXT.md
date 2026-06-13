# Phase 6 Context

## Domain
整理全量 API 清单与输出开发规范 (Research Documentation & Guidelines) — 梳理 UXP 支持的所有 API 清单，并输出防范 UXP 开发陷阱的规范。

## Canonical refs
- 目前暂无外部指定的参考文档，本阶段将生成新的参考文档。

## Decisions

### 1. API 清单的覆盖范围 (API Scope)
- 采取先宽后窄的策略：先全面摸底、梳理所有 UXP 暴露的功能（包含滤镜、3D、动画等高级功能），形成完整的全景清单。
- 然后从中筛选出大模型最常用的高频操作（如图层、选区、图像处理等），作为精简版的工具集，以保持高效和防范幻觉。

### 2. API 清单的输出格式 (API Format)
- 两者兼顾：
  - 生成用于人类阅读的 **Markdown 全景字典**。
  - 导出一份精简后的 **JSON Schema** 专门供大模型加载为 Tools Context。

### 3. 开发规范的落地形式 (Guidelines Location)
- 结合两种形式：
  - 建立一个独立的规范文档（如 `docs/UXP-GUIDELINES.md`），作为人类开发者和模型的系统性查阅手册。
  - 将防范沙盒限制、同步阻塞等核心铁律同步写入项目根目录的 `.planning/GEMINI.md`，确保它作为大模型后续写代码时的全局强制上下文。

## Code context
- 依赖于上一阶段测试输出的结论文件：`.planning/phases/05-core-capability-validation/05-CAPABILITY-MATRIX.md`。
- UXP 核心工具文件：`frontend/src/modalQueue.ts`, `frontend/src/uxpTools.ts`, `frontend/src/batchPlayTools.ts` 等。
