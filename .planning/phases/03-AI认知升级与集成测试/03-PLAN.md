# Phase 3: AI 认知升级与集成测试 - Plan

**Status:** Code implemented, awaiting UAT verification

## 1. 目标

在大模型提示词中全面暴露这 15 个新接口，并将提示词从代码中剥离、外置为独立的 Markdown 文本文件，同时增加区分易混淆操作和复合连贯操作的强力引导规则。

## 2. 计划与步骤

### 2.1 任务 1: 创建独立系统提示词文件
- **File:** `backend/prompts/system_prompt.md` (NEW)
- **Description:** 创建一个全新的系统提示词文件，内容基于原有的提示词进行扩充和升维。
- **Requirements:**
  1. 明确大模型可调用的图层操作与文档操作全集。
  2. 针对 `resize_canvas` 与 `resize_image` 添加明确的区分规则和使用场景描述。
  3. 增加对于“多步复合操作”的明确指引，要求在处理复杂指令时按逻辑顺次执行。

### 2.2 任务 2: 改造 agent.py 以动态读取提示词
- **File:** `backend/agent.py`
- **Description:** 替换硬编码的 `system_instruction` 字符串。
- **Requirements:**
  1. 在 `PhotoshopAgent.handle_message` 或初始化阶段，读取 `backend/prompts/system_prompt.md` 文件内容。
  2. 如遇到文件读取失败，应有默认的 fall-back 机制（或报错提示）。
  3. 传递给 Provider 接口作为系统提示词。

### 2.3 任务 3: 系统连贯性整合测试 (UAT)
- **File:** N/A (Manual Execution)
- **Description:** 在前端界面通过一系列的自然语言进行集成测试。
- **Requirements:**
  1. 测试易混淆词汇：“放大画布” vs “放大图片”。
  2. 测试连贯指令：“新建一个名为测试的图层，并将其转化为智能对象”。
  3. 测试查询类结合执行类指令。
