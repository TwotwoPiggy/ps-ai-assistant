# Roadmap

**Milestone:** v1.0
**Goal:** 多 Provider 支持（Gemini、DeepSeek、Qwen、MiMo 及自定义 OpenAI 兼容）

## Execution Phases

| Phase | Name | Goal | Requirements | Success Criteria |
|-------|------|------|--------------|------------------|
| 1 | **架构与接口重构** | 1/1 | Complete   | 2026-06-12 |
| 2 | **集成预置厂商** | 1/1 | Complete   | 2026-06-12 |
| 3 | **前端配置面板改造** | 让用户能在 UI 上直观选择 Provider、填入 API Key 和配置 Base URL | CONF-03, CONF-04 | 3 |

---

## Phase Details

### Phase 1: 架构与接口重构
**Goal:** 建立 BaseProvider 抽象，适配 Gemini 与通用 OpenAI 接口
**Requirements:** ARCH-01, ARCH-02, ARCH-03, ARCH-04, ARCH-05, CONF-01, CONF-02

**Success Criteria:**
1. 工具方法成功从 `agent.py` 抽离，原 Gemini 调用逻辑在新架构下保持正常工作。
2. 成功实现 Python 方法到 OpenAI JSON Schema 的动态转换，并在日志中验证格式。
3. 后端 `config.py` 支持新的嵌套结构，前端拉取时 API Key 显示为 `****1234` 格式。

### Phase 2: 集成预置厂商
**Goal:** 实现对 DeepSeek, Qwen, MiMo 和自定义厂商的差异化支持及容错
**Requirements:** PROV-01, PROV-02, PROV-03, PROV-04, PROV-05

**Success Criteria:**
1. Qwen-VL 和 MiMo 能够正常接收画布截图并进行多轮函数调用。
2. DeepSeek (文本模型) 接收请求时能够安全忽略视觉输入并正常进行工具调用。
3. 任何自定义 Base URL (支持 OpenAI 规范) 都可直接进行工具对话。

### Phase 3: 前端配置面板改造
**Goal:** 让用户能在 UI 上直观选择 Provider、填入 API Key 和配置 Base URL
**Requirements:** CONF-03, CONF-04

**Success Criteria:**
1. UI 上新增 Provider 下拉选框，且能正确显示当前生效的厂商。
2. 选中预置厂商时，Base URL 字段自动填充或隐藏，选中 Custom 时允许手动输入。
3. 配置能够成功持久化到后端的 `ai_config.json`，且能立即生效进行聊天。
