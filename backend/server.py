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


def reload_ai_agent(new_key: str, new_model: str) -> bool:
    """用新的 API Key 和模型初始化或重载 AI Agent"""
    global ai_agent, api_key
    if not new_key:
        ai_agent = None
        api_key = ""
        return False
    try:
        model = new_model or "gemini-2.5-flash"
        ai_agent = PhotoshopAgent(api_key=new_key, model=model)
        api_key = new_key
        save_ai_config(new_key, model)
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
async def connect(sid, environ):
    print(f"[PS-AI] 客户端已连接: {sid}")


@sio.event
async def disconnect(sid):
    print(f"[PS-AI] 客户端已断开: {sid}")


@sio.event
async def ai_chat(sid, payload={}):
    """处理前端发来的聊天消息"""
    global ai_agent

    # 懒初始化: 第一次收到 ai_chat 时尝试加载 API Key 并创建 Agent
    if not ai_agent:
        config = get_ai_config()
        key = config.get("gemini_api_key", "")
        model = config.get("model", "gemini-2.5-flash")
        if not key:
            await sio.emit('ai_chat_response', {
                "response": "请先在 AI 配置面板中设置您的 Gemini API Key 以启用 AI 聊天操作功能。"
            }, to=sid)
            return
        else:
            reload_ai_agent(key, model)
            if not ai_agent:
                await sio.emit('ai_chat_response', {
                    "response": "AI Agent 初始化失败，请检查您的 API Key 是否正确。"
                }, to=sid)
                return

    message = payload.get("message", "")
    if not message:
        return

    async def status_callback(status, msg):
        await sio.emit('ai_chat_status', {
            "status": status,
            "message": msg
        }, to=sid)

    try:
        response = await ai_agent.handle_message(sid, message, status_callback)
        await sio.emit('ai_chat_response', {
            "response": response
        }, to=sid)
    except Exception as e:
        await sio.emit('ai_chat_response', {
            "response": f"执行出错: {str(e)}"
        }, to=sid)
        await status_callback("done", f"执行出错: {str(e)}")


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
        new_key = payload.get("gemini_api_key", "").strip()
        new_model = payload.get("model", "gemini-2.5-flash").strip()
        # If new_key is empty or dummy placeholder, try to keep the existing one if it's available
        if not new_key and api_key:
            new_key = api_key
        success = reload_ai_agent(new_key, new_model)
        return {"success": success, "has_key": bool(api_key), "model": new_model}
    else:
        # GET: 返回当前配置状态
        config = get_ai_config()
        current_key = api_key or config.get("gemini_api_key", "")
        current_model = config.get("model", "gemini-2.5-flash")
        return {"has_key": bool(current_key), "gemini_api_key": current_key, "model": current_model}


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
