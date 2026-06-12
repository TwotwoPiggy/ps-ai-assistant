# 多提供商架构研究总结

*综合自 STACK.md, FEATURES.md, ARCHITECTURE.md, PITFALLS.md*

## 1. 技术栈变更
- **新增核心依赖**: `openai>=2.41.1` (一个 SDK 覆盖所有非 Gemini 供应商)
- **双引擎策略**: Gemini 继续使用原生 `google-genai` SDK，DeepSeek/Qwen/MiMo/自定义统一使用 `openai` SDK。不推荐引入各家原生 SDK。

## 2. 核心特性对比与挑战
- **工具定义差异**: Gemini 靠原生函数推断 schema；OpenAI 兼容接口必须手动提供 JSON Schema 格式。这是最大的改造点，需要从现有的 Python 方法动态生成 OpenAPI 格式的 JSON Schema。
- **消息格式差异**: Gemini 历史为 `types.Content` 对象；OpenAI 格式为标准 `dict` ({"role": "user", "content": "..."})。
- **视觉能力断层**: 
  - Gemini / Qwen-VL / MiMo-v2.5: 原生支持多模态，图像数据可随 Prompt 发送。
  - DeepSeek: 主流文本/推理模型**不支持**图片。使用此 Provider 时无法分析画布截图，需降级。
- **推理模型陷阱 (Thinking)**: DeepSeek R1 和 Qwen 的思维模式与 Tool Calling 的交互可能导致 JSON 解析异常。建议针对 PS 工具交互场景**默认关闭** thinking mode 或做特殊容错。

## 3. 架构设计方向
- **Strategy Pattern (策略模式)**: 
  - `PhotoshopAgent` 作为协调层
  - 下设 `BaseProvider` 接口
  - 分离为 `GeminiProvider` 和 `OpenAICompatProvider` 两个主要实现
- **解耦操作**: 将原先混在 Agent 类中的 11 个 PS COM 操作拆分到独立的 `tools/ps_tools.py` 中。
- **内部统一格式**: 采用更标准的 OpenAI 字典格式作为系统内部交互标准，GeminiProvider 负责将其转换为 Gemini 对象。

## 4. 安全与配置扩展
- 前端配置从"1个Key+1个模型"扩展为"预置厂商下拉列表 + Key + BaseURL(可选) + Model"
- 需要修改 `ai_config` WebSocket 接口以支持新的配置结构。
- 考虑到前端会拉取配置，务必在服务端向前端返回配置时进行 API Key **脱敏**（如截断显示后四位），防止安全泄漏。
