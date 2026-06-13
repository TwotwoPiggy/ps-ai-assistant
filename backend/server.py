"""
Photoshop AI Assistant — 独立后端服务器
使用 FastAPI + python-socketio 提供 WebSocket 通信
默认端口: 18919
"""
import os
import uvicorn
import socketio
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import get_ai_config, save_ai_config
from .agent import PhotoshopAgent

# ==========================================
# 全局状态
# ==========================================
ai_agent: PhotoshopAgent | None = None
api_key: str = ""
client_types: dict[str, str] = {}

def mask_api_key(key: str) -> str:
    """对 API Key 进行脱敏，保留前4位和后4位"""
    if not key:
        return ""
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}****{key[-4:]}"

def reload_ai_agent() -> bool:
    """根据最新的系统配置初始化或重载 AI Agent"""
    global ai_agent, api_key
    try:
        config = get_ai_config()
        curr_p = config.get("current_provider", "gemini")
        curr_config = config.get("providers", {}).get(curr_p, {})
        curr_key = curr_config.get("api_key", "").strip()
        
        if not curr_key:
            ai_agent = None
            api_key = ""
            return False
            
        ai_agent = PhotoshopAgent()
        api_key = curr_key
        return True
    except Exception as e:
        print(f"[PS-AI] Agent 初始化失败: {e}")
        ai_agent = None
        api_key = ""
        return False

# ==========================================
# Socket.IO 服务器
# ==========================================
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
)


@sio.event
async def connect(sid, environ, auth=None):
    client_type = "web"
    if auth and isinstance(auth, dict):
        client_type = auth.get("client_type", "web")
    elif environ:
        import urllib.parse
        query_string = environ.get('QUERY_STRING', '')
        params = urllib.parse.parse_qs(query_string)
        if 'client_type' in params:
            client_type = params['client_type'][0]
            
    client_types[sid] = client_type
    print(f"[PS-AI] 客户端已连接: {sid}, 类型: {client_type}")


@sio.event
async def disconnect(sid):
    client_type = client_types.pop(sid, "web")
    print(f"[PS-AI] 客户端已断开: {sid}, 类型: {client_type}")


@sio.event
async def ai_chat(sid, payload={}):
    """处理前端发来的聊天消息"""
    global ai_agent

    # 懒初始化: 第一次收到 ai_chat 时尝试加载配置并创建 Agent
    if not ai_agent:
        reload_ai_agent()
        if not ai_agent:
            await sio.emit('ai_chat_response', {
                "response": "请先在 AI 配置面板中设置您的 API Key 以启用智能助手服务。"
            }, to=sid)
            return

    message = payload.get("message", "")
    if not message:
        return

    async def status_callback(status, msg):
        if status == "thinking_word":
            await sio.emit('ai_chat_thinking', {
                "word": msg
            }, to=sid)
        else:
            await sio.emit('ai_chat_status', {
                "status": status,
                "message": msg
            }, to=sid)


    try:
        client_type = client_types.get(sid, "web")
        # 寻找是否有已连接的 UXP 客户端
        uxp_sid = None
        for s, t in client_types.items():
            if t == "uxp":
                uxp_sid = s
                break
        response = await ai_agent.handle_message(
            sid, message, status_callback, 
            client_type=client_type, sio=sio, uxp_sid=uxp_sid
        )
        await sio.emit('ai_chat_response', {
            "response": response
        }, to=sid)
    except Exception as e:
        await sio.emit('ai_chat_response', {
            "response": f"执行出错: {str(e)}"
        }, to=sid)
        await status_callback("done", f"执行出错: {str(e)}")


@sio.event
async def ps_event(sid, payload={}):
    """处理前端 UXP 发来的 Photoshop 事件推送"""
    event_name = payload.get("event")
    data = payload.get("descriptor", {})
    print(f"\n[PS-AI] 收到 UXP 事件: {event_name}")
    print(f"[PS-AI] 事件详情: {data}\n")
    return {"success": True}


@sio.event
async def ai_clear_history(sid, payload={}):
    """清空用户的历史对话记录"""
    global ai_agent
    if ai_agent:
        ai_agent.clear_conversations(sid)
        print(f"[PS-AI] 已清空客户端历史记录: {sid}")
    return {"success": True}


@sio.event
async def ai_config(sid, payload={}):
    """处理 AI 配置的读取和保存"""
    global ai_agent, api_key

    action = payload.get("action", "get")
    if action == "save":
        # 获取现有的配置
        config = get_ai_config()
        
        current_provider = payload.get("current_provider")
        providers_payload = payload.get("providers")
        
        if current_provider is not None:
            config["current_provider"] = current_provider
            
        if providers_payload and isinstance(providers_payload, dict):
            # 新的多 Provider 格式保存
            for p, fields in providers_payload.items():
                if p not in config["providers"]:
                    config["providers"][p] = {}
                    
                raw_key = fields.get("api_key", "").strip()
                if raw_key:
                    # 如果收到包含掩码的 key，忽略它，不覆写原已保存的 Key
                    if "****" in raw_key:
                        pass
                    else:
                        config["providers"][p]["api_key"] = raw_key
                        
                if "base_url" in fields:
                    config["providers"][p]["base_url"] = fields["base_url"].strip()
                if "model" in fields:
                    config["providers"][p]["model"] = fields["model"].strip()
        else:
            # 兼容旧版本保存: payload.get("gemini_api_key"), payload.get("model")
            new_gemini_key = payload.get("gemini_api_key", "").strip()
            new_model = payload.get("model", "").strip()
            
            if new_gemini_key:
                if "****" not in new_gemini_key:
                    config["providers"]["gemini"]["api_key"] = new_gemini_key
            if new_model:
                config["providers"]["gemini"]["model"] = new_model
                
        # 写入物理配置文件
        save_ai_config(
            current_provider=config["current_provider"],
            providers=config["providers"]
        )
        
        # 重载 Agent
        success = reload_ai_agent()
        
        # 返回新状态
        curr_p = config["current_provider"]
        curr_model = config["providers"][curr_p]["model"]
        return {"success": success, "has_key": bool(api_key), "model": curr_model}
    else:
        # GET: 返回包含脱敏数据的新老配置信息
        config = get_ai_config()
        
        masked_providers = {}
        for p, fields in config.get("providers", {}).items():
            masked_providers[p] = fields.copy()
            masked_providers[p]["api_key"] = mask_api_key(fields.get("api_key", ""))
            
        curr_p = config.get("current_provider", "gemini")
        curr_key = config["providers"][curr_p]["api_key"]
        curr_model = config["providers"][curr_p]["model"]
        
        return {
            "success": True,
            "current_provider": curr_p,
            "providers": masked_providers,
            # 旧版兼容字段
            "has_key": bool(curr_key),
            "gemini_api_key": mask_api_key(config["providers"]["gemini"]["api_key"]),
            "model": curr_model
        }


# ==========================================
# FastAPI 应用
# ==========================================
app = FastAPI(title="Photoshop AI Assistant")

# 挂载 Socket.IO 到 FastAPI
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

# 如果前端已构建 (frontend/dist 目录存在)，提供静态文件服务
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"
if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")


# ==========================================
# 入口
# ==========================================
DEFAULT_PORT = 18919

if __name__ == "__main__":
    port = int(os.environ.get("PORT", DEFAULT_PORT))
    print(f"[PS-AI] 服务器启动中，端口: {port}")
    print(f"[PS-AI] 前端静态文件: {'已挂载 (' + str(FRONTEND_DIST) + ')' if FRONTEND_DIST.is_dir() else '未找到'}")
    uvicorn.run(
        socket_app,
        host="0.0.0.0",
        port=port,
        log_level="info",
    )
