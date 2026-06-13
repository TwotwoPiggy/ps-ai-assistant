import asyncio
from backend.agent import PhotoshopAgent
from backend.engines import COMEngine

async def test_fallback():
    agent = PhotoshopAgent()
    
    # 1. 模拟没有 UXP 连接的情况下，Web Chat 请求路由
    engine_fallback = agent._get_engine(sid="session_web", client_type="web", sio=None, uxp_sid=None)
    assert isinstance(engine_fallback, COMEngine), "在没有 UXP 客户端在线时，Web Chat 应自动路由到 COMEngine"
    print("[Test Fallback] [OK] 成功验证 Web 客户端单独请求时，路由退回到 COMEngine")
    
    # 2. 模拟 UXP 连接在线时，Web Chat 请求路由
    engine_uxp = agent._get_engine(sid="session_web", client_type="web", sio=None, uxp_sid="session_uxp")
    from backend.engines import UXPEngine
    assert isinstance(engine_uxp, UXPEngine), "在有 UXP 客户端在线时，Web Chat 应优先路由到 UXPEngine"
    print("[Test Fallback] [OK] 成功验证 UXP 客户端在线时，Web Chat 请求路由到 UXPEngine")

if __name__ == "__main__":
    asyncio.run(test_fallback())
