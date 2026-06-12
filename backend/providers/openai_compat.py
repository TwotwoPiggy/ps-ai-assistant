import json
from typing import List, Dict, Any, Tuple
from openai import AsyncOpenAI
from .base import BaseProvider

class OpenAICompatProvider(BaseProvider):
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url or "https://api.openai.com/v1"
        self.model = model
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    @property
    def supports_vision(self) -> bool:
        # 针对常见不支持视觉的模型进行判定
        model_lower = self.model.lower()
        url_lower = self.base_url.lower()
        if "deepseek" in model_lower or "deepseek" in url_lower:
            return False
        # 如果是 qwen 纯文本模型
        if "qwen" in model_lower and "vl" not in model_lower:
            # 阿里千问普通模型有些不支持多模态，需使用 qwen-vl-* 系列。
            # 这里保守起见，如果非 vl 系列，则认为不支持 vision
            return False
        return True

    async def chat(self, 
                  messages: List[Dict[str, Any]], 
                  tools: List[dict], 
                  system_prompt: str) -> Tuple[str, List[dict]]:
        # 1. 处理消息多模态降级
        processed_messages = []
        
        # 首先注入系统提示词
        if system_prompt:
            processed_messages.append({"role": "system", "content": system_prompt})
            
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            
            # 如果是 tool 角色，需要携带 tool_call_id 和 name
            new_msg = {"role": role}
            if role == "tool":
                new_msg["tool_call_id"] = msg.get("tool_call_id")
                new_msg["name"] = msg.get("name")
                
            # 处理 tool_calls 字段的兼容 (assistant 发出的 tool_calls)
            if "tool_calls" in msg:
                new_msg["tool_calls"] = msg["tool_calls"]

            if isinstance(content, list):
                if not self.supports_vision:
                    # 降级处理：提取文本，丢弃或用占位符替换图片
                    text_parts = []
                    for part in content:
                        if part.get("type") == "text":
                            text_parts.append(part.get("text", ""))
                        elif part.get("type") == "image_url":
                            text_parts.append("[画布截图]")
                    new_msg["content"] = " ".join(text_parts)
                else:
                    new_msg["content"] = content
            else:
                new_msg["content"] = content
                
            processed_messages.append(new_msg)

        # 2. 构建 API 参数
        kwargs = {
            "model": self.model,
            "messages": processed_messages
        }
        
        if tools:
            kwargs["tools"] = tools

        # 3. 发送请求
        response = await self.client.chat.completions.create(**kwargs)
        
        choice = response.choices[0]
        reply_text = choice.message.content or ""
        
        tool_calls_result = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except Exception:
                    args = tc.function.arguments
                tool_calls_result.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "args": args
                })
                
        return reply_text, tool_calls_result
