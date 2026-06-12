import os
import json
from pathlib import Path

# Config file path
CONFIG_PATH = Path(__file__).parent / "store" / "ai_config.json"

def get_ai_config() -> dict:
    config = {
        "gemini_api_key": os.environ.get("GEMINI_API_KEY", ""),
        "model": "gemini-2.5-flash" # default
    }
    
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("gemini_api_key"):
                    config["gemini_api_key"] = data.get("gemini_api_key")
                if data.get("model"):
                    config["model"] = data.get("model")
        except Exception:
            pass
            
    return config

def save_ai_config(api_key: str, model: str):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass
            
    if api_key is not None:
        data["gemini_api_key"] = api_key
    if model is not None:
        data["model"] = model
        
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
