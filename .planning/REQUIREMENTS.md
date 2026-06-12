# Requirements: PS AI Assistant

**Defined:** 2026-06-12
**Core Value:** 用户可以用自然语言直接控制 Photoshop，AI 自动理解意图并执行对应的 PS 操作。

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Provider Abstraction (架构重构)

- [x] **ARCH-01**: 从 `agent.py` 抽离 PS 工具逻辑到独立的工具注册表 `tools/ps_tools.py` 中。
- [x] **ARCH-02**: 开发 `tools/schema.py` 动态将 Python 工具方法解析为 OpenAI JSON Schema。
- [x] **ARCH-03**: 设计并实现 `BaseProvider` 抽象接口，统一化 `chat`, `format_tool_results`, `inject_image`。
- [x] **ARCH-04**: 实现 `GeminiProvider` 适配器（保留 `google-genai` SDK 原生功能）。
- [x] **ARCH-05**: 实现 `OpenAICompatProvider` 适配器以支持统一的 OpenAI SDK 规范。

### Provider Integration (预置与自定义厂商)

- [x] **PROV-01**: 支持预置厂商 DeepSeek（`api.deepseek.com`）并 handle 其 tool choice 怪癖。
- [x] **PROV-02**: 支持预置厂商 通义千问 Qwen（`dashscope.aliyuncs.com`）。
- [x] **PROV-03**: 支持预置厂商 MiMo（`api.xiaomimimo.com`）。
- [x] **PROV-04**: 支持用户配置自定义 OpenAI 兼容 Provider（手动输入 baseUrl + apiKey）。
- [x] **PROV-05**: 处理 Providers 的视觉能力差异（拦截不支持视觉的厂商避免崩溃）。

### Configuration & UI (配置与界面)

- [x] **CONF-01**: 后端 `config.py` 数据结构支持多 Provider 保存（支持旧版配置自动迁移）。
- [x] **CONF-02**: 后端接口在返回配置到前端时对 API Key 进行脱敏（仅显示前四后四），修复现有明文传输漏洞。
- [x] **CONF-03**: 前端配置面板改造：增加 Provider 下拉菜单（Gemini/DeepSeek/Qwen/MiMo/Custom）。
- [x] **CONF-04**: 前端配置面板改造：为非自定义的提供商自动填充 Base URL（锁定/隐藏或作为 Placeholder），用户仅需填 API Key 和模型名。

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### 高级集成
- **ADV-01**: 针对 DeepSeek 的 Reasoning Tokens (`<think>`) 在聊天界面前端展示支持。
- **ADV-02**: 自动化降级工作流：当不支持视觉的文本模型遇到图像需求时，自动调用预置的本地端/或低成本 Vision 模型生成图像描述文本。

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| 多 Provider 同时在线热切换聊天 | 复杂度极高，v1.0 限定为单例全局激活（在配置面板切换） |
| 非 Function Calling 模型的文本解析降级 | Photoshop 操作 100% 依赖精确参数，尝试用纯文本正则提取不可靠 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| ARCH-01 | Phase 1 | Complete |
| ARCH-02 | Phase 1 | Complete |
| ARCH-03 | Phase 1 | Complete |
| ARCH-04 | Phase 1 | Complete |
| ARCH-05 | Phase 1 | Complete |
| PROV-01 | Phase 2 | Complete |
| PROV-02 | Phase 2 | Complete |
| PROV-03 | Phase 2 | Complete |
| PROV-04 | Phase 2 | Complete |
| PROV-05 | Phase 2 | Complete |
| CONF-01 | Phase 1 | Complete |
| CONF-02 | Phase 1 | Complete |
| CONF-03 | Phase 3 | Complete |
| CONF-04 | Phase 3 | Complete |

**Coverage:**
- v1 requirements: 14 total
- Mapped to phases: 14
- Unmapped: 0 ✓

---
*Requirements defined: 2026-06-12*
*Last updated: 2026-06-12 after roadmap creation*
