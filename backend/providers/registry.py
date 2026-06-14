from .openai_compat import OpenAICompatProvider
from .gemini import GeminiProvider
from .base import BaseProvider

def get_provider(provider_name: str, config: dict) -> BaseProvider:
    """根据 Provider 名称和全局配置字典，实例化对应的 Provider 适配器。
    
    Args:
        provider_name: 'gemini', 'deepseek', 'qwen', 'mimo', 'custom'
        config: 全局配置字典，格式符合 config.py 中的 get_ai_config() 返回值
    """
    providers_config = config.get("providers", {})
    prov_config = providers_config.get(provider_name, {})
    
    api_key = prov_config.get("api_key", "").strip()
    base_url = prov_config.get("base_url", "").strip()
    model = prov_config.get("model", "").strip()
    
    if provider_name == "gemini":
        # 如果 model 为空，提供默认值
        model = model or "gemini-2.5-flash"
        return GeminiProvider(api_key=api_key, model=model)
    else:
        # deepseek, qwen, mimo, custom 均统一通过 OpenAICompatProvider 接入
        # 提供各通道对应的默认模型和 base_url (防止配置里为空)
        if provider_name == "deepseek":
            base_url = base_url or "https://api.deepseek.com/v1"
            model = model or "deepseek-chat"
        elif provider_name == "qwen":
            base_url = base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"
            model = model or "qwen-plus"
        elif provider_name == "mimo":
            base_url = base_url or ""
            model = model or "mimo-v1"
            
        return OpenAICompatProvider(
            api_key=api_key,
            base_url=base_url,
            model=model
        )
