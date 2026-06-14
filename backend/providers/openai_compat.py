import json
from typing import List, Dict, Any, Tuple, Callable, Awaitable
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
            return False
        return True

    async def chat(self, 
                  messages: List[Dict[str, Any]], 
                  tools: List[dict], 
                  system_prompt: str,
                  on_thinking_callback: Callable[[str], Awaitable[None]] = None) -> Tuple[str, List[dict]]:

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

        # 2. 构建 API 参数 (启用流式传输)
        kwargs = {
            "model": self.model,
            "messages": processed_messages,
            "stream": True
        }
        
        if tools:
            kwargs["tools"] = tools

        # 3. 发送请求并流式解析
        response_stream = await self.client.chat.completions.create(**kwargs)
        
        reply_text_parts = []
        tool_calls_chunks = {}
        
        async for chunk in response_stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            
            # 3.1 提取 DeepSeek R1 专属思考字段
            reasoning = getattr(delta, "reasoning_content", "") or ""
            if reasoning and on_thinking_callback:
                await on_thinking_callback(reasoning)
                
            # 3.2 提取文本内容
            content = delta.content or ""
            if content:
                reply_text_parts.append(content)
                
            # 3.3 提取流式工具调用切片
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in tool_calls_chunks:
                        tool_calls_chunks[idx] = {
                            "id": "",
                            "name": "",
                            "arguments": []
                        }
                    tc_chunk = tool_calls_chunks[idx]
                    if tc.id:
                        tc_chunk["id"] = tc.id
                    if tc.function:
                        if tc.function.name:
                            tc_chunk["name"] = tc.function.name
                        if tc.function.arguments:
                            tc_chunk["arguments"].append(tc.function.arguments)

        # 4. 拼装最终结果
        reply_text = "".join(reply_text_parts)
        
        tool_calls_result = []
        for idx, tc_data in sorted(tool_calls_chunks.items()):
            args_str = "".join(tc_data["arguments"])
            args = {}
            if args_str:
                try:
                    args = json.loads(args_str)
                except Exception:
                    args = args_str
            tool_calls_result.append({
                "id": tc_data["id"] or f"call_{idx}",
                "name": tc_data["name"],
                "args": args
            })
                
        return reply_text, tool_calls_result

