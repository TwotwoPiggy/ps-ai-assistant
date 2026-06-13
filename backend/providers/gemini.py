import json
import base64
import asyncio
from typing import List, Dict, Any, Tuple, Callable, Awaitable
from google import genai
from google.genai import types

from .base import BaseProvider
from backend.tools.registry import registry


class GeminiProvider(BaseProvider):
    def __init__(self, api_key: str, model: str = 'gemini-2.5-flash'):
        self.api_key = api_key
        self.model = model
        self.client = genai.Client(api_key=api_key)

    @property
    def supports_vision(self) -> bool:
        return True

    def _convert_messages(self, messages: List[Dict[str, Any]]) -> List[types.Content]:
        """将统一的 OpenAI 格式消息转换为 Gemini SDK 接受的 Content 列表"""
        gemini_contents = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            tool_calls = msg.get("tool_calls")
            
            parts = []
            
            # 1. 转换模型产生的 function_calls
            if tool_calls:
                for tc in tool_calls:
                    # 转换成 Gemini 的 FunctionCall
                    fc = types.FunctionCall(
                        name=tc.get("name"),
                        args=tc.get("args") or {},
                        id=tc.get("id")
                    )
                    part_kwargs = {"function_call": fc}
                    if "thought_signature" in tc and tc.get("thought_signature"):
                        part_kwargs["thought_signature"] = tc.get("thought_signature")
                    parts.append(types.Part(**part_kwargs))
            
            # 2. 处理 content
            if content:
                if isinstance(content, list):
                    # OpenAI 的多模态 List[dict] 格式
                    for part in content:
                        part_type = part.get("type")
                        if part_type == "text":
                            parts.append(types.Part.from_text(text=part.get("text", "")))
                        elif part_type == "image_url":
                            url = part.get("image_url", {}).get("url") or part.get("url", "")
                            if "base64," in url:
                                try:
                                    header, base64_data = url.split("base64,", 1)
                                    mime_type = header.split(";")[0].split(":")[1]
                                    img_bytes = base64.b64decode(base64_data)
                                    parts.append(types.Part.from_bytes(data=img_bytes, mime_type=mime_type))
                                except Exception as e:
                                    print(f"[GeminiProvider] 转换 base64 图像失败: {e}")
                else:
                    parts.append(types.Part.from_text(text=content))
                    
            # 3. 处理 tool 角色返回的 function_response
            if role == "tool":
                name = msg.get("name")
                resp_val = content
                if isinstance(content, str):
                    try:
                        resp_val = json.loads(content)
                    except Exception:
                        pass
                
                # 特殊处理：剥离大图的 base64 字符串
                if isinstance(resp_val, dict) and "imageBase64" in resp_val:
                    img_b64 = resp_val["imageBase64"]
                    resp_val = resp_val.copy()
                    del resp_val["imageBase64"]
                    resp_val["message"] = "画布截图已作为独立的图像实体(Part)附在当前消息中提供给您进行视觉分析。"
                    try:
                        img_bytes = base64.b64decode(img_b64)
                        parts.append(types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"))
                    except Exception as e:
                        print(f"[GeminiProvider] 解码截图 base64 失败: {e}")
                        
                # 获取原始 tool_call_id
                tool_call_id = msg.get("tool_call_id")
                
                fr = types.FunctionResponse(
                    name=name,
                    response=resp_val,
                    id=tool_call_id
                )
                parts.append(types.Part(function_response=fr))
                
            # 映射角色类型
            # Gemini 中工具回复也是作为 role="user" 发送
            gemini_role = "user"
            if role == "assistant":
                gemini_role = "model"
            elif role == "system":
                # system_prompt 走 Config.system_instruction，在这里跳过
                continue
                
            gemini_contents.append(types.Content(
                role=gemini_role,
                parts=parts
            ))
            
        return gemini_contents

    async def chat(self, 
                  messages: List[Dict[str, Any]], 
                  tools: List[dict], 
                  system_prompt: str,
                  on_thinking_callback: Callable[[str], Awaitable[None]] = None) -> Tuple[str, List[dict]]:
        # 1. 转换历史消息为 Gemini 格式

        contents = self._convert_messages(messages)
        
        # 2. 转换工具为 Gemini 支持的 Tool 声明
        gemini_tools = []
        if tools:
            func_decls = []
            for tool in tools:
                func_data = tool.get("function", {})
                
                func_decls.append(types.FunctionDeclaration(
                    name=func_data.get("name"),
                    description=func_data.get("description", ""),
                    parameters=func_data.get("parameters")
                ))
            if func_decls:
                gemini_tools = [types.Tool(function_declarations=func_decls)]

        # 3. 构造 Config
        config = types.GenerateContentConfig()
        if system_prompt:
            config.system_instruction = system_prompt
        if gemini_tools:
            config.tools = gemini_tools

        # 4. 在单独线程中运行同步的 SDK 调用以防阻塞事件循环
        def run_call():
            return self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=config
            )
            
        response = await asyncio.to_thread(run_call)
        
        # 5. 解析返回
        reply_text = response.text or ""
        tool_calls_result = []
        
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.function_call:
                    fc = part.function_call
                    args = {}
                    if fc.args:
                        if hasattr(fc.args, "items"):
                            args = {k: v for k, v in fc.args.items()}
                        else:
                            args = dict(fc.args)
                    tool_calls_result.append({
                        "id": getattr(fc, "id", None) or f"call_{fc.name}",
                        "name": fc.name,
                        "args": args,
                        "thought_signature": getattr(part, "thought_signature", None)
                    })
                
        return reply_text, tool_calls_result
