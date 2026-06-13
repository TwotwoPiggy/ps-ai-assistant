import os
import time
import base64
import tempfile
import logging
import win32com.client

logger = logging.getLogger(__name__)

class PhotoshopContext:
    """Photoshop 运行上下文，用于纯函数工具与 Photoshop Agent 共享状态"""
    def __init__(self, layer_id_map=None, next_id_val=1):
        self.layer_id_map = layer_id_map if layer_id_map is not None else {}
        self.next_id_val = next_id_val

    def get_app(self):
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except Exception:
            pass
        return win32com.client.Dispatch("Photoshop.Application")

    def get_doc(self):
        ps_app = self.get_app()
        if ps_app.Documents.Count == 0:
            raise Exception("当前 Photoshop 中没有打开的文档，请先在 Photoshop 中打开或创建一个文档。")
        return ps_app.ActiveDocument

    def resolve_layer(self, doc, layer_identify: str):
        if not layer_identify:
            raise Exception("未指定图层标识符。")
        if layer_identify not in self.layer_id_map:
            raise Exception(f"未找到标识符为 {layer_identify} 的图层，请确认图层树是否是最新的。")
        path = self.layer_id_map[layer_identify]
        current = doc
        for idx in path:
            current = current.Layers.Item(idx)
        return current

# ==========================================
# Photoshop 纯函数工具集
# ==========================================

def _activate_layer(doc, layer_name: str = None):
    """根据图层名称递归查找并激活图层。如果未提供名称，则返回当前活动图层。"""
    if not layer_name:
        return doc.ActiveLayer

    def find_layer(container, name):
        for i in range(1, container.Count + 1):
            layer = container.Item(i)
            if layer.Name == name:
                return layer
            if layer.typename == "LayerSet":
                found = find_layer(layer.Layers, name)
                if found:
                    return found
        return None

    target = find_layer(doc.Layers, layer_name)
    if not target:
        raise Exception(f"未找到名称为 '{layer_name}' 的图层")
    
    doc.ActiveLayer = target
    return target

def get_layer_tree(ctx: PhotoshopContext) -> dict:
    """获取当前 Photoshop 文档的完整图层树结构，包括图层名称、ID、类型、可见性等。
    当你需要修改、删除、重命名图层或了解文档图层结构时，必须首先调用此函数获取最新的图层 ID。
    """
    try:
        doc = ctx.get_doc()
        ctx.layer_id_map = {}
        ctx.next_id_val = 1
        
        def traverse(container, path_prefix):
            nodes = []
            for i in range(1, container.Count + 1):
                layer = container.Item(i)
                current_path = path_prefix + [i]
                
                layer_id = f"layer_{ctx.next_id_val}"
                ctx.next_id_val += 1
                ctx.layer_id_map[layer_id] = current_path
                
                node = {
                    "id": layer_id,
                    "name": layer.Name,
                    "type": layer.typename,
                    "visible": layer.Visible,
                    "opacity": 100.0
                }
                
                if layer.typename == "ArtLayer":
                    try:
                        node["opacity"] = float(layer.Opacity)
                    except Exception:
                        pass
                
                if layer.typename == "LayerSet":
                    node["children"] = traverse(layer.Layers, current_path)
                    
                nodes.append(node)
            return nodes
            
        layers = traverse(doc.Layers, [])
        return {"success": True, "layers": layers}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_canvas_snapshot(ctx: PhotoshopContext) -> dict:
    """获取当前 Photoshop 画布的最新截图快照。
    当需要理解画面视觉内容（例如调整亮度和对比度、剪裁、或者根据视觉指示进行操作）时调用此函数。
    """
    temp_file = os.path.join(tempfile.gettempdir(), f"ps_snap_{int(time.time())}.jpg")
    try:
        doc = ctx.get_doc()
        options = win32com.client.Dispatch("Photoshop.ExportOptionsSaveForWeb")
        options.Format = 6  # JPEG
        options.Quality = 60
        
        doc.Export(ExportIn=temp_file, ExportAs=2, Options=options)
        with open(temp_file, "rb") as f:
            img_data = f.read()
        img_b64 = base64.b64encode(img_data).decode("utf-8")
        return {
            "success": True,
            "imageBase64": img_b64,
            "width": float(doc.Width),
            "height": float(doc.Height)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass

def create_layer(ctx: PhotoshopContext, name: str, opacity: float = 100.0, above: str = None) -> dict:
    """在 Photoshop 中创建一个新普通图层。
    
    Args:
        name: 新图层名称
        opacity: 不透明度百分比 (0 到 100)，默认 100
        above: 可选。目标图层标识符（如 'layer_1'）。如果指定，新图层将被移到该图层上方；不指定则放在最顶层。
    """
    try:
        doc = ctx.get_doc()
        new_layer = doc.ArtLayers.Add()
        new_layer.Name = name
        try:
            new_layer.Opacity = opacity
        except Exception:
            pass
        
        if above:
            target = ctx.resolve_layer(doc, above)
            new_layer.Move(target, 3)  # psPlaceBefore = 3
            
        return {"success": True, "message": f"成功创建图层 '{name}'"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def delete_layer(ctx: PhotoshopContext, layer_identify: str) -> dict:
    """删除 Photoshop 中的指定图层。
    
    Args:
        layer_identify: 目标图层标识符 (例如 'layer_1')
    """
    try:
        doc = ctx.get_doc()
        layer = ctx.resolve_layer(doc, layer_identify)
        layer_name = layer.Name
        layer.Delete()
        return {"success": True, "message": f"成功删除图层 '{layer_name}'"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def rename_layer(ctx: PhotoshopContext, layer_identify: str, new_name: str) -> dict:
    """重命名 Photoshop 中的指定图层。
    
    Args:
        layer_identify: 目标图层标识符 (例如 'layer_1')
        new_name: 新的图层名称
    """
    try:
        doc = ctx.get_doc()
        layer = ctx.resolve_layer(doc, layer_identify)
        old_name = layer.Name
        layer.Name = new_name
        return {"success": True, "message": f"已将图层 '{old_name}' 重命名为 '{new_name}'"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def set_layer_visibility(ctx: PhotoshopContext, layer_identify: str, visible: bool) -> dict:
    """设置 Photoshop 中指定图层的可见性 (显示或隐藏)。
    
    Args:
        layer_identify: 目标图层标识符 (例如 'layer_1')
        visible: true 表示显示图层，false 表示隐藏图层
    """
    try:
        doc = ctx.get_doc()
        layer = ctx.resolve_layer(doc, layer_identify)
        layer.Visible = visible
        state = "显示" if visible else "隐藏"
        return {"success": True, "message": f"已将图层 '{layer.Name}' 设置为{state}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def reorder_layer(ctx: PhotoshopContext, layer_identify: str, target_identify: str, placement: str) -> dict:
    """调整图层的顺序，将指定图层移动到相对于另一个目标图层的特定位置。
    
    Args:
        layer_identify: 要移动的图层标识符 (例如 'layer_1')
        target_identify: 放置位置的参照目标图层标识符 (例如 'layer_2')
        placement: 放置方式。只能是：'placeBefore' (放于上方), 'placeAfter' (放于下方), 或 'placeInside' (移入该图层组内部)
    """
    placement_map = {
        "placeBefore": 3,
        "placeAfter": 4,
        "placeInside": 2
    }
    if placement not in placement_map:
        return {"success": False, "error": f"无效的放置参数 '{placement}'，必须是 'placeBefore', 'placeAfter' 或 'placeInside'"}
        
    try:
        doc = ctx.get_doc()
        layer = ctx.resolve_layer(doc, layer_identify)
        target = ctx.resolve_layer(doc, target_identify)
        
        layer_name = layer.Name
        target_name = target.Name
        
        layer.Move(target, placement_map[placement])
        return {"success": True, "message": f"已将图层 '{layer_name}' 移至 '{target_name}' 的 {placement} 位置"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def adjust_brightness_contrast(ctx: PhotoshopContext, brightness: int, contrast: int, layer_identify: str = None) -> dict:
    """调整图层中图像的亮度和对比度。
    注意：必须在包含像素图像数据的图层上进行调整。如果是新创建的空白图层或图层组，操作将抛出错误。
    
    Args:
        brightness: 亮度变化量 (-150 到 150)
        contrast: 对比度变化量 (-50 到 100)
        layer_identify: 可选。指定图层标识符。如果不提供，将应用于当前激活/选中的图层。
    """
    try:
        doc = ctx.get_doc()
        if layer_identify:
            layer = ctx.resolve_layer(doc, layer_identify)
            doc.ActiveLayer = layer
        else:
            layer = doc.ActiveLayer
            
        layer_name = layer.Name
        layer.AdjustBrightnessContrast(brightness, contrast)
        return {"success": True, "message": f"成功将图层 '{layer_name}' 的亮度调整为 {brightness}，对比度调整为 {contrast}"}
    except Exception as e:
        return {
            "success": False, 
            "error": f"调整亮度对比度失败，这可能是因为当前图层没有图像数据(例如是空白图层或图层组)。详细报错: {str(e)}"
        }

def crop_canvas(ctx: PhotoshopContext, top: float, left: float, bottom: float, right: float) -> dict:
    """裁剪画布至指定的像素边界。
    
    Args:
        top: 裁剪区域上边界的像素坐标
        left: 裁剪区域左边界的像素坐标
        bottom: 裁剪区域下边界的像素坐标
        right: 裁剪区域右边界的像素坐标
    """
    try:
        doc = ctx.get_doc()
        doc.Crop([left, top, right, bottom])
        return {"success": True, "message": f"画布成功裁剪至区域: left={left}, top={top}, right={right}, bottom={bottom}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def resize_canvas(ctx: PhotoshopContext, width: int, height: int, anchor: str = 'middleCenter') -> dict:
    """更改画布尺寸的大小（像素）。
    
    Args:
        width: 新画布的宽度 (像素)
        height: 新画布的高度 (像素)
        anchor: 可选。锚点位置，控制尺寸扩展的方向。
                可选值: 'topLeft', 'topCenter', 'topRight', 'leftCenter', 'middleCenter', 'rightCenter', 'bottomLeft', 'bottomCenter', 'bottomRight'。默认 'middleCenter'。
    """
    anchor_map = {
        'topLeft': 1,
        'topCenter': 2, 'top': 2,
        'topRight': 3,
        'leftCenter': 4, 'left': 4,
        'middleCenter': 5, 'center': 5,
        'rightCenter': 6, 'right': 6,
        'bottomLeft': 7,
        'bottomCenter': 8, 'bottom': 8,
        'bottomRight': 9
    }
    if anchor not in anchor_map:
        return {"success": False, "error": f"无效的锚点参数 '{anchor}'"}
        
    try:
        doc = ctx.get_doc()
        doc.ResizeCanvas(width, height, anchor_map[anchor])
        return {"success": True, "message": f"画布尺寸已成功调整为 {width}x{height}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def flip_image(ctx: PhotoshopContext, direction: str) -> dict:
    """水平或垂直翻转当前整个文档图像。
    
    Args:
        direction: 翻转方向，只能是 'horizontal' 或 'vertical'
    """
    direction_map = {
        "horizontal": 1,
        "vertical": 2
    }
    if direction not in direction_map:
        return {"success": False, "error": f"无效的翻转方向 '{direction}'，只能为 'horizontal' 或 'vertical'"}
        
    try:
        doc = ctx.get_doc()
        doc.FlipCanvas(direction_map[direction])
        return {"success": True, "message": f"画布已成功进行了 {direction} 翻转"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def execute_jsx(ctx: PhotoshopContext, jsx_code: str) -> dict:
    """向 Photoshop 注入并执行一段 JavaScript (JSX) 脚本。
    
    Args:
        jsx_code: 要注入执行的 ExtendScript 脚本代码
    """
    try:
        logger.debug(f"Executing JSX code:\n{jsx_code}")
        result = ctx.get_app().DoJavaScript(jsx_code)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

def create_document(ctx: PhotoshopContext, width: int, height: int, resolution: float = 72.0, name: str = "New Document") -> dict:
    """在 Photoshop 中新建一个指定宽高、分辨率和名称的空白文档（画布）。
    支持在无打开文档的状态下运行。
    
    Args:
        width: 新建文档的宽度 (像素)
        height: 新建文档的高度 (像素)
        resolution: 分辨率 (像素/英寸)，默认 72.0
        name: 文档标题名称，默认 "New Document"
    """
    try:
        app = ctx.get_app()
        new_doc = app.Documents.Add(width, height, resolution, name)
        return {"success": True, "message": f"成功创建新文档 '{new_doc.Name}' ({width}x{height} px, {resolution} ppi)"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def open_and_place(ctx: PhotoshopContext, file_path: str) -> dict:
    """在 Photoshop 中打开指定路径的文件并置入画布中。
    支持在无打开文档的状态下运行。
    
    Args:
        file_path: 待打开或置入的本地图像文件绝对路径
    """
    try:
        app = ctx.get_app()
        opened_doc = app.Open(file_path)
        return {"success": True, "message": f"成功打开并置入文件: '{opened_doc.Name}'"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def save_document(ctx: PhotoshopContext, file_path: str = None) -> dict:
    """保存当前活动的 Photoshop 文档。
    
    Args:
        file_path: 可选。保存的目标绝对文件路径。
                   如果未提供，且文档是新建未曾存盘的，则会自动以 ps_ai_export_{时间戳}.psd 命名保存至用户的系统桌面。
    """
    try:
        doc = ctx.get_doc()
        if not file_path:
            try:
                # 获取当前文档已有关联 the 物理文件路径
                file_path = str(doc.FullName)
            except Exception:
                file_path = ""
            
            # 如果没有关联路径（新建文档，FullName 不可达或不是绝对路径）
            if not file_path or not os.path.isabs(file_path):
                desktop = os.path.expanduser("~/Desktop")
                timestamp = int(time.time())
                file_path = os.path.join(desktop, f"ps_ai_export_{timestamp}.psd")
        
        # 统一规范化路径格式
        file_path = os.path.abspath(file_path)
        doc.SaveAs(file_path)
        return {"success": True, "message": f"文档已成功保存至: '{file_path}'"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def resize_image(ctx: PhotoshopContext, width: int, height: int) -> dict:
    """调整当前 Photoshop 图像的物理尺寸大小。
    
    Args:
        width: 目标图像的宽度 (像素)
        height: 目标图像的高度 (像素)
    """
    try:
        doc = ctx.get_doc()
        doc.ResizeImage(width, height)
        return {"success": True, "message": f"图像物理尺寸已成功调整为 {width}x{height}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def change_color_mode(ctx: PhotoshopContext, mode: str) -> dict:
    """更改当前活动的 Photoshop 文档的色彩模式。
    
    执行此工具前，必须先在聊天界面提示用户即将进行色彩转换，等待用户明确回复『允许 (allow)』后才可调用。
    
    Args:
        mode: 目标色彩模式。可选值包括: 'RGB', 'CMYK', 'Grayscale', 'Lab'。
    """
    mode_map = {
        "grayscale": 1,
        "gray": 1,
        "rgb": 2,
        "cmyk": 3,
        "lab": 4
    }
    target_mode = mode.lower().strip()
    if target_mode not in mode_map:
        return {"success": False, "error": f"不支持的色彩模式 '{mode}'。可选模式有: 'RGB', 'CMYK', 'Grayscale', 'Lab'。"}
        
    try:
        app = ctx.get_app()
        # 备份原先的弹窗设置
        orig_dialogs = app.DisplayDialogs
        # 设置为 psDisplayNoDialogs = 3 以拦截所有警告弹窗
        app.DisplayDialogs = 3
        
        doc = ctx.get_doc()
        doc.ChangeMode(mode_map[target_mode])
        
        # 还原弹窗设置
        app.DisplayDialogs = orig_dialogs
        return {"success": True, "message": f"成功将色彩模式转换为 {mode.upper()}"}
    except Exception as e:
        try:
            app.DisplayDialogs = orig_dialogs
        except Exception:
            pass
        return {"success": False, "error": str(e)}

def history_control(ctx: PhotoshopContext) -> dict:
    """撤销上一步在 Photoshop 中执行的操作。
    """
    try:
        app = ctx.get_app()
        app.DoJavaScript("app.runMenuItem(charIDToTypeID('undo'));")
        return {"success": True, "message": "成功执行撤销 (Undo) 操作"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def zoom_view(ctx: PhotoshopContext, action: str) -> dict:
    """调整当前 Photoshop 文档的画布视图缩放比例。
    
    Args:
        action: 缩放行为。支持的值有：
                - '100%': 缩放到实际像素大小
                - 'fit': 适合屏幕大小
    """
    try:
        app = ctx.get_app()
        if action == '100%':
            app.DoJavaScript("app.runMenuItem(stringIDToTypeID('actualPixels'));")
            msg = "实际像素 (100%)"
        elif action == 'fit':
            app.DoJavaScript("app.runMenuItem(stringIDToTypeID('fitOnScreen'));")
            msg = "适合屏幕"
        else:
            return {"success": False, "error": f"不支持的缩放指令 '{action}'。只支持 '100%' 和 'fit'。"}
        return {"success": True, "message": f"视图已成功调整为 {msg}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def group_layers(ctx: PhotoshopContext, layer_names: list, group_name: str) -> dict:
    """将指定名称的多个图层进行编组（创建一个新的图层组并将它们移入）。
    
    Args:
        layer_names: 待编组的图层名称列表
        group_name: 新创建的图层组的名称
    """
    try:
        doc = ctx.get_doc()
        new_group = doc.LayerSets.Add()
        new_group.Name = group_name
        
        for name in layer_names:
            layer = _activate_layer(doc, name)
            layer.Move(new_group, 2)  # psPlaceInside = 2
            
        return {"success": True, "message": f"成功将 {len(layer_names)} 个图层编入组 '{group_name}'"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def set_layer_opacity_and_fill(ctx: PhotoshopContext, opacity: float = None, fill: float = None, layer_name: str = None) -> dict:
    """设置图层的不透明度与填充。如果不指定层名，则对当前活动层生效。
    
    Args:
        opacity: 图层的不透明度百分比 (0 到 100)
        fill: 图层的填充不透明度百分比 (0 到 100)
        layer_name: 可选。目标图层名称
    """
    try:
        doc = ctx.get_doc()
        layer = _activate_layer(doc, layer_name)
        
        if opacity is not None:
            layer.Opacity = opacity
            
        if fill is not None:
            try:
                layer.FillOpacity = fill
            except Exception:
                pass  # 图层组可能不支持 FillOpacity
                
        return {"success": True, "message": f"成功更新图层 '{layer.Name}' 的透明度参数"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def set_layer_blend_mode(ctx: PhotoshopContext, blend_mode: str, layer_name: str = None) -> dict:
    """设置图层的混合模式。如果不指定层名，则对当前活动层生效。
    
    Args:
        blend_mode: 混合模式，例如 'normal', 'multiply', 'screen', 'overlay', 'softLight', 'hardLight', 'colorDodge', 'colorBurn', 'linearBurn', 'linearDodge' 等
        layer_name: 可选。目标图层名称
    """
    try:
        doc = ctx.get_doc()
        layer = _activate_layer(doc, layer_name)
        
        mode_map = {
            "normal": "BlendMode.NORMAL",
            "multiply": "BlendMode.MULTIPLY",
            "screen": "BlendMode.SCREEN",
            "overlay": "BlendMode.OVERLAY",
            "softlight": "BlendMode.SOFTLIGHT",
            "hardlight": "BlendMode.HARDLIGHT",
            "colordodge": "BlendMode.COLORDODGE",
            "colorburn": "BlendMode.COLORBURN",
            "linearburn": "BlendMode.LINEARBURN",
            "lineardodge": "BlendMode.LINEARDODGE",
            "darken": "BlendMode.DARKEN",
            "lighten": "BlendMode.LIGHTEN",
            "difference": "BlendMode.DIFFERENCE",
            "exclusion": "BlendMode.EXCLUSION",
            "hue": "BlendMode.HUE",
            "saturation": "BlendMode.SATURATION",
            "color": "BlendMode.COLOR",
            "luminosity": "BlendMode.LUMINOSITY"
        }
        
        jsx_mode = mode_map.get(blend_mode.lower(), "BlendMode.NORMAL")
        
        jsx_code = f"""
        var layer = app.activeDocument.activeLayer;
        layer.blendMode = {jsx_mode};
        """
        res = execute_jsx(ctx, jsx_code)
        if not res["success"]:
            raise Exception(res.get("error", "JSX 执行失败"))
            
        return {"success": True, "message": f"成功将图层 '{layer.Name}' 的混合模式设置为 '{blend_mode}'"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def move_layer(ctx: PhotoshopContext, x: float = None, y: float = None, dx: float = None, dy: float = None, layer_name: str = None) -> dict:
    """移动图层的坐标位置（支持绝对坐标 x/y 或相对偏移 dx/dy）。如果不指定层名，则对当前活动层生效。
    
    Args:
        x: 目标绝对 X 坐标
        y: 目标绝对 Y 坐标
        dx: 相对水平偏移量
        dy: 相对垂直偏移量
        layer_name: 可选。目标图层名称
    """
    try:
        doc = ctx.get_doc()
        layer = _activate_layer(doc, layer_name)
        
        delta_x, delta_y = 0.0, 0.0
        
        if x is not None and y is not None:
            bounds = layer.Bounds
            current_x = bounds[0]
            current_y = bounds[1]
            delta_x = x - current_x
            delta_y = y - current_y
        else:
            if dx is not None:
                delta_x = dx
            if dy is not None:
                delta_y = dy
                
        layer.Translate(delta_x, delta_y)
        return {"success": True, "message": f"成功移动图层 '{layer.Name}'"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def merge_layers(ctx: PhotoshopContext, merge_type: str = "mergeDown", layer_name: str = None) -> dict:
    """合并图层。支持向下合并、合并可见图层、拼合图像。如果不指定层名，则对当前活动层生效。
    
    Args:
        merge_type: 合并类型。'mergeDown' (向下合并), 'mergeVisible' (合并可见), 'flattenImage' (拼合图像)
        layer_name: 可选。目标图层名称
    """
    try:
        doc = ctx.get_doc()
        layer = _activate_layer(doc, layer_name)
        
        if merge_type == "mergeDown":
            layer.Merge()
        elif merge_type == "mergeVisible":
            doc.MergeVisibleLayers()
        elif merge_type == "flattenImage":
            doc.Flatten()
        else:
            return {"success": False, "error": f"无效的合并类型: {merge_type}"}
            
        return {"success": True, "message": f"成功执行图层合并 ({merge_type})"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def duplicate_layer(ctx: PhotoshopContext, layer_name: str = None, new_name: str = None) -> dict:
    """复制图层。如果不指定层名，则对当前活动层生效。
    
    Args:
        layer_name: 可选。目标图层名称
        new_name: 可选。复制后的新图层名称
    """
    try:
        doc = ctx.get_doc()
        layer = _activate_layer(doc, layer_name)
        
        dup = layer.Duplicate()
        if new_name:
            dup.Name = new_name
            
        return {"success": True, "message": f"成功复制图层 '{layer.Name}'，新图层名: '{dup.Name}'"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def rasterize_layer(ctx: PhotoshopContext, layer_name: str = None) -> dict:
    """栅格化图层（支持幂等，已是普通图层则直接静默成功）。如果不指定层名，则对当前活动层生效。
    
    Args:
        layer_name: 可选。目标图层名称
    """
    try:
        doc = ctx.get_doc()
        layer = _activate_layer(doc, layer_name)
        
        jsx_code = """
        var layer = app.activeDocument.activeLayer;
        if (layer.kind != LayerKind.NORMAL) {
            layer.rasterize(RasterizeType.ENTIRELAYER);
        }
        """
        res = execute_jsx(ctx, jsx_code)
        if not res["success"]:
            raise Exception(res.get("error", "JSX 执行失败"))
            
        return {"success": True, "message": f"成功栅格化图层 '{layer.Name}'"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def convert_to_smart_object(ctx: PhotoshopContext, layer_name: str = None) -> dict:
    """将图层转换为智能对象（支持幂等，已是智能对象则直接静默成功）。如果不指定层名，则对当前活动层生效。
    
    Args:
        layer_name: 可选。目标图层名称
    """
    try:
        doc = ctx.get_doc()
        layer = _activate_layer(doc, layer_name)
        
        jsx_code = """
        var layer = app.activeDocument.activeLayer;
        if (layer.kind != LayerKind.SMARTOBJECT) {
            executeAction(stringIDToTypeID("newPlacedLayer"), undefined, DialogModes.NO);
        }
        """
        res = execute_jsx(ctx, jsx_code)
        if not res["success"]:
            raise Exception(res.get("error", "JSX 执行失败"))
            
        return {"success": True, "message": f"成功将图层 '{layer.Name}' 转换为智能对象"}
    except Exception as e:
        return {"success": False, "error": str(e)}
