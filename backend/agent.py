import os
import sys
import time
import base64
import json
import asyncio
from typing import List, Dict, Any, Tuple

from backend.tools import PhotoshopContext, registry
from backend.providers import get_provider
from backend.config import get_ai_config

class PhotoshopAgent:
    def __init__(self, api_key: str = None, model: str = None):
        """初始化 Photoshop AI 协调代理。
        
        Args:
            api_key: 可选。用于向后兼容单 Gemini API Key。
            model: 可选。用于向后兼容单 Gemini 模型。
        """
        self.api_key = api_key
        self.model = model
        # 统一存储 OpenAI 格式的历史会话: sid -> list[dict]
        self.conversations: dict[str, list[dict]] = {}
        # 为每个会话维护独立的 Photoshop 运行上下文
        self.contexts: dict[str, PhotoshopContext] = {}

    def clear_conversations(self, sid: str):
        """清空当前会话的历史聊天记录"""
        if sid in self.conversations:
            self.conversations[sid] = []
        if sid in self.contexts:
            # 清空图层映射关系，确保图层树是全新的
            self.contexts[sid] = PhotoshopContext()

    def _get_context(self, sid: str) -> PhotoshopContext:
        if sid not in self.contexts:
            self.contexts[sid] = PhotoshopContext()
        return self.contexts[sid]

    async def handle_message(self, sid: str, message: str, status_callback=None) -> str:
        """处理来自前端 Chat UI 的用户自然语言消息，返回 AI 回复"""
        
        # 1. 确保会话存在并清理历史超大 base64 图像
        if sid not in self.conversations:
            self.conversations[sid] = []
            
        cleaned_history = []
        for msg in self.conversations[sid]:
            content = msg.get("content")
            if isinstance(content, list):
                # 清理多模态消息中的超大 Base64 数据以防 Token 溢出
                new_content = []
                for part in content:
                    if part.get("type") == "image_url":
                        img_url_data = part.get("image_url", {})
                        url = img_url_data.get("url", "") if isinstance(img_url_data, dict) else part.get("url", "")
                        if len(url) > 1000:
                            # 替换为纯文本占位符，防止触发 API base64 格式校验错误
                            cleaned_part = {
                                "type": "text",
                                "text": "[系统提示：之前的画布快照截图已被清除以释放上下文 Token]"
                            }
                            new_content.append(cleaned_part)
                        else:
                            new_content.append(part)
                    else:
                        new_content.append(part)
                msg["content"] = new_content
            cleaned_history.append(msg)
        self.conversations[sid] = cleaned_history

        # 2. 载入最新配置并实例化 Provider
        config = get_ai_config()
        current_provider_name = config.get("current_provider", "gemini")
        
        # 兼容旧版本 reload_ai_agent 行为：
        # 如果初始化时传入了 api_key (且当前选定的是 gemini 且配置里的 key 未更新)，则优先使用传入的
        if self.api_key and current_provider_name == "gemini":
            prov_conf = config.get("providers", {}).get("gemini", {})
            if not prov_conf.get("api_key"):
                prov_conf["api_key"] = self.api_key
            if self.model and not prov_conf.get("model"):
                prov_conf["model"] = self.model
                
        provider = get_provider(current_provider_name, config)
        ctx = self._get_context(sid)

        # 3. 追加当前用户的新消息
        self.conversations[sid].append({
            "role": "user",
            "content": message
        })

        # 4. 获取统一的 OpenAI tools 描述
        tools_schema = registry.get_openai_schemas()

        system_instruction = (
            "你是一个功能强大的 Photoshop AI 助手，能够直接通过执行 Python COM 操作来修改当前的 Photoshop 文档。\n"
            "你可以使用一系列定义好的工具（Tools）来完成用户的指令，包含图层基础操作和画布基本编辑。\n"
            "【操作准则】:\n"
            "1. 务必始终使用【简体中文】与用户进行回复和交流。\n"
            "2. 当用户请求任何与图层相关的操作时，你没有默认图层的标识符。你【必须】首先调用 `get_layer_tree` 获取当前图层树以取得目标的 `layer_identify` (如 layer_1)，之后再利用它进行具体操作。不要猜测或使用用户提到的名字作为 ID 传入其他操作参数中。\n"
            "3. 如果用户发出的指令非常依赖视觉理解（如'把画面变亮点'、'裁剪掉左上角'等），你应该优先调用 `get_canvas_snapshot` 获取当前画面，结合视觉特征后再做出调用工具或回复的判断。\n"
            "4. 一次回复里，你可以决定调用一个或多个工具。多步操作应当按照合理顺序连贯调用，直到完成指令。\n"
            "5. 当所有的工具调用执行完毕并得到结果后，你应该将执行情况及最终画布状态汇总成简明且易读的简体中文回复告诉用户。\n"
            "6. 如果某个操作返回了错误（例如无法调整空白图层的亮度），请在最终回复中诚实告知用户，并提供指导或建议。"
        )

        max_turns = 10
        turn = 0
        
        while turn < max_turns:
            turn += 1
            if status_callback:
                await status_callback("thinking", f"AI 正在思考中... (第 {turn} 轮)")
                
            # 引入 RateLimit/Unavailable 重试处理
            import openai
            from google.genai import errors as gemini_errors
            
            max_retries = 3
            reply_text = ""
            tool_calls = []
            primary_error = None
            
            for attempt in range(max_retries):
                try:
                    # 定义 R1 推理思维链流式实时回调
                    async def on_thinking(chunk: str):
                        if status_callback:
                            await status_callback("thinking_word", chunk)

                    reply_text, tool_calls = await provider.chat(
                        messages=self.conversations[sid],
                        tools=tools_schema,
                        system_prompt=system_instruction,
                        on_thinking_callback=on_thinking
                    )
                    primary_error = None
                    break
                except Exception as e:
                    primary_error = e
                    is_rate_limit = False
                    err_msg = str(e)
                    
                    if isinstance(e, openai.RateLimitError):
                        is_rate_limit = True
                    elif isinstance(e, gemini_errors.APIError) and getattr(e, "code", None) in (429, 503):
                        is_rate_limit = True
                    elif "429" in err_msg or "rate limit" in err_msg.lower():
                        is_rate_limit = True
                        
                    if is_rate_limit and attempt < max_retries - 1:
                        sleep_time = (attempt * 15) + 20
                        if status_callback:
                            await status_callback("thinking", f"接口繁忙或受限，将在 {sleep_time} 秒后重试...")
                        await asyncio.sleep(sleep_time)
                    else:
                        break
            
            if primary_error:
                # 触发自动降级回退至 Gemini 逻辑
                auto_fallback = config.get("auto_fallback_to_gemini", True)
                gemini_key = config.get("providers", {}).get("gemini", {}).get("api_key", "").strip()
                
                if auto_fallback and current_provider_name != "gemini" and gemini_key:
                    if status_callback:
                        await status_callback("thinking", f"主提供商 ({current_provider_name}) 连接超时或发生异常，正在自动降级回退至 Gemini 运行...")
                    try:
                        fallback_provider = get_provider("gemini", config)

                        
                        reply_text, tool_calls = await fallback_provider.chat(
                            messages=self.conversations[sid],
                            tools=tools_schema,
                            system_prompt=system_instruction
                        )
                        reply_text = f"【系统提示：由于主模型 {current_provider_name} 连接失败，本轮对话已自动降级由 Gemini 接管处理。】\n\n{reply_text}"
                        primary_error = None
                    except Exception as fallback_error:

                        print(f"[PS-AI] 降级回退至 Gemini 失败: {fallback_error}")
                        raise primary_error
                else:
                    raise primary_error

            # 追加 Assistant 消息到历史记录
            assistant_msg = {
                "role": "assistant",
                "content": reply_text
            }
            if tool_calls:
                assistant_msg["tool_calls"] = tool_calls
            self.conversations[sid].append(assistant_msg)

            # 如果没有工具调用，说明对话已经收敛，返回最终回复
            if not tool_calls:
                if status_callback:
                    await status_callback("done", "完成回复")
                return reply_text

            # 准备存放此轮工具调用结果的列表，保证多个并行 tool 消息连续追加
            tool_responses = []
            img_b64_list = []

            # 依次执行工具调用并收集结果
            for tool_call in tool_calls:
                tc_id = tool_call.get("id")
                name = tool_call.get("name")
                args = tool_call.get("args")

                if status_callback:
                    await status_callback("executing", f"正在执行 PS 操作: {name}...")

                # 执行工具 (通过注册中心，并传入当前会话的 ctx)
                result = registry.execute_tool(name, args, ctx)

                # 处理图片数据，剥离超大 base64 字符串以防止污染 tool content
                tool_content = result.copy() if isinstance(result, dict) else result
                img_b64 = None
                if isinstance(tool_content, dict) and "imageBase64" in tool_content:
                    img_b64 = tool_content["imageBase64"]
                    del tool_content["imageBase64"]
                    tool_content["message"] = "截图已成功生成，数据已作为随后的图像消息附带发送给您。"

                # 收集 Tool 回复
                tool_responses.append({
                    "role": "tool",
                    "tool_call_id": tc_id,
                    "name": name,
                    "content": json.dumps(tool_content, ensure_ascii=False)
                })

                if img_b64:
                    img_b64_list.append(img_b64)

            # 严格对齐 OpenAI 规范：一次性连续追加所有并行的 tool 消息，中途不能穿插 user 或其他消息
            self.conversations[sid].extend(tool_responses)

            # 所有工具执行结果追加完毕后，若有产生的截图，整体追加在工具响应之后
            for img_b64 in img_b64_list:
                self.conversations[sid].append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "（上一步 get_canvas_snapshot 获取的画布最新快照截图）"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                    ]
                })

        if status_callback:
            await status_callback("done", "AI 回复超时")
        return "抱歉，由于操作步骤过多，AI 回复已超时。"

