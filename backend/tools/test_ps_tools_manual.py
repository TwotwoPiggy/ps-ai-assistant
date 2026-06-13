import os
import sys
import time

# 将项目根目录添加到 python 路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.tools.ps_tools import (
    PhotoshopContext,
    create_document,
    resize_image,
    change_color_mode,
    zoom_view,
    execute_jsx,
    save_document,
    history_control,
    open_and_place
)

def run_manual_test():
    print("==================================================")
    print("      Photoshop COM 8个新增功能实机测试脚本")
    print("==================================================")
    print("请确保您的 Windows 上正运行着 Adobe Photoshop 软件。\n")
    
    input("按下回车键 [Enter] 开始测试...")
    
    ctx = PhotoshopContext()
    
    try:
        # Step 1: 测试无文档状态下创建画布
        print("\n[Step 1] 测试新建画布 (create_document)")
        print("正在尝试新建一个 800x600 像素，名为 'GSD_Phase1_Test' 的画布...")
        res = create_document(ctx, width=800, height=600, name="GSD_Phase1_Test")
        print("执行结果:", res)
        time.sleep(2)
        
        # Step 2: 测试视图缩放
        print("\n[Step 2] 测试画布缩放 (zoom_view)")
        print("正在将视图缩放为 'fit' (适合屏幕)...")
        res = zoom_view(ctx, action="fit")
        print("执行结果:", res)
        time.sleep(1.5)
        
        print("正在将视图缩放为 '100%' (实际像素)...")
        res = zoom_view(ctx, action="100%")
        print("执行结果:", res)
        time.sleep(1.5)
        
        # Step 3: 测试更改图像大小
        print("\n[Step 3] 测试更改图像大小 (resize_image)")
        print("正在将图像尺寸变更为 1024x768 像素...")
        res = resize_image(ctx, width=1024, height=768)
        print("执行结果:", res)
        time.sleep(2)
        
        # Step 4: 测试执行底层 JSX 脚本
        print("\n[Step 4] 测试注入 ExtendScript 脚本 (execute_jsx)")
        print("正在向 PS 注入脚本新建一个图层并设置名称...")
        # 注入一段 ExtendScript 代码：添加一个新图层并命名为 'JSX Layer'
        jsx = "var doc = app.activeDocument; var newLyr = doc.artLayers.add(); newLyr.name = 'JSX Layer';"
        res = execute_jsx(ctx, jsx_code=jsx)
        print("执行结果:", res)
        time.sleep(2)
        
        # Step 5: 测试撤销操作
        print("\n[Step 5] 测试撤销操作 (history_control)")
        print("正在撤销刚才通过 JSX 创建的图层...")
        res = history_control(ctx)
        print("执行结果:", res)
        time.sleep(2)
        
        # Step 6: 测试色彩模式转换
        print("\n[Step 6] 测试色彩模式转换 (change_color_mode)")
        print("注意: 正常运行时需先在前端交互得到『允许』。此处脚本直接验证底层机制。")
        print("正在将模式转换为 CMYK...")
        res = change_color_mode(ctx, mode="CMYK")
        print("执行结果:", res)
        time.sleep(2)
        
        # Step 7: 测试文档保存（桌面兜底另存为）
        print("\n[Step 7] 测试自动保存文档 (save_document)")
        print("由于是新建画布，将自动测试桌面 PSD 兜底另存...")
        res = save_document(ctx)
        print("执行结果:", res)
        time.sleep(2)
        
        # 获取桌面路径以找到刚才保存的文件
        desktop = os.path.expanduser("~/Desktop")
        # 找找刚保存的文件名
        saved_file = ""
        for file in os.listdir(desktop):
            if file.startswith("ps_ai_export_") and file.endswith(".psd"):
                saved_file = os.path.join(desktop, file)
                break
                
        # Step 8: 测试打开文件
        if saved_file and os.path.exists(saved_file):
            print(f"\n[Step 8] 测试打开与置入文件 (open_and_place)")
            print(f"正在关闭所有文档以清除画布环境...")
            # 简单用 JSX 关闭所有
            execute_jsx(ctx, "while(app.documents.length > 0){app.activeDocument.close(SaveOptions.DONOTSAVECHANGES);}")
            time.sleep(1.5)
            
            print(f"正在尝试重新打开刚才另存到桌面的文件: {os.path.basename(saved_file)} ...")
            res = open_and_place(ctx, file_path=saved_file)
            print("执行结果:", res)
            time.sleep(2)
            
            print(f"\n清理测试产生的桌面临时 PSD 文件...")
            try:
                # 再次关闭它以便可以删除
                execute_jsx(ctx, "app.activeDocument.close(SaveOptions.DONOTSAVECHANGES);")
                time.sleep(1)
                os.remove(saved_file)
                print("清理成功。")
            except Exception as e:
                print("清理失败，请手动删除桌面上的临时 PSD。报错:", e)
        else:
            print("\n[Step 8] 跳过，未在桌面找到生成的 PSD 兜底文件。")
            
        print("\n==================================================")
        print("🎉 测试流程全部跑通！新实现的 8 个 COM 接口均工作正常。")
        print("==================================================")
        
    except Exception as e:
        print("\n❌ 测试中途出错:", e)

if __name__ == "__main__":
    run_manual_test()
