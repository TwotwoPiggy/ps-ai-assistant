import asyncio
import socketio
import json
import os
import time

sio = socketio.AsyncClient()
RESULTS_FILE = os.path.join(os.path.dirname(__file__), "capability_results.json")

tools_to_test = [
    ("get_layer_tree", {}),
    ("get_canvas_snapshot", {}),
    ("create_layer", {"name": "TestLayer", "opacity": 50}),
    # For rename_layer, we need an ID. Since we just created a layer, it's the active layer, but we don't know its ID.
    # To keep the test simple, we assume ID "1" might fail or pass, which is fine to test error handling too.
    # We will pass dummy IDs just to see if the invocation reaches the correct handler.
    ("rename_layer", {"layer_identify": "1", "new_name": "RenamedLayer"}),
    ("set_layer_visibility", {"layer_identify": "1", "visible": False}),
    ("reorder_layer", {"layer_identify": "1", "target_identify": "2", "placement": "placeAfter"}),
    ("adjust_brightness_contrast", {"brightness": 10, "contrast": 10}),
    ("crop_canvas", {"top": 10, "left": 10, "bottom": 100, "right": 100}),
    ("resize_canvas", {"width": 800, "height": 600}),
    ("flip_image", {"direction": "horizontal"}),
    ("delete_layer", {"layer_identify": "1"}),
]

results = []

@sio.event
async def connect():
    print("[Test] 已连接到后端服务器。")
    await run_tests()

async def run_tests():
    print("[Test] 准备在 2 秒后开始测试（请确保 PS 已打开并连接插件）...")
    await asyncio.sleep(2)

    for tool_name, args in tools_to_test:
        for use_batchplay in [False, True]:
            test_args = args.copy()
            test_args["_use_batchplay"] = use_batchplay
            mode = "batchPlay" if use_batchplay else "DOM API"
            
            print(f"\n======================================")
            print(f"正在测试: {tool_name} (模式: {mode})")
            print(f"参数: {test_args}")
            
            try:
                # call with a timeout of 10s
                result = await sio.call(
                    "debug_execute_tool",
                    {"name": tool_name, "args": test_args},
                    timeout=10
                )
                print(f"结果: {result}")
                results.append({
                    "tool": tool_name,
                    "mode": mode,
                    "success": result.get("success", False),
                    "result": result
                })
            except Exception as e:
                print(f"调用发生异常: {e}")
                results.append({
                    "tool": tool_name,
                    "mode": mode,
                    "success": False,
                    "result": {"error": str(e)}
                })
                
    # Save to JSON
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    print(f"\n[Test] 测试完成。结果已保存至 {RESULTS_FILE}")
    await sio.disconnect()

@sio.event
async def disconnect():
    print("[Test] 已断开连接。")

async def main():
    try:
        await sio.connect("http://127.0.0.1:18919", auth={"client_type": "test_script"})
        await sio.wait()
    except Exception as e:
        print(f"连接失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())
