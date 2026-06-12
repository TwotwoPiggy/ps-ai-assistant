# 多供应商架构设计研究

> 研究日期：2026-06-12
> 目标：为 ps-ai-assistant 设计多 Provider 抽象层架构

---

## 1. 当前架构分析

### 单一耦合点

当前 `PhotoshopAgent` 类直接依赖 `google-genai` SDK：

```
PhotoshopAgent (agent.py)
├── __init__: genai.Client(api_key) — 直接创建 Gemini 客户端
├── handle_message: 
│   ├── 构建 tools=[] 使用 Python 方法引用 — Gemini 专有
│   ├── 管理 self.conversations[sid] 使用 types.Content — Gemini 专有
│   ├── 调用 client.models.generate_content() — Gemini 专有
│   ├── 解析 response.function_calls — Gemini 专有
│   ├── 构建 Part.from_function_response() — Gemini 专有
│   └── 注入 Part.from_bytes() 图像 — Gemini 专有
└── 11 个工具方法: get_layer_tree, create_layer, ... — 纯业务逻辑，无 SDK 依赖 ✅
```

**关键发现：工具方法本身（PS COM 操作）与 SDK 完全解耦。**

---

## 2. 推荐架构：Strategy + Adapter 模式

### 2.1 整体架构

```
backend/
├── agent.py            → PhotoshopAgent (瘦协调层)
├── providers/
│   ├── __init__.py     → ProviderRegistry
│   ├── base.py         → BaseProvider (抽象接口)
│   ├── gemini.py       → GeminiProvider (google-genai SDK)
│   ├── openai_compat.py→ OpenAICompatProvider (openai SDK)
│   └── registry.py     → 预置 provider 注册表
├── tools/
│   ├── __init__.py
│   ├── registry.py     → ToolRegistry (统一工具注册)
│   ├── schema.py       → 工具 schema 生成器（Python → JSON Schema）
│   └── ps_tools.py     → PS 操作工具（从 agent.py 提取）
├── config.py           → 多供应商配置管理
└── server.py           → WebSocket 服务器
```

### 2.2 核心接口定义

```python
# providers/base.py
from abc import ABC, abstractmethod
from typing import Any

class BaseProvider(ABC):
    """AI Provider 统一接口"""
    
    @abstractmethod
    def __init__(self, api_key: str, model: str, base_url: str = None, **kwargs):
        pass
    
    @abstractmethod
    async def chat(
        self,
        messages: list[dict],   # 内部统一消息格式
        tools: list[dict],      # OpenAI 格式 JSON Schema
        system_prompt: str,
        status_callback=None
    ) -> tuple[str | None, list[dict] | None]:
        """
        返回: (final_text, tool_calls)
        - 如果模型返回文本：(text, None)
        - 如果模型要求工具调用：(None, [{name, arguments, id}])
        """
        pass
    
    @abstractmethod
    def format_tool_results(
        self, 
        tool_calls: list[dict],    # 原始 tool_calls
        results: list[dict]        # 工具执行结果
    ) -> list[dict]:
        """将工具执行结果格式化为供应商期望的消息格式"""
        pass
    
    @abstractmethod
    def inject_image(self, base64_data: str, mime_type: str) -> dict:
        """将图像数据格式化为供应商期望的消息 part"""
        pass
    
    @property
    @abstractmethod
    def supports_vision(self) -> bool:
        """该 provider/model 是否支持视觉输入"""
        pass
```

### 2.3 Gemini Provider

```python
# providers/gemini.py
class GeminiProvider(BaseProvider):
    """使用 google-genai 原生 SDK"""
    
    def __init__(self, api_key, model, **kwargs):
        from google import genai
        self.client = genai.Client(api_key=api_key)
        self.model = model
    
    async def chat(self, messages, tools, system_prompt, status_callback=None):
        # 将内部消息格式转换为 types.Content
        # 将 OpenAI JSON Schema tools 转换为 Python 函数引用
        # 或者：直接使用 Gemini 的原生 tool 定义方式
        ...
    
    def format_tool_results(self, tool_calls, results):
        # 构建 Part.from_function_response()
        ...
    
    def inject_image(self, base64_data, mime_type):
        # 构建 Part.from_bytes()
        ...
```

### 2.4 OpenAI Compatible Provider

```python
# providers/openai_compat.py
class OpenAICompatProvider(BaseProvider):
    """使用 openai SDK 的通用适配器"""
    
    def __init__(self, api_key, model, base_url, **kwargs):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
    
    async def chat(self, messages, tools, system_prompt, status_callback=None):
        # 直接使用 OpenAI 格式
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        ...
    
    def format_tool_results(self, tool_calls, results):
        # 构建 role="tool" + tool_call_id 消息
        ...
    
    def inject_image(self, base64_data, mime_type):
        # 构建 image_url content part
        return {
            "type": "image_url",
            "image_url": {"url": f"data:{mime_type};base64,{base64_data}"}
        }
```

---

## 3. 工具 Schema 转换策略

### 3.1 从 Python 方法生成 JSON Schema

```python
# tools/schema.py
import inspect
import json
from typing import get_type_hints

def python_method_to_openai_schema(method) -> dict:
    """从 Python 方法签名 + docstring 生成 OpenAI 格式 tool schema"""
    hints = get_type_hints(method)
    sig = inspect.signature(method)
    docstring = inspect.getdoc(method) or ""
    
    # 解析 docstring 中的 Args 部分获取参数描述
    param_descriptions = _parse_docstring_args(docstring)
    
    # 提取 description（docstring 第一行）
    description = docstring.split("\n")[0].strip()
    
    properties = {}
    required = []
    
    for name, param in sig.parameters.items():
        if name == "self":
            continue
        
        prop = {"type": _python_type_to_json_type(hints.get(name, str))}
        if name in param_descriptions:
            prop["description"] = param_descriptions[name]
        
        if param.default is inspect.Parameter.empty:
            required.append(name)
        
        properties[name] = prop
    
    return {
        "type": "function",
        "function": {
            "name": method.__name__,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    }
```

### 3.2 Gemini 保留原生方式

Gemini Provider 可以继续使用 Python 方法引用直接传给 SDK，无需转换。这保留了 Gemini 的自动推断优势。

---

## 4. 内部消息格式

采用 OpenAI 兼容的 dict 格式作为内部统一格式（因为它是最广泛支持的标准）：

```python
# 用户消息
{"role": "user", "content": "把图层变亮一些"}

# 带图片的用户消息  
{"role": "user", "content": [
    {"type": "text", "text": "分析画布"},
    {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
]}

# 助手文本回复
{"role": "assistant", "content": "已完成操作"}

# 助手工具调用
{"role": "assistant", "content": None, "tool_calls": [
    {"id": "call_xxx", "type": "function", "function": {"name": "...", "arguments": "..."}}
]}

# 工具结果
{"role": "tool", "tool_call_id": "call_xxx", "content": "{\"success\": true}"}
```

**Gemini Provider 负责在内部格式和 `types.Content` 之间双向转换。**

---

## 5. Provider 注册表

```python
# providers/registry.py
PROVIDER_PRESETS = {
    "gemini": {
        "name": "Google Gemini",
        "provider_class": "GeminiProvider",
        "base_url": None,  # 使用原生 SDK，无需 base_url
        "default_model": "gemini-2.5-flash",
        "models": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"],
        "supports_vision": True,
    },
    "deepseek": {
        "name": "DeepSeek",
        "provider_class": "OpenAICompatProvider",
        "base_url": "https://api.deepseek.com",
        "default_model": "deepseek-chat",
        "models": ["deepseek-chat", "deepseek-reasoner"],
        "supports_vision": False,
    },
    "qwen": {
        "name": "通义千问 (Qwen)",
        "provider_class": "OpenAICompatProvider",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen-max",
        "models": ["qwen-max", "qwen-plus", "qwen-turbo", "qwen-vl-plus"],
        "supports_vision": True,  # qwen-vl 系列
    },
    "mimo": {
        "name": "MiMo (小米)",
        "provider_class": "OpenAICompatProvider",
        "base_url": "https://api.xiaomimimo.com/v1",
        "default_model": "mimo-v2.5-pro",
        "models": ["mimo-v2.5-pro", "mimo-v2-flash"],
        "supports_vision": True,
    },
    "custom": {
        "name": "自定义 (OpenAI 兼容)",
        "provider_class": "OpenAICompatProvider",
        "base_url": None,  # 用户自行填写
        "default_model": "",
        "models": [],  # 用户自行填写
        "supports_vision": True,  # 默认假设支持
    }
}
```

---

## 6. 配置存储演进

```python
# 当前配置格式
{
    "gemini_api_key": "...",
    "model": "gemini-2.5-flash"
}

# 新配置格式
{
    "active_provider": "gemini",
    "providers": {
        "gemini": {
            "api_key": "...",
            "model": "gemini-2.5-flash"
        },
        "deepseek": {
            "api_key": "...",
            "model": "deepseek-chat"
        },
        "qwen": {
            "api_key": "...",
            "model": "qwen-max",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
        },
        "mimo": {
            "api_key": "...",
            "model": "mimo-v2.5-pro"
        },
        "custom": {
            "api_key": "...",
            "model": "gpt-4o",
            "base_url": "https://api.openai.com/v1"
        }
    }
}
```

**向后兼容**：检测旧格式（有 `gemini_api_key` 字段），自动迁移到新格式。

---

## 7. 改造影响评估

| 文件 | 改造范围 | 难度 |
|------|---------|------|
| `agent.py` | 拆分为 Agent + Provider + Tools 三层 | 🔴 高 |
| `config.py` | 扩展为多供应商配置 | 🟡 中 |
| `server.py` | 适配 provider 切换逻辑 | 🟡 中 |
| `frontend ChatPanel.tsx` | 配置面板 UI 改造 | 🟡 中 |
| 新增 `providers/` | 全新模块 | 🟠 新增 |
| 新增 `tools/` | 从 agent.py 提取 | 🟠 新增 |

### 建议拆分步骤

1. 提取工具方法到 `tools/ps_tools.py`（纯业务逻辑，无 SDK 依赖）
2. 实现 `tools/schema.py` 的 JSON Schema 生成器
3. 定义 `providers/base.py` 抽象接口
4. 实现 `providers/gemini.py`（重构现有逻辑）
5. 实现 `providers/openai_compat.py`（新增）
6. 重构 `agent.py` 为瘦协调层
7. 扩展 `config.py` 和 `server.py`
8. 改造前端配置面板
