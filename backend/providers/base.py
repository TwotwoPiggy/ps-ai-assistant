from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Callable, Awaitable

class BaseProvider(ABC):
    @abstractmethod
    async def chat(self, 
                  messages: List[Dict[str, Any]], 
                  tools: List[dict], 
                  system_prompt: str,
                  on_thinking_callback: Callable[[str], Awaitable[None]] = None) -> Tuple[str, List[dict]]:
        """发送对话请求并获取回复。
        
        Args:
            messages: 统一的 OpenAI 消息格式列表:
                      [{"role": "user"|"assistant"|"tool", "content": ...}]
            tools: 统一的 OpenAI 工具 Schema 列表
            system_prompt: 系统提示词
            on_thinking_callback: 可选。用于接收流式返回的思考词 (思维链 reasoning_content)
            
        Returns:
            Tuple[reply_text, tool_calls]
            - reply_text: AI 返回的文本，无文本时为 ""
            - tool_calls: 结构化的工具调用列表:
              [{"id": "...", "name": "...", "args": {...}}]
        """
        pass


    @property
    @abstractmethod
    def supports_vision(self) -> bool:
        """该模型/服务商是否支持视觉多模态 (处理图像数据)"""
        pass
