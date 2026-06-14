# Phase 1 Discussion Log

**Date:** 2026-06-12
**Phase:** 架构与接口重构

## Question 1: 内部消息格式
**Options Presented:**
- [x] 直接使用 OpenAI 的 dict 格式（`{"role": "user", "content": "..."}`）作为内部标准，Gemini 在发送前再转换为 `types.Content`
- [ ] 使用 Pydantic Model / Dataclass 定义内部 Message 类型，所有 Provider 强制转换为此类型

**Notes:**
User chose the OpenAI dict format for simplicity, as it acts as a universally understood lowest common denominator across APIs.

## Question 2: 配置存储加密
**Options Presented:**
- [x] 暂时保持 `ai_config.json` 明文存储（只要前端脱敏即可），后续版本再考虑加密
- [ ] 引入 `keyring` 或系统级加密将各个 API Key 独立存储，`ai_config.json` 仅保留非敏感配置

**Notes:**
User preferred to keep things simple with plaintext JSON storage, as long as the UI stops leaking the keys via WebSockets (which CONF-02 covers).

## Question 3: 工具执行上下文
**Options Presented:**
- [x] (推荐) 通过参数传递（如 `kwargs` 或 `Context` 对象）：工具函数签名显式接收所需上下文，最安全且利于测试。
- [ ] 使用上下文变量（如 `contextvars`）：代码较简洁，但容易增加隐式耦合。

**Notes:**
Recommended dependency injection to pass `sid` to functions. The user agreed. This ensures concurrency safety for WebSockets.
