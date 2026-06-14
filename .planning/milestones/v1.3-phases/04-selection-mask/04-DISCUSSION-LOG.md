# Discussion Log: Phase 04 - 选区与蒙版控制

## Discussed Areas

### 1. 选区模式与多重选区叠加机制
- **Options presented:** 支持组合操作 vs 简单即可
- **Selected:** 支持组合操作：增加 `selection_mode` 参数（支持 replace/add/subtract/intersect），默认 replace。
- **Notes:** 允许大模型通过多次工具调用组合复杂选区。

### 2. 智能选区的容错与执行超时机制
- **Options presented:** 明确捕获并反馈给 AI vs 直接抛出底层异常
- **Selected:** 明确捕获并反馈给 AI：针对此类易错操作，捕获异常并返回明确的错误结果。
- **Notes:** 让大模型充当“解释者”，安抚用户。

### 3. 选区存为通道的命名规则
- **Options presented:** 由 AI 提供 vs 系统自动命名
- **Selected:** (Recommended) 由 AI 提供，并带有后备机制。
- **Notes:** 发挥 LLM 语义提取能力，同时兼顾健壮性。

### 4. 蒙版应用的破坏性保护
- **Options presented:** 提供但限制 vs 自由放开 vs 完全屏蔽
- **Selected:** 提供但限制：要求大模型在调用时传入 `force_apply: true` 类似的安全参数。
- **Notes:** 防范“应用蒙版”带来的像素永久丢失风险。
