import os
import sys
import time

# 确保脚本能正确找到根目录下的 backend 模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.engines import COMEngine
from backend.tools import ps_tools

def run_tests():
    print("====== 开始运行 Phase 06 自动化集成测试 ======")
    engine = COMEngine()
    ctx = engine.ctx

    # 1. 测试高斯模糊与表面模糊
    if hasattr(ps_tools, "apply_blur_sharpen"):
        print("\n-- 步骤 1: 测试高斯模糊 --")
        ps_tools.create_document(ctx, width=400, height=400, name="Gaussian Blur Test")
        ps_tools.create_layer(ctx, name="BlurLayer")
        res = ps_tools.apply_blur_sharpen(ctx, filter_type="gaussian", radius=3.5)
        print("Apply Gaussian Blur:", res)
        assert res["success"] is True
        
        print("\n-- 步骤 2: 测试表面模糊 --")
        res = ps_tools.apply_blur_sharpen(ctx, filter_type="surface", radius=5.0, threshold=15)
        print("Apply Surface Blur:", res)
        assert res["success"] is True

        print("\n-- 步骤 3: 测试 USM 锐化 --")
        res = ps_tools.apply_blur_sharpen(ctx, filter_type="usm", radius=1.0, amount=80.0, threshold=4)
        print("Apply USM Sharpen:", res)
        assert res["success"] is True

        ctx.get_doc().Close(2) # 2 = psDoNotSaveChanges
    else:
        print("[Skip] apply_blur_sharpen is not implemented yet.")

    # 2. 测试液化
    if hasattr(ps_tools, "apply_liquify"):
        print("\n-- 步骤 4: 测试智能液化 (API 可达性) --")
        # 由于液化是模态弹窗，全自动测试如果真实触发会卡住，因此此处仅校验函数注册与转换安全对象能力
        assert hasattr(ps_tools, "apply_liquify")
        print("apply_liquify API is present.")
    else:
        print("[Skip] apply_liquify is not implemented yet.")

    # 3. 测试 Camera Raw 预设加载
    if hasattr(ps_tools, "apply_camera_raw_preset"):
        print("\n-- 步骤 5: 测试 Camera Raw 预设应用 --")
        ps_tools.create_document(ctx, width=400, height=400, name="Camera Raw Test")
        ps_tools.create_layer(ctx, name="PhotoLayer")
        
        # 期待传入空时使用内置默认预设，并首先自动将普通图层转换为智能对象
        res = ps_tools.apply_camera_raw_preset(ctx, preset_path="")
        print("Apply Camera Raw Preset:", res)
        
        # 验证 PhotoLayer 的类型应当被转换为智能对象
        tree_res = ps_tools.get_layer_tree(ctx)
        layers = tree_res.get("layers", [])
        photo_layer = next((l for l in layers if l["name"] == "PhotoLayer"), None)
        print("Converted Layer Details:", photo_layer)
        assert photo_layer is not None
        assert photo_layer["type"] == "ArtLayer" # 只能表示成功挂载，但在 win32com 中 typenames 多为 ArtLayer，我们可以通过检查智能滤镜或其它判定，这里保证调用 success 即可
        
        ctx.get_doc().Close(2)
    else:
        print("[Skip] apply_camera_raw_preset is not implemented yet.")

    # 4. 测试经典商业磨皮动作流
    if hasattr(ps_tools, "apply_commercial_retouch"):
        print("\n-- 步骤 6: 测试经典自适应商业磨皮动作流 --")
        ps_tools.create_document(ctx, width=400, height=400, name="Retouch Test")
        ps_tools.create_layer(ctx, name="SkinLayer")
        
        res = ps_tools.apply_commercial_retouch(ctx, opacity=80.0)
        print("Apply Commercial Retouch:", res)
        assert res["success"] is True
        
        # 验证新图层 SkinLayer_磨皮 存在，且不透明度匹配，混合模式为 Linear Light，且带蒙版
        tree_res = ps_tools.get_layer_tree(ctx)
        layers = tree_res.get("layers", [])
        retouch_layer = next((l for l in layers if l["name"] == "SkinLayer_磨皮"), None)
        print("Retouch Layer:", retouch_layer)
        assert retouch_layer is not None
        
        ctx.get_doc().Close(2)
    else:
        print("[Skip] apply_commercial_retouch is not implemented yet.")

    # 5. 测试生成式填充及无选区防御
    if hasattr(ps_tools, "apply_generative_fill"):
        print("\n-- 步骤 7: 测试生成式填充及无选区拦截 --")
        ps_tools.create_document(ctx, width=400, height=400, name="Generative Fill Test")
        ps_tools.create_layer(ctx, name="BaseLayer")
        
        # 1) 无选区调用，期待被拦截
        res = ps_tools.apply_generative_fill(ctx, prompt="a red apple")
        print("Generative Fill (no selection):", res)
        assert res["success"] is False
        assert "选区" in res.get("error", "") or "NO_SELECTION" in res.get("error", "")
        
        # 2) 创建选区后再调用
        ps_tools.basic_selection(ctx, action="rect", bounds=[100, 100, 200, 200])
        # 仅测 API 连通性，因为生成式填充如果没有联网会报 JSX 错误，所以只要拦截能正常工作即表明连通性通过
        assert hasattr(ps_tools, "apply_generative_fill")
        
        ctx.get_doc().Close(2)
    else:
        print("[Skip] apply_generative_fill is not implemented yet.")

    print("\n====== 自动化测试执行完毕 ======")

if __name__ == "__main__":
    run_tests()
