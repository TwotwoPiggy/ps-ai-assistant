# Phase 1 Plan: 架构与接口重构

**Phase Goal:** 建立 BaseProvider 抽象，适配 Gemini 与通用 OpenAI 接口
**Status:** Complete

## 1. 现状分析与实现思路

当前项目强耦合了 `google-genai` SDK，PhotoshopAgent 直接初始化 Client，并在其中混杂了对话维护、历史压缩与工具执行的逻辑。

为了满足多供应商支持（Gemini + OpenAI 兼容），必须进行解耦。我们将采用 **Strategy (策略) + Adapter (适配器) 模式**，并将所有 PS 工具抽取到独立的模块中，以统一 JSON Schema 的形式供给 OpenAI 规范的模型调用。由于 Gemini 支持使用原生 Python 函数推断 Schema，Gemini Adapter 可以继续使用原生功能，也可以统一转换为 OpenAI 格式。为了架构统一且满足讨论阶段决定的「内部统一使用 OpenAI dict 格式」，我们将**全部**统一采用 OpenAPI 的 JSON Schema。

## 2. 详细技术方案

### 2.1 依赖与配置扩展
1. 修改 `backend/requirements.txt`：
   - [x] 新增 `openai>=2.41.1`。
2. 重构 `backend/config.py`：
   - [ ] 扩展 Config 数据类，支持 `providers` 字典（包含 gemini, deepseek, qwen, mimo, custom），存储 `api_key`, `base_url`, `model`。
   - [ ] 添加向后兼容逻辑，读取现有的 `gemini_api_key` 格式并迁移为新格式。

### 2.2 核心抽象层 (`backend/providers/base.py`)
1. 定义 `BaseProvider` 抽象类：
   - [ ] 包含 `chat(messages, tools, system_prompt)` 方法，返回 `(final_text, tool_calls)`。
   - [ ] 包含 `format_tool_results(tool_calls, results)` 方法。
   - [ ] 包含 `inject_image(base64_data, mime_type)` 方法。
   - [ ] 定义 `supports_vision` 属性。

### 2.3 工具集解耦 (`backend/tools/`)
1. 创建 `ps_tools.py`：
   - [ ] 将 `PhotoshopAgent` 中的 11 个操作方法（如 `get_layer_tree`, `create_layer` 等）迁移为纯函数。
   - [ ] 每个工具方法需接收 `ctx` 参数（用于 WebSocket 回调和 SID 传递）。
2. 创建 `schema.py`：
   - [ ] 开发 `python_method_to_openai_schema` 函数，通过 `inspect` 提取方法的 `docstring` 和类型提示，自动生成满足 OpenAPI 规范的 JSON Schema 工具描述。
3. 创建 `registry.py`：
   - [ ] 实现 `ToolRegistry`，统筹注册工具函数并暴露出统一的执行接口 `execute_tool(name, args, ctx)`。

### 2.4 Provider 适配器实现
1. 实现 `OpenAICompatProvider` (`backend/providers/openai_compat.py`)：
   - [ ] 使用 `openai.OpenAI` 初始化。
   - [ ] `chat()` 实现标准 OpenAI 函数调用流（支持并行工具）。
   - [ ] 处理图像格式 `{"type": "image_url", "url": "data:image/jpeg;base64,..."}`。
2. 实现 `GeminiProvider` (`backend/providers/gemini.py`)：
   - [ ] 继续使用 `google.genai.Client`。
   - [ ] **关键转换**：在发送前，将内部的 `{"role": "user", "content": "..."}` 格式转换为 `types.Content`。
   - [ ] **工具转换**：将传入的 OpenAI Schema 转换为 `types.Tool` 或维持传递原生方法。
   - [ ] 处理图像格式 `Part.from_bytes(data, mime_type)`。

### 2.5 PhotoshopAgent 重构
1. 简化 `backend/agent.py`：
   - [ ] 移除所有 PS 特定的工具逻辑。
   - [ ] 引入 `ToolRegistry` 和 `ProviderRegistry`。
   - [ ] 内部状态 `self.conversations` 统一存储 OpenAI 格式的 list[dict]。
   - [ ] 实现核心对话循环（生成响应 -> 执行工具 -> 生成最终回复），所有外部调用通过 Provider 接口进行。

### 2.6 安全性强化
1. 修改 `backend/server.py`：
   - [ ] 在响应前端的 `ai_config` 事件时，拦截所有的 API Key，只返回 `****1234` 格式以脱敏。
   - [ ] 在前端发送 `save_config` 事件时，妥善处理脱敏 Key（如果收到的是脱敏格式，不覆盖原有配置）。

## 3. 验证计划 (Verification)
1. **启动测试**：应用能成功运行不报错。
2. **Gemini 回归测试**：使用 Gemini 能正常发送画布截图并完成工具调用（由于这是纯后端重构阶段，主要验证接口格式正确）。
3. **OpenAI SDK 验证**：配置任意兼容服务（如模拟服务），验证 `chat` 和 JSON Schema 生成工作正常。
4. **安全验证**：拦截 WebSocket 流量，验证配置拉取时不会泄露完整的 API Key。

## 4. 执行步骤分解

- [ ] **Step 1**: 更新 `requirements.txt` 并重构 `config.py`。
- [ ] **Step 2**: 开发 `backend/tools/` 模块（解耦工具并实现 Schema 自动生成）。
- [ ] **Step 3**: 开发 `backend/providers/` 抽象与适配器。
- [ ] **Step 4**: 重构 `backend/agent.py` 为瘦协调层。
- [ ] **Step 5**: 修改 `backend/server.py` 以集成新配置和实现 Key 脱敏。
