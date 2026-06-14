import asyncio
import socketio
import sys

async def run_test():
    # 1. 实例化 Mock UXP 客户端
    uxp_sio = socketio.AsyncClient()
    
    # 2. 实例化 Mock Web Chat 客户端
    web_sio = socketio.AsyncClient()
    
    uxp_connected = asyncio.Event()
    web_connected = asyncio.Event()
    test_finished = asyncio.Event()

    @uxp_sio.event
    async def connect():
        print("[UXP Client] 已连接到服务器")
        uxp_connected.set()

    @uxp_sio.event
    async def disconnect():
        print("[UXP Client] 已从服务器断开")

    @uxp_sio.on("execute_tool")
    async def on_execute_tool(data):
        name = data.get("name")
        args = data.get("args")
        print(f"[UXP Client] 接收到工具执行请求: {name}, 参数: {args}")
        
        # 针对 get_layer_tree 模拟返回图层树，否则大模型会卡在不知道图层ID
        if name == "get_layer_tree":
            mock_result = {
                "success": True,
                "layers": [
                    {"id": "layer_1", "name": "背景", "type": "ArtLayer", "visible": True},
                    {"id": "layer_2", "name": "文本图层", "type": "ArtLayer", "visible": True}
                ]
            }
        else:
            mock_result = {
                "success": True,
                "message": f"UXP 模拟成功执行了 {name}"
            }
        print(f"[UXP Client] 返回 Ack 响应: {mock_result}")
        return mock_result

    @web_sio.event
    async def connect():
        print("[Web Client] 已连接到服务器")
        web_connected.set()

    @web_sio.event
    async def disconnect():
        print("[Web Client] 已从服务器断开")

    @web_sio.on("ai_chat_response")
    async def on_ai_chat_response(data):
        print(f"[Web Client] 收到 AI 最终聊天回复:\n{data.get('response')}")
        test_finished.set()

    @web_sio.on("ai_chat_status")
    async def on_ai_chat_status(data):
        print(f"[Web Client] 收到执行状态更新: {data.get('status')} - {data.get('message')}")

    @web_sio.on("ai_chat_thinking")
    async def on_ai_chat_thinking(data):
        # 过滤思维链输出，防止日志过多
        pass

    # 开始连接
    print("\n--- 开始端到端集成集成测试 ---")
    try:
        print("[Test] 正在连接 UXP 客户端...")
        await uxp_sio.connect("http://127.0.0.1:18919", auth={"client_type": "uxp"}, transports=["websocket"])
        
        print("[Test] 正在连接 Web Chat 客户端...")
        await web_sio.connect("http://127.0.0.1:18919", auth={"client_type": "web"}, transports=["websocket"])

        # 等待双端连接就绪
        await asyncio.wait_for(asyncio.gather(uxp_connected.wait(), web_connected.wait()), timeout=5.0)
        print("[Test] 双端连接就绪，开始发送测试聊天请求...")

        # 模拟发送聊天，触发工具调用。
        # 我们使用 "把那个叫文本图层的图层隐藏掉" 这个消息，它只需要执行 get_layer_tree 和 set_layer_visibility。
        # 不需要使用多模态截图。
        test_message = "把那个叫文本图层的图层隐藏掉"
        print(f"[Web Client] 发送消息: '{test_message}'")
        await web_sio.emit("ai_chat", {"message": test_message})

        # 等待测试流程跑完（AI 最终回复了 web 客户端）
        # 超时时间设为 45 秒，因为大模型需要几轮调用
        await asyncio.wait_for(test_finished.wait(), timeout=45.0)
        print("[Test] 测试流程成功跑通！")
        
    except asyncio.TimeoutError:
        print("[Test] 错误：测试执行超时！请确认 API Key 是否已配置，或者网络连接是否正常。")
        import os
        os._exit(1)
    except Exception as e:
        print(f"[Test] 发生异常: {e}")
        import os
        os._exit(1)
    finally:
        # 断开连接
        print("[Test] 正在清理连接...")
        if uxp_sio.connected:
            await uxp_sio.disconnect()
        if web_sio.connected:
            await web_sio.disconnect()
        print("--- 集成测试结束 ---\n")
        import os
        os._exit(0)

if __name__ == "__main__":
    asyncio.run(run_test())
