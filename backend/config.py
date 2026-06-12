import os
import json
from pathlib import Path

# Config file path
CONFIG_PATH = Path(__file__).parent / "store" / "ai_config.json"

DEFAULT_PROVIDERS = {
    "gemini": {
        "api_key": "",
        "base_url": "",
        "model": "gemini-2.5-flash"
    },
    "deepseek": {
        "api_key": "",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat"
    },
    "qwen": {
        "api_key": "",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus"
    },
    "mimo": {
        "api_key": "",
        "base_url": "",
        "model": "mimo-v1"
    },
    "custom": {
        "api_key": "",
        "base_url": "",
        "model": ""
    }
}

def get_ai_config() -> dict:
    # 优先从环境变量获取初始值
    providers_init = {}
    for p, default in DEFAULT_PROVIDERS.items():
        providers_init[p] = default.copy()

    # 映射环境变量
    env_keys = {
        "gemini": "GEMINI_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "qwen": "DASHSCOPE_API_KEY",
        "mimo": "MIMO_API_KEY"
    }
    for p, env_var in env_keys.items():
        val = os.environ.get(env_var, "")
        if val:
            providers_init[p]["api_key"] = val

    config = {
        "providers": providers_init,
        "current_provider": "gemini"
    }

    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                # 兼容旧版本格式 (如果直接有顶级字段)
                old_key = data.get("gemini_api_key")
                old_model = data.get("model")

                # 加载新结构数据
                if "providers" in data and isinstance(data["providers"], dict):
                    for p, val in data["providers"].items():
                        if p in config["providers"] and isinstance(val, dict):
                            config["providers"][p].update(val)
                elif old_key:
                    # 如果只有旧 key，将其合入 gemini
                    config["providers"]["gemini"]["api_key"] = old_key

                if "current_provider" in data:
                    config["current_provider"] = data["current_provider"]
                elif old_model:
                    # 如果只有旧 model 且是 gemini 系列，设置 current_provider
                    if old_model.startswith("gemini"):
                        config["current_provider"] = "gemini"
                        config["providers"]["gemini"]["model"] = old_model
        except Exception:
            pass

    # 注入顶级兼容字段以兼容旧的单 Gemini 适配器
    curr = config["current_provider"]
    config["gemini_api_key"] = config["providers"]["gemini"]["api_key"]
    config["model"] = config["providers"][curr]["model"]

    return config

def save_ai_config(api_key: str = None, model: str = None, current_provider: str = None, providers: dict = None):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    
    # 读出当前存储的数据
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass

    # 处理旧签名的调用形式: save_ai_config(api_key, model) 默认更新 gemini
    if current_provider is None and providers is None:
        if "providers" not in data:
            data["providers"] = {}
        if "gemini" not in data["providers"]:
            data["providers"]["gemini"] = {}
        if api_key is not None:
            data["providers"]["gemini"]["api_key"] = api_key
            data["gemini_api_key"] = api_key
        if model is not None:
            data["providers"]["gemini"]["model"] = model
            data["model"] = model
        data["current_provider"] = "gemini"
    else:
        # 新签名调用
        if current_provider is not None:
            data["current_provider"] = current_provider
        if providers is not None:
            if "providers" not in data:
                data["providers"] = {}
            for p, fields in providers.items():
                if p not in data["providers"]:
                    data["providers"][p] = {}
                data["providers"][p].update(fields)
            
            # 同时更新顶级兼容字段
            if "gemini" in providers and "api_key" in providers["gemini"]:
                data["gemini_api_key"] = providers["gemini"]["api_key"]
            curr = data.get("current_provider", "gemini")
            if curr in data["providers"] and "model" in data["providers"][curr]:
                data["model"] = data["providers"][curr]["model"]

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

