import os
import sys
import time

# 确保脚本能正确找到根目录下的 backend 模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.engines import COMEngine
from backend.tools import ps_tools

def main():
    print("====== 开始测试 Phase 04 选区与蒙版功能 ======")
    
    # 1. 初始化引擎与上下文
    engine = COMEngine()
    ctx = engine.ctx
    print("引擎初始化成功。")
    
    # 2. 创建一个测试用的新文档
    print("\n-- 步骤 1: 创建测试文档 --")
    res = ps_tools.create_document(ctx, width=800, height=600, name="Selection Mask Test")
    print("Create Document:", res)
    
    # 在文档里建个新图层
    ps_tools.create_layer(ctx, name="Test Layer")
    
    # 3. 创建矩形选区
    print("\n-- 步骤 2: 基础选区 (创建矩形) --")
    res = ps_tools.basic_selection(ctx, action="rect", bounds=[100, 100, 400, 400])
    print("Basic Selection (rect):", res)
    time.sleep(1)
    
    # 4. 修改选区 (扩展)
    print("\n-- 步骤 3: 选区修改 (扩展) --")
    res = ps_tools.modify_selection(ctx, action="expand", value=20)
    print("Modify Selection (expand):", res)
    time.sleep(1)
    
    # 5. 保存通道
    print("\n-- 步骤 4: 通道控制 (存储选区) --")
    channel_name = "Test_Saved_Channel"
    res = ps_tools.channel_control(ctx, action="save_selection", channel_name=channel_name)
    print("Channel Control (save):", res)
    time.sleep(1)
    
    # 6. 取消选区
    print("\n-- 步骤 5: 基础选区 (取消选择) --")
    res = ps_tools.basic_selection(ctx, action="deselect")
    print("Basic Selection (deselect):", res)
    time.sleep(1)
    
    # 7. 重新载入选区
    print("\n-- 步骤 6: 通道控制 (载入选区) --")
    res = ps_tools.channel_control(ctx, action="load_selection", channel_name=channel_name)
    print("Channel Control (load):", res)
    time.sleep(1)
    
    # 8. 添加图层蒙版
    print("\n-- 步骤 7: 蒙版控制 (从选区创建蒙版) --")
    # 获取图层树，找到 "Test Layer" 的标识符
    tree_res = ps_tools.get_layer_tree(ctx)
    if tree_res["success"]:
        layers = tree_res.get("layers", [])
        layer_id = None
        for l in layers:
            if l["name"] == "Test Layer":
                layer_id = l["id"]
                break
                
        if layer_id:
            res = ps_tools.mask_control(ctx, layer_identify=layer_id, action="add")
            print("Mask Control (add):", res)
        else:
            print("未能找到图层进行蒙版测试")
    time.sleep(1)
    
    # 9. 测试 AI 智能选取 (注意：需要画面有主体，空图层会触发兜底报错，用以检验错误捕获是否生效)
    print("\n-- 步骤 8: AI 智能选取测试 --")
    print("（由于是空白图像，此操作通常会抛出异常，用以检验后端捕获是否生效并输出友好提示）")
    res = ps_tools.smart_selection(ctx, action="subject")
    print("Smart Selection (subject):", res)
    
    print("\n====== 测试完成 ======")

if __name__ == "__main__":
    main()
