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
                # 图层组(LayerSet)的 DOM 不支持直接设置 FillOpacity，需要使用 ActionManager 回退处理
                jsx_code = f"""
                try {{
                    var idsetd = charIDToTypeID( "setd" );
                    var desc1 = new ActionDescriptor();
                    var idnull = charIDToTypeID( "null" );
                    var ref1 = new ActionReference();
                    var idLyr = charIDToTypeID( "Lyr " );
                    var idOrdn = charIDToTypeID( "Ordn" );
                    var idTrgt = charIDToTypeID( "Trgt" );
                    ref1.putEnumerated( idLyr, idOrdn, idTrgt );
                    desc1.putReference( idnull, ref1 );
                    var idT = charIDToTypeID( "T   " );
                    var desc2 = new ActionDescriptor();
                    var idfillOpacity = stringIDToTypeID( "fillOpacity" );
                    var idPrc = charIDToTypeID( "#Prc" );
                    desc2.putUnitDouble( idfillOpacity, idPrc, {fill} );
                    var idLyr = charIDToTypeID( "Lyr " );
                    desc1.putObject( idT, idLyr, desc2 );
                    executeAction( idsetd, desc1, DialogModes.NO );
                }} catch(e) {{
                    // 如果依然失败则静默
                }}
                """
                execute_jsx(ctx, jsx_code)
                
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
        
        try:
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
        except Exception as e:
            err_msg = str(e).lower()
            if "空" in err_msg or "empty" in err_msg or "bounds" in err_msg or "矩形" in err_msg:
                return {"success": True, "message": f"图层 '{layer.Name}' 是空图层，无需也无法移动，已自动静默处理。"}
            raise e
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
            err_msg = res.get("error", "").lower()
            if "空" in err_msg or "empty" in err_msg or "bounds" in err_msg or "矩形" in err_msg or "not currently available" in err_msg or "不可用" in err_msg:
                return {"success": True, "message": f"图层 '{layer.Name}' 为空图层或已经是普通图层，无需栅格化，已自动忽略。"}
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
            var isEmpty = false;
            try {
                var b = layer.bounds;
                if (b[0].value == 0 && b[1].value == 0 && b[2].value == 0 && b[3].value == 0) {
                    isEmpty = true;
                }
            } catch(e) {
                isEmpty = true;
            }
            if (isEmpty) {
                throw new Error("EMPTY_LAYER_ERROR");
            }
            executeAction(stringIDToTypeID("newPlacedLayer"), undefined, DialogModes.NO);
        }
        """
        res = execute_jsx(ctx, jsx_code)
        if not res["success"]:
            err_msg = res.get("error", "").lower()
            if "empty_layer_error" in err_msg or "空" in err_msg or "empty" in err_msg or "bounds" in err_msg:
                # 明确向 AI 报告错误，引导 AI 提示用户，而不是静默成功，防止后续操作基于错误的智能对象假设
                return {"success": False, "error": f"无法将空图层 '{layer.Name}' 转换为智能对象。请先在图层上添加可见的像素内容。"}
            raise Exception(res.get("error", "JSX 执行失败"))
            
        return {"success": True, "message": f"成功将图层 '{layer.Name}' 转换为智能对象"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def basic_selection(ctx: PhotoshopContext, action: str, bounds: list = None, selection_mode: str = 'replace') -> dict:
    """在 Photoshop 中进行基础选区控制（创建矩形/椭圆选区、全选、反选、取消选择）。

    Args:
        action: 选区行为。可选值：'rect' (创建矩形选区), 'ellipse' (创建椭圆选区), 'all' (全选), 'invert' (反选), 'deselect' (取消选择)
        bounds: 创建选区时的边界坐标 [top, left, bottom, right] (像素)，仅在 action 为 'rect' 或 'ellipse' 时需要。
        selection_mode: 选区模式。可选值：'replace' (替代当前选区), 'add' (添加到选区), 'subtract' (从选区减去), 'intersect' (与当前选区交叉)。默认 'replace'。
    """
    try:
        doc = ctx.get_doc()
        
        # 处理不需要 bounds 的全局选区操作
        if action == 'all':
            doc.Selection.SelectAll()
            return {"success": True, "message": "已全选当前画布"}
        elif action == 'invert':
            doc.Selection.Invert()
            return {"success": True, "message": "已反选当前选区"}
        elif action == 'deselect':
            doc.Selection.Deselect()
            return {"success": True, "message": "已取消当前所有选区"}
            
        # 针对需要 bounds 的操作 (rect, ellipse)
        if action not in ['rect', 'ellipse']:
            return {"success": False, "error": f"不支持的选区操作动作 '{action}'"}
            
        if not bounds or not isinstance(bounds, (list, tuple)) or len(bounds) != 4:
            return {"success": False, "error": "创建选区需要有效的 bounds 参数，格式为 [top, left, bottom, right]"}
            
        top, left, bottom, right = bounds
        
        # 使用 JSX 统一处理矩形与椭圆选区，因为 COM 传递嵌套数组易出错，且 DOM 不直接支持椭圆选区
        jsx_code = f"""
        (function() {{
            var top = {top};
            var left = {left};
            var bottom = {bottom};
            var right = {right};
            var mode = "{selection_mode.lower()}";
            var shape = "{action}";
            
            var actionID = charIDToTypeID("setd");
            if (mode === "add") actionID = charIDToTypeID("Add ");
            else if (mode === "subtract") actionID = charIDToTypeID("Sbt ");
            else if (mode === "intersect") actionID = charIDToTypeID("Intr");

            var desc1 = new ActionDescriptor();
            var ref1 = new ActionReference();
            ref1.putProperty( charIDToTypeID("Chnl"), charIDToTypeID("fsel") );
            desc1.putReference( charIDToTypeID("null"), ref1 );
            
            var desc2 = new ActionDescriptor();
            desc2.putUnitDouble( charIDToTypeID("Top "), charIDToTypeID("#Rlt"), top );
            desc2.putUnitDouble( charIDToTypeID("Left"), charIDToTypeID("#Rlt"), left );
            desc2.putUnitDouble( charIDToTypeID("Btom"), charIDToTypeID("#Rlt"), bottom );
            desc2.putUnitDouble( charIDToTypeID("Rght"), charIDToTypeID("#Rlt"), right );
            
            var shapeID = charIDToTypeID(shape === "ellipse" ? "Elps" : "Rctn");
            desc1.putObject( charIDToTypeID("T   "), shapeID, desc2 );
            executeAction( actionID, desc1, DialogModes.NO );
            return "success";
        }})();
        """
        
        res = execute_jsx(ctx, jsx_code)
        if not res["success"]:
            raise Exception(res.get("error", "JSX 执行失败"))
            
        shape_cn = "矩形" if action == 'rect' else "椭圆"
        mode_cn = {"replace": "新选区", "add": "加选", "subtract": "减选", "intersect": "交叉"}.get(selection_mode, selection_mode)
        return {"success": True, "message": f"成功创建{shape_cn}选区({mode_cn}): top={top}, left={left}, bottom={bottom}, right={right}"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def modify_selection(ctx: PhotoshopContext, action: str, value: int) -> dict:
    """修改当前的选区边界（羽化、扩展、收缩、平滑、边界）。

    Args:
        action: 修改类型。可选值：'feather' (羽化), 'expand' (扩展), 'contract' (收缩), 'smooth' (平滑), 'border' (边界)。
        value: 修改像素值 (正整数，通常为 1-100)。
    """
    if value <= 0:
        return {"success": False, "error": f"无效的修改像素值 {value}，必须为正整数"}
        
    action_map = {
        'feather': '羽化',
        'expand': '扩展',
        'contract': '收缩',
        'smooth': '平滑',
        'border': '边界'
    }
    
    if action not in action_map:
        return {"success": False, "error": f"不支持的选区修改类型 '{action}'"}
        
    try:
        jsx_code = f"""
        (function() {{
            var action = "{action}";
            var val = {value};
            var sel = app.activeDocument.selection;
            if (action === "feather") {{
                sel.feather(val);
            }} else if (action === "expand") {{
                sel.expand(val);
            }} else if (action === "contract") {{
                sel.contract(val);
            }} else if (action === "smooth") {{
                sel.smooth(val);
            }} else if (action === "border") {{
                sel.border(val);
            }}
            return "success";
        }})();
        """
        
        res = execute_jsx(ctx, jsx_code)
        if not res["success"]:
            # 当当前没有活跃的选区时，上述方法在 JSX 中会抛出错误
            err_msg = res.get("error", "").lower()
            if "not exist" in err_msg or "empty" in err_msg or "selection" in err_msg:
                return {"success": False, "error": "当前画面中没有选区，请先创建选区后再进行修改"}
            raise Exception(res.get("error", "JSX 执行失败"))
            
        return {"success": True, "message": f"已成功将当前选区进行 {action_map[action]} 处理，像素值: {value}"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def smart_selection(ctx: PhotoshopContext, action: str) -> dict:
    """使用 Photoshop 的 AI 智能功能快速处理选区（智能选择主体、自动删除背景）。

    Args:
        action: 智能处理动作。可选值：'subject' (选择图像中的主体物), 'remove_bg' (智能移除图像背景)。
    """
    if action not in ['subject', 'remove_bg']:
        return {"success": False, "error": f"不支持的智能动作 '{action}'"}
        
    try:
        if action == 'subject':
            # 智能主体选择的 ActionManager 脚本
            jsx_code = """
            (function() {
                try { app.activeDocument.selection.deselect(); } catch(e) {}
                
                var idautoCutout = stringIDToTypeID( "autoCutout" );
                var desc = new ActionDescriptor();
                var idsampleAllLayers = stringIDToTypeID( "sampleAllLayers" );
                desc.putBoolean( idsampleAllLayers, false );
                executeAction( idautoCutout, desc, DialogModes.NO );
                
                var hasSelection = false;
                try {
                    var sb = app.activeDocument.selection.bounds;
                    hasSelection = true;
                } catch(e) {}
                
                if (!hasSelection) {
                    throw new Error("NO_SUBJECT_FOUND");
                }
                return "success";
            })();
            """
            action_desc = "智能选择主体"
        else:
            # 自动移除背景的 ActionManager 脚本
            jsx_code = """
            (function() {
                var idquickActionRemoveBackground = stringIDToTypeID( "quickActionRemoveBackground" );
                var desc = new ActionDescriptor();
                executeAction( idquickActionRemoveBackground, desc, DialogModes.NO );
                
                var ref = new ActionReference();
                ref.putEnumerated( charIDToTypeID("Lyr "), charIDToTypeID("Ordn"), charIDToTypeID("Trgt") );
                var layerDesc = executeActionGet(ref);
                if (!layerDesc.getBoolean(stringIDToTypeID("hasUserMask"))) {
                    throw new Error("NO_SUBJECT_FOUND");
                }
                return "success";
            })();
            """
            action_desc = "自动移除背景"
            
        res = execute_jsx(ctx, jsx_code)
        if not res["success"]:
            # 捕获 AI 工具失败时的异常，返回友好的中文提示
            logger.warning(f"智能动作失败: {res.get('error')}")
            return {"success": False, "error": f"{action_desc}失败或未在当前图像中找到合适的主体，请确认当前图层包含清晰的前景物体。"}
            
        return {"success": True, "message": f"成功执行{action_desc}"}
        
    except Exception as e:
        return {"success": False, "error": f"{action_desc}失败: {str(e)}"}


def mask_control(ctx: PhotoshopContext, action: str, layer_identify: str = None, force_apply: bool = False) -> dict:
    """控制 Photoshop 指定图层的蒙版状态（新建、应用、删除蒙版，或者启用、停用蒙版）。如果不指定图层标识符，则自动对当前活动图层生效。

    Args:
        action: 蒙版操作动作。可选值：
                - 'add': 从当前选区创建图层蒙版（如果没有选区，则创建全显蒙版）
                - 'apply': 应用蒙版（破坏性像素混合）
                - 'delete': 删除/丢弃蒙版而不应用
                - 'enable': 启用蒙版
                - 'disable': 停用蒙版
        layer_identify: 可选。目标图层标识符 (例如 'layer_1')。如果不提供，将应用于当前激活/选中的图层。
        force_apply: 是否强制执行应用蒙版操作。应用蒙版属于破坏性像素修改，默认为 False。必须显式设为 True 才能执行 'apply' 操作。
    """
    if action == 'apply' and not force_apply:
        return {
            "success": False, 
            "error": "应用蒙版是破坏性操作（会导致被隐藏的像素永久丢失）。如果确认要应用并合并蒙版，请将 force_apply 参数显式设置为 True。"
        }
        
    action_map = {
        'add': '添加蒙版',
        'apply': '应用蒙版',
        'delete': '删除蒙版',
        'enable': '启用蒙版',
        'disable': '停用蒙版'
    }
    
    if action not in action_map:
        return {"success": False, "error": f"不支持的蒙版操作 '{action}'"}
        
    try:
        doc = ctx.get_doc()
        if layer_identify:
            layer = ctx.resolve_layer(doc, layer_identify)
            doc.ActiveLayer = layer
        else:
            layer = doc.ActiveLayer
            
        # 使用 JSX 进行蒙版的高级 ActionManager 操作
        if action == 'add':
            # 创建蒙版：如果有选区则从选区创建，否则创建全显蒙版
            jsx_code = """
            (function() {
                var hasSelection = false;
                try {
                    var sb = app.activeDocument.selection.bounds;
                    hasSelection = true;
                } catch(e) {}
                
                var idMk = charIDToTypeID( "Mk  " );
                var desc2 = new ActionDescriptor();
                desc2.putClass( charIDToTypeID( "Nw  " ), charIDToTypeID( "Chnl" ) );
                var ref1 = new ActionReference();
                ref1.putEnumerated( charIDToTypeID( "Chnl" ), charIDToTypeID( "Chnl" ), charIDToTypeID( "Msk " ) );
                desc2.putReference( charIDToTypeID( "At  " ), ref1 );
                var usingVal = hasSelection ? "RvlS" : "RvlA";
                desc2.putEnumerated( charIDToTypeID( "Usng" ), charIDToTypeID( "UsrM" ), charIDToTypeID( usingVal ) );
                executeAction( idMk, desc2, DialogModes.NO );
                return "success";
            })();
            """
        elif action in ['apply', 'delete']:
            # 应用或删除/丢弃蒙版
            apply_val = "true" if action == 'apply' else "false"
            jsx_code = f"""
            (function() {{
                var iddlt = charIDToTypeID( "dlt " );
                var desc = new ActionDescriptor();
                var ref = new ActionReference();
                ref.putEnumerated( charIDToTypeID( "Chnl" ), charIDToTypeID( "Chnl" ), charIDToTypeID( "Msk " ) );
                desc.putReference( charIDToTypeID( "null" ), ref );
                desc.putBoolean( charIDToTypeID( "Aply" ), {apply_val} );
                executeAction( iddlt, desc, DialogModes.NO );
                return "success";
            }})();
            """
        else:  # enable 或 disable
            usr_mask = "true" if action == 'enable' else "false"
            jsx_code = f"""
            (function() {{
                var idsetd = charIDToTypeID( "setd" );
                var desc1 = new ActionDescriptor();
                var ref1 = new ActionReference();
                ref1.putEnumerated( charIDToTypeID( "Chnl" ), charIDToTypeID( "Chnl" ), charIDToTypeID( "Msk " ) );
                desc1.putReference( charIDToTypeID( "null" ), ref1 );
                var desc2 = new ActionDescriptor();
                desc2.putBoolean( charIDToTypeID( "UsrM" ), {usr_mask} );
                desc1.putObject( charIDToTypeID( "T   " ), charIDToTypeID( "Chnl" ), desc2 );
                executeAction( idsetd, desc1, DialogModes.NO );
                return "success";
            }})();
            """
            
        res = execute_jsx(ctx, jsx_code)
        if not res["success"]:
            # 通常蒙版操作失败是因为当前图层并没有蒙版（例如在没有蒙版时执行 apply, delete, enable, disable）
            err_msg = res.get("error", "").lower()
            if "not available" in err_msg or "error" in err_msg:
                return {"success": False, "error": f"对图层 '{layer.Name}' 执行{action_map[action]}失败，可能是由于该图层不存在图层蒙版。"}
            raise Exception(res.get("error", "JSX 执行失败"))
            
        return {"success": True, "message": f"成功在图层 '{layer.Name}' 上执行{action_map[action]}操作"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def channel_control(ctx: PhotoshopContext, action: str, channel_name: str = None) -> dict:
    """控制选区的通道存储和载入（实现选区的存储与读取）。

    Args:
        action: 通道控制动作。可选值：'save_selection' (将当前选区存储为通道), 'load_selection' (从已有通道载入选区)。
        channel_name: 通道名称。如果存储选区时未指定，系统会自动以 Selection_YYYYMMDD_HHMMSS 格式命名。
    """
    if action not in ['save_selection', 'load_selection']:
        return {"success": False, "error": f"不支持的通道操作 '{action}'"}
        
    try:
        if action == 'save_selection':
            if not channel_name:
                channel_name = f"Selection_{time.strftime('%Y%m%d_%H%M%S')}"
                
            jsx_code = f"""
            (function() {{
                var chanName = "{channel_name}";
                var doc = app.activeDocument;
                var newChan = doc.channels.add();
                newChan.name = chanName;
                doc.selection.store(newChan, SelectionType.REPLACE);
                return "success";
            }})();
            """
            res = execute_jsx(ctx, jsx_code)
            if not res["success"]:
                err_msg = res.get("error", "").lower()
                if "no selection" in err_msg or "empty" in err_msg or "selection" in err_msg:
                    return {"success": False, "error": "当前画面中没有选区，无法保存为空通道"}
                raise Exception(res.get("error", "JSX 执行失败"))
                
            return {"success": True, "message": f"已成功将当前选区存入通道，通道名称为: '{channel_name}'"}
            
        else:  # load_selection
            if not channel_name:
                return {"success": False, "error": "载入选区必须指定 channel_name"}
                
            jsx_code = f"""
            (function() {{
                var chanName = "{channel_name}";
                var doc = app.activeDocument;
                var chan = null;
                for (var i = 0; i < doc.channels.length; i++) {{
                    if (doc.channels[i].name === chanName) {{
                        chan = doc.channels[i];
                        break;
                    }}
                }}
                if (!chan) {{
                    throw new Error("NOT_FOUND");
                }}
                doc.selection.load(chan, SelectionType.REPLACE);
                return "success";
            }})();
            """
            res = execute_jsx(ctx, jsx_code)
            if not res["success"]:
                err_msg = res.get("error", "").lower()
                if "not_found" in err_msg:
                    return {"success": False, "error": f"在当前文档中未找到名称为 '{channel_name}' 的通道"}
                raise Exception(res.get("error", "JSX 执行失败"))
                
            return {"success": True, "message": f"已成功从通道 '{channel_name}' 中载入选区"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def set_color(ctx: PhotoshopContext, target: str, color_format: str, color_value: any) -> dict:
    """设置前景色或背景色。
    
    当用户要求设置或应用一个模糊颜色且提供了参考图片时，大模型应该主动利用多模态视觉能力提取图片中主色调的 HEX 值传入此方法。
    
    Args:
        target: 'foreground' 或 'background'
        color_format: 'hex', 'rgb', 'hsb', 'cmyk'
        color_value: 色值。'hex'应为'#RRGGBB'或'RRGGBB'; rgb为[R,G,B]; hsb为[H,S,B]; cmyk为[C,M,Y,K]
    """
    try:
        fmt = color_format.lower()
        tgt = target.lower()
        if tgt not in ['foreground', 'background']:
            return {"success": False, "error": f"不支持的目标 '{target}'"}
            
        if fmt == 'hex':
            hex_str = str(color_value).lstrip('#')
            if len(hex_str) != 6:
                return {"success": False, "error": "HEX色值必须为6位"}
            color_setter = f"color.rgb.hexValue = '{hex_str}';"
        elif fmt == 'rgb':
            color_setter = f"""
            color.rgb.red = {float(color_value[0])};
            color.rgb.green = {float(color_value[1])};
            color.rgb.blue = {float(color_value[2])};
            """
        elif fmt == 'hsb':
            color_setter = f"""
            color.hsb.hue = {float(color_value[0])};
            color.hsb.saturation = {float(color_value[1])};
            color.hsb.brightness = {float(color_value[2])};
            """
        elif fmt == 'cmyk':
            color_setter = f"""
            color.cmyk.cyan = {float(color_value[0])};
            color.cmyk.magenta = {float(color_value[1])};
            color.cmyk.yellow = {float(color_value[2])};
            color.cmyk.black = {float(color_value[3])};
            """
        else:
            return {"success": False, "error": f"不支持的颜色格式 '{color_format}'"}

        target_prop = "foregroundColor" if tgt == "foreground" else "backgroundColor"
        
        jsx_code = f"""
        (function() {{
            var color = new SolidColor();
            {color_setter}
            app.{target_prop} = color;
            return "success";
        }})();
        """
        
        res = execute_jsx(ctx, jsx_code)
        if not res["success"]:
            raise Exception(res.get("error", "JSX 执行失败"))
            
        return {"success": True, "message": f"成功设置{'前景色' if tgt == 'foreground' else '背景色'}为 {color_value} ({color_format})"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def fill_selection(ctx: PhotoshopContext, fill_type: str) -> dict:
    """对当前选区执行填充操作。支持颜色填充、内容识别(CAF)填充等。
    
    Args:
        fill_type: 填充类型。可选值：'foreground', 'background', 'content_aware', 'pattern', 'black', 'white', 'gray'
    """
    try:
        doc = ctx.get_doc()
        
        # 安全拦截：如果没有选区且执行内容识别，必须拦截
        try:
            bounds = doc.Selection.Bounds
            is_empty_selection = False
        except Exception:
            is_empty_selection = True
            
        if is_empty_selection and fill_type == 'content_aware':
            return {"success": False, "error": "当前没有有效选区，内容识别填充已被拦截，请先创建选区。"}
            
        if fill_type == 'content_aware':
            jsx_code = """
            var idFl = charIDToTypeID( "Fl  " );
            var desc = new ActionDescriptor();
            var idUsng = charIDToTypeID( "Usng" );
            var idFlCn = charIDToTypeID( "FlCn" );
            var idCntA = charIDToTypeID( "CntA" ); // Content-Aware
            desc.putEnumerated( idUsng, idFlCn, idCntA );
            executeAction( idFl, desc, DialogModes.NO );
            """
            res = execute_jsx(ctx, jsx_code)
            if not res["success"]:
                raise Exception(res.get("error", "JSX执行失败"))
            return {"success": True, "message": "成功执行内容识别填充(Content-Aware Fill)"}
            
        type_map = {
            'foreground': 1,
            'background': 2,
            'pattern': 3,
            'black': 4,
            'white': 5,
            'gray': 6
        }
        
        if fill_type not in type_map:
            return {"success": False, "error": f"不支持的填充类型 '{fill_type}'"}
            
        doc.Selection.Fill(type_map[fill_type])
        return {"success": True, "message": f"成功使用 '{fill_type}' 填充选区"}
    except Exception as e:
        err_msg = str(e).lower()
        if "bounds" in err_msg or "empty" in err_msg or "空" in err_msg:
            return {"success": False, "error": "当前没有有效选区，请先创建选区后再执行填充操作。"}
        return {"success": False, "error": str(e)}

def color_correction(ctx: PhotoshopContext, correction_type: str, is_adjustment_layer: bool = True, params: dict = None) -> dict:
    """统一调色处理 API，支持色阶 (Levels)。
    支持通过 is_adjustment_layer 选择是新建无损调整图层还是破坏性直接修改图层。
    
    模糊修图指令应当询问用户是否使用无损调整图层。高级子通道参数请按需使用，建议以主通道调节为主。
    
    Args:
        correction_type: 'levels'
        is_adjustment_layer: 是否以调整图层的形式应用。
        params: 调色参数字典。对于 'levels':
               主通道参数：'master': {'input': [0, 255], 'output': [0, 255], 'gamma': 1.0}
               子通道参数：'red', 'green', 'blue' 结构同上。
    """
    if params is None:
        params = {}
        
    try:
        # 强制前置拦截：确保有活动文档，否则 DoJavaScript 在无文档时运行会引发 Photoshop 卡死
        doc = ctx.get_doc()
        
        if correction_type == 'levels':
            channels_to_add = []
            
            # 主通道 (Composite)
            master = params.get('master', {})
            if master or ('red' not in params and 'green' not in params and 'blue' not in params):
                channels_to_add.append(("Cmpc", master.get('input', [0, 255]), master.get('output', [0, 255]), master.get('gamma', 1.0)))
                
            # 子通道：红、绿、蓝
            red = params.get('red', {})
            if red:
                channels_to_add.append(("Rd  ", red.get('input', [0, 255]), red.get('output', [0, 255]), red.get('gamma', 1.0)))
                
            green = params.get('green', {})
            if green:
                channels_to_add.append(("Grn ", green.get('input', [0, 255]), green.get('output', [0, 255]), green.get('gamma', 1.0)))
                
            blue = params.get('blue', {})
            if blue:
                channels_to_add.append(("Bl  ", blue.get('input', [0, 255]), blue.get('output', [0, 255]), blue.get('gamma', 1.0)))
                
            add_channel_calls = []
            for ch_code, ch_in, ch_out, ch_gamma in channels_to_add:
                add_channel_calls.append(f'addChannel("{ch_code}", {ch_in[0]}, {ch_in[1]}, {ch_gamma}, {ch_out[0]}, {ch_out[1]});')
            add_channel_jsx = "\n                    ".join(add_channel_calls)
            
            jsx_code = f"""
            (function(){{
                try {{
                    var isLayer = {str(is_adjustment_layer).lower()};
                    
                    var buildLevelsDesc = function() {{
                        var desc = new ActionDescriptor();
                        var idpresetKind = stringIDToTypeID( "presetKind" );
                        var idpresetKindType = stringIDToTypeID( "presetKindType" );
                        var idpresetKindCustom = stringIDToTypeID( "presetKindCustom" );
                        desc.putEnumerated( idpresetKind, idpresetKindType, idpresetKindCustom );
                        
                        var list = new ActionList();
                        
                        var addChannel = function(channelCode, inputMin, inputMax, gamma, outMin, outMax) {{
                            var d = new ActionDescriptor();
                            var idChnl = charIDToTypeID( "Chnl" );
                            var ref = new ActionReference();
                            ref.putEnumerated( charIDToTypeID( "Chnl" ), charIDToTypeID( "Chnl" ), charIDToTypeID( channelCode ) );
                            d.putReference( idChnl, ref );
                            var idInpt = charIDToTypeID( "Inpt" );
                            var listIn = new ActionList();
                            listIn.putInteger( inputMin );
                            listIn.putInteger( inputMax );
                            d.putList( idInpt, listIn );
                            var idGmm = charIDToTypeID( "Gmm " );
                            d.putDouble( idGmm, gamma );
                            var idOtpt = charIDToTypeID( "Otpt" );
                            var listOut = new ActionList();
                            listOut.putInteger( outMin );
                            listOut.putInteger( outMax );
                            d.putList( idOtpt, listOut );
                            
                            var idLvlA = charIDToTypeID( "LvlA" );
                            list.putObject( idLvlA, d );
                        }};
                        
                        {add_channel_jsx}
                        
                        var idAdjs = charIDToTypeID( "Adjs" );
                        desc.putList( idAdjs, list );
                        return desc;
                    }};
                    
                    var desc = buildLevelsDesc();
                    
                    if (isLayer) {{
                        var idMk = charIDToTypeID( "Mk  " );
                        var d2 = new ActionDescriptor();
                        var idnull = charIDToTypeID( "null" );
                        var ref2 = new ActionReference();
                        var idAdjL = charIDToTypeID( "AdjL" );
                        ref2.putClass( idAdjL );
                        d2.putReference( idnull, ref2 );
                        var idUsng = charIDToTypeID( "Usng" );
                        var d3 = new ActionDescriptor();
                        var idType = charIDToTypeID( "Type" );
                        var idLvls = charIDToTypeID( "Lvls" );
                        d3.putObject( idType, idLvls, desc );
                        d2.putObject( idUsng, idAdjL, d3 );
                        executeAction( idMk, d2, DialogModes.NO );
                    }} else {{
                        var idLvls = charIDToTypeID( "Lvls" );
                        executeAction( idLvls, desc, DialogModes.NO );
                    }}
                    return "success";
                }} catch(e) {{
                    return "error: " + e.toString();
                }}
            }})();
            """
            res = execute_jsx(ctx, jsx_code)
            if not res["success"]:
                raise Exception(res.get("error", "Levels 调整失败"))
                
            exec_res = res.get("result", "")
            if exec_res and str(exec_res).startswith("error:"):
                return {"success": False, "error": f"Photoshop 内部调色执行失败: {exec_res}"}
                
        else:
            return {"success": False, "error": f"不支持的调色类型 '{correction_type}'。目前支持 'levels'。"}
            
        mode_str = "无损调整图层" if is_adjustment_layer else "直接像素修改"
        return {"success": True, "message": f"成功使用 {mode_str} 模式应用了 '{correction_type}'"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def stroke_selection(ctx: PhotoshopContext, width: int, location: str = 'center', color_hex: str = "#000000") -> dict:
    """对当前选区执行描边操作。
    
    Args:
        width: 描边宽度 (像素)
        location: 描边位置。'inside', 'center', 'outside'
        color_hex: 描边颜色 (HEX)，如 "#FF0000"
    """
    try:
        hex_str = color_hex.lstrip('#')
        if len(hex_str) != 6:
            return {"success": False, "error": "HEX色值必须为6位"}
            
        loc_map = {
            'inside': "StrokeLocation.INSIDE",
            'center': "StrokeLocation.CENTER",
            'outside': "StrokeLocation.OUTSIDE"
        }
        if location not in loc_map:
            return {"success": False, "error": f"不支持的描边位置 '{location}'"}
            
        stroke_loc = loc_map[location]
        
        jsx_code = f"""
        (function() {{
            var doc = app.activeDocument;
            var color = new SolidColor();
            color.rgb.hexValue = '{hex_str}';
            
            try {{
                var bounds = doc.selection.bounds;
            }} catch(e) {{
                throw new Error("NO_SELECTION");
            }}
            
            doc.selection.stroke(color, {width}, {stroke_loc});
            return "success";
        }})();
        """
        res = execute_jsx(ctx, jsx_code)
        if not res["success"]:
            err_msg = res.get("error", "").lower()
            if "no_selection" in err_msg or "bounds" in err_msg:
                return {"success": False, "error": "当前没有有效选区，无法执行描边。"}
            raise Exception(res.get("error", "描边执行失败"))
            
        return {"success": True, "message": f"成功以宽度 {width} 和颜色 {color_hex} 为选区描边"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def apply_blur_sharpen(ctx: PhotoshopContext, filter_type: str, radius: float = None, threshold: int = None, amount: float = None, clear_selection: bool = False) -> dict:
    """对当前图层（或选区）应用模糊或锐化滤镜。
    
    Args:
        filter_type: 滤镜类型。'gaussian' (高斯模糊), 'surface' (表面模糊), 'usm' (USM 锐化)
        radius: 像素半径，可选。
        threshold: 阈值 (仅用于表面模糊和 USM 锐化)，可选。
        amount: 数量百分比 (仅用于 USM 锐化)，可选。
        clear_selection: 在应用滤镜前是否强制清空当前选区以全局应用，默认 False。
    """
    try:
        doc = ctx.get_doc()
        layer = doc.ActiveLayer
        
        # 决策 D-03: 如果 clear_selection 为 True，执行 JSX 清空选区
        if clear_selection:
            clear_jsx = "app.activeDocument.selection.deselect();"
            execute_jsx(ctx, clear_jsx)
            
        if filter_type == 'gaussian':
            r = radius if radius is not None else 5.0
            layer.applyGaussianBlur(r)
            return {"success": True, "message": f"图层 '{layer.Name}' 已成功应用高斯模糊 (半径: {r} px)"}
            
        elif filter_type == 'usm':
            r = radius if radius is not None else 1.0
            amt = amount if amount is not None else 50.0
            th = threshold if threshold is not None else 4
            layer.applyUnsharpMask(amt, r, th)
            return {"success": True, "message": f"图层 '{layer.Name}' 已成功应用 USM 锐化 (数量: {amt}%, 半径: {r} px, 阈值: {th})"}
            
        elif filter_type == 'surface':
            r = radius if radius is not None else 5.0
            th = threshold if threshold is not None else 15
            
            jsx_code = f"""
            (function() {{
                var desc = new ActionDescriptor();
                desc.putUnitDouble(stringIDToTypeID("radius"), stringIDToTypeID("pixelsUnit"), {r});
                desc.putInteger(stringIDToTypeID("threshold"), {th});
                executeAction(stringIDToTypeID("surfaceBlur"), desc, DialogModes.NO);
                return "success";
            }})();
            """
            res = execute_jsx(ctx, jsx_code)
            if not res["success"]:
                raise Exception(res.get("error", "表面模糊执行失败"))
            return {"success": True, "message": f"图层 '{layer.Name}' 已成功应用表面模糊 (半径: {r} px, 阈值: {th})"}
            
        else:
            return {"success": False, "error": f"不支持的滤镜类型 '{filter_type}'"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def apply_liquify(ctx: PhotoshopContext) -> dict:
    """交互式唤起液化滤镜。
    会自动检测图层类型，如果是普通像素图层，会自动转换为智能对象，保证无损挂载智能滤镜。
    因为液化滤镜为模态工作区，调用后 Photoshop 会弹出原生液化面板并阻塞进程，用户处理完毕后点击确认即可返回。
    """
    try:
        doc = ctx.get_doc()
        layer = doc.ActiveLayer
        
        # 决策 D-05: 自动转换智能对象以实现无损智能滤镜
        is_smart_object = False
        try:
            if int(layer.Kind) == 17:
                is_smart_object = True
        except Exception:
            pass
            
        if not is_smart_object:
            logger.info(f"图层 '{layer.Name}' 不是智能对象，自动转换为智能对象以进行无损液化。")
            convert_to_smart_object(ctx)
            layer = doc.ActiveLayer
            
        jsx_code = """
        (function() {
            var idLqFy = charIDToTypeID("LqFy");
            executeAction(idLqFy, undefined, DialogModes.ALL); // 弹出液化面板
            return "success";
        })();
        """
        
        print("\n[PS AI Assistant] 已在 Photoshop 中唤起液化滤镜面板，请在 Photoshop 原生界面内调整五官或形体，并点击“确定”或“取消”以继续。")
        res = execute_jsx(ctx, jsx_code)
        if not res["success"]:
            raise Exception(res.get("error", "液化执行失败"))
            
        return {"success": True, "message": f"成功在图层 '{layer.Name}' 上应用液化滤镜"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def apply_camera_raw_preset(ctx: PhotoshopContext, preset_path: str = "", show_dialog: bool = False) -> dict:
    """对当前活动图层应用 Camera Raw 滤镜（XMP 调色预设）。
    会自动检测图层类型，如果是普通像素图层，会自动转换为智能对象，保证无损挂载智能滤镜。
    
    Args:
        preset_path: XMP 预设文件的本地绝对路径。如果为空，将自动使用内置的胶片风格预置。
        show_dialog: 是否交互式弹出 Camera Raw 界面以供用户手动微调参数，默认 False。
    """
    try:
        doc = ctx.get_doc()
        layer = doc.ActiveLayer
        
        # 决策 D-05: 自动转换智能对象以实现无损智能滤镜
        is_smart_object = False
        try:
            if int(layer.Kind) == 17:
                is_smart_object = True
        except Exception:
            pass
            
        if not is_smart_object:
            logger.info(f"图层 '{layer.Name}' 不是智能对象，自动转换为智能对象以进行无损 Camera Raw 调色。")
            convert_to_smart_object(ctx)
            layer = doc.ActiveLayer
            
        # 决策 D-09: 路径处理与 Fallback XMP 字符串设计
        xmp_content = ""
        if preset_path and os.path.exists(preset_path):
            with open(preset_path, 'r', encoding='utf-8') as f:
                xmp_content = f.read()
        else:
            # 极简通用胶片预设 Fallback
            xmp_content = """<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="Adobe XMP Core 7.0-c000 79.1340">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about="" xmlns:crs="http://ns.adobe.com/camera-raw-settings/1.0/"
   crs:Version="15.4" crs:ProcessVersion="15.4"
   crs:Exposure2012="+0.30" crs:Contrast2012="+15" crs:Highlights2012="-20" crs:Shadows2012="+20"
   crs:Clarity2012="+10" crs:Saturation="+5" crs:Sharpness="25" crs:HasSettings="True" />
 </rdf:RDF>
</x:xmpmeta>"""

        # 对 XMP 进行转义，防范 JSX 多行或单双引号报错
        xmp_escaped = xmp_content.replace('\\', '\\\\').replace('\'', '\\\'').replace('\n', '\\n').replace('\r', '')
        
        dialog_val = "true" if show_dialog else "false"
        
        jsx_code = f"""
        (function() {{
            var idACR = stringIDToTypeID("Adobe Camera Raw Filter");
            var desc = new ActionDescriptor();
            desc.putString(charIDToTypeID("Sett"), '{xmp_escaped}');
            
            var dialogMode = {dialog_val} ? DialogModes.ALL : DialogModes.NO;
            executeAction(idACR, desc, dialogMode);
            return "success";
        }})();
        """
        
        if show_dialog:
            print("\n[PS AI Assistant] 已在 Photoshop 中唤起 Camera Raw 面板，请调整参数后点击“确定”以继续。")
            
        res = execute_jsx(ctx, jsx_code)
        if not res["success"]:
            raise Exception(res.get("error", "Camera Raw 滤镜应用失败"))
            
        return {"success": True, "message": f"成功对图层 '{layer.Name}' 应用了 Camera Raw 预设滤镜"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def apply_neural_filter(ctx: PhotoshopContext, filter_type: str, parameters: dict = None) -> dict:
    """触发神经网络滤镜 (Neural Filters)。
    
    Args:
        filter_type: 滤镜功能类型，例如 'skin_smoothing' (平滑皮肤), 'smart_portrait' (智能肖像)。
        parameters: 可选的微调参数字典，例如 {"skin_smoothness": 50, "blemish_reduction": 50}。
    """
    try:
        doc = ctx.get_doc()
        layer = doc.ActiveLayer
        
        # 决策 D-10: 神经网络滤镜环境防崩溃与降级机制
        jsx_code = """
        (function() {
            try {
                var idCmd = stringIDToTypeID("neuralFiltersCmd");
                executeAction(idCmd, undefined, DialogModes.ALL);
                return "success";
            } catch(e) {
                return "ERROR: " + e.message;
            }
        })();
        """
        
        print(f"\n[PS AI Assistant] 正在触发神经网络滤镜 [{filter_type}]，请在 Photoshop 原生面板中处理，完成后脚本将继续运行。")
        res = execute_jsx(ctx, jsx_code)
        if not res["success"]:
            err_msg = res.get("error", "").lower()
            return {
                "success": False, 
                "error": f"神经网络滤镜启动失败 ({err_msg})。可能是由于本地未激活、未联网或未下载该模型组件。推荐您降级使用传统的商业磨皮功能。"
            }
            
        if res.get("result") and "ERROR" in str(res["result"]):
            return {
                "success": False,
                "error": f"神经网络滤镜在 PS 侧执行报错 ({res['result']})。推荐您降级使用传统的商业磨皮功能。"
            }
            
        return {"success": True, "message": f"成功对图层 '{layer.Name}' 触发神经网络滤镜 {filter_type}"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def apply_commercial_retouch(ctx: PhotoshopContext, opacity: float = 100.0) -> dict:
    """对当前活动图层执行经典的自适应商业磨皮动作流（高分离频率无损皮肤质感修饰）。
    
    Args:
        opacity: 磨皮图层的不透明度 (0.0 - 100.0)，默认 100.0。
    """
    try:
        doc = ctx.get_doc()
        layer = doc.ActiveLayer
        
        # 决策 D-02: 自适应分辨率像素半径换算
        width = float(doc.Width)
        scale_factor = width / 1920.0
        
        r_hp = max(1.0, round(3.0 * scale_factor, 1))
        r_sb = max(1.0, round(3.0 * scale_factor, 1))
        sb_threshold = 10
        
        logger.info(f"DPI自适应磨皮: 画布宽度为 {width} px，自适应高反差半径缩放为: {r_hp} px，表面模糊半径缩放为: {r_sb} px")
        
        # 决策 D-04: 静默自动新建备份图层以实现无损磨皮
        jsx_code = f"""
        (function() {{
            var doc = app.activeDocument;
            var activeLyr = doc.activeLayer;
            
            // 1. 复制当前图层并重命名
            var copyLyr = activeLyr.duplicate();
            copyLyr.name = activeLyr.name + "_磨皮";
            doc.activeLayer = copyLyr;
            
            // 确保图层是普通像素图层，以便应用破坏性滤镜和反相
            try {{
                if (copyLyr.kind !== LayerKind.NORMAL) {{
                    copyLyr.rasterize(RasterizeType.ENTIRELAYER);
                }}
            }} catch(e) {{}}
            
            // 2. 将图层混合模式设为线性光 (Linear Light)
            copyLyr.blendMode = BlendMode.LINEARLIGHT;
            copyLyr.opacity = {opacity};
            
            // 3. 执行反相 (优先使用 DOM 方法，失败则 fallback 到 ActionManager)
            try {{
                copyLyr.invert();
            }} catch(e) {{
                executeAction(charIDToTypeID("Invt"), undefined, DialogModes.NO);
            }}
            
            // 4. 应用高反差保留 (High Pass)
            var hpDesc = new ActionDescriptor();
            hpDesc.putUnitDouble(stringIDToTypeID("radius"), stringIDToTypeID("pixelsUnit"), {r_hp});
            executeAction(stringIDToTypeID("highPass"), hpDesc, DialogModes.NO);
            
            // 5. 应用表面模糊 (Surface Blur)
            var sbDesc = new ActionDescriptor();
            sbDesc.putUnitDouble(stringIDToTypeID("radius"), stringIDToTypeID("pixelsUnit"), {r_sb});
            sbDesc.putInteger(stringIDToTypeID("threshold"), {sb_threshold});
            executeAction(stringIDToTypeID("surfaceBlur"), sbDesc, DialogModes.NO);
            
            // 6. 添加黑色全隐蒙版 (Hide All)
            var idMk = charIDToTypeID("Mk  ");
            var maskDesc = new ActionDescriptor();
            maskDesc.putClass(charIDToTypeID("Nw  "), charIDToTypeID("Chnl"));
            var ref = new ActionReference();
            ref.putEnumerated(charIDToTypeID("Chnl"), charIDToTypeID("Chnl"), charIDToTypeID("Msk "));
            maskDesc.putReference(charIDToTypeID("At  "), ref);
            maskDesc.putEnumerated(charIDToTypeID("Usng"), charIDToTypeID("UsrM"), charIDToTypeID("HdAl"));
            executeAction(idMk, maskDesc, DialogModes.NO);
            
            return "success";
        }})();
        """
        
        res = execute_jsx(ctx, jsx_code)
        if not res["success"]:
            raise Exception(res.get("error", "商业磨皮动作流执行失败"))
            
        return {"success": True, "message": f"图层 '{layer.Name}' 已成功应用自适应商业磨皮动作流，生成了包含黑色蒙版的无损磨皮层 '{layer.Name}_磨皮'"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def apply_generative_fill(ctx: PhotoshopContext, prompt: str = "") -> dict:
    """对当前活动选区执行 AI 生成式填充 (Generative Fill)。
    
    Args:
        prompt: 生成式填充所需的英文描述词（提示词）。
    """
    try:
        doc = ctx.get_doc()
        layer = doc.ActiveLayer
        
        # 威胁模型：过滤一些显而易见的极端敏感词
        sensitive_keywords = {"nude", "naked", "porn", "violence", "blood", "gore", "kill"}
        clean_prompt = prompt.strip()
        lower_prompt = clean_prompt.lower()
        for kw in sensitive_keywords:
            if kw in lower_prompt:
                return {"success": False, "error": f"由于提示词中包含敏感或限制级词汇 '{kw}'，生成式填充已被前置拦截保护。"}
                
        prompt_escaped = clean_prompt.replace('\\', '\\\\').replace('\'', '\\\'').replace('\n', '\\n').replace('\r', '')
        
        # 决策 D-06: 选区强拦截防御
        jsx_code = f"""
        (function() {{
            var doc = app.activeDocument;
            
            var hasSelection = false;
            try {{
                var bounds = doc.selection.bounds;
                hasSelection = true;
            }} catch(e) {{}}
            
            if (!hasSelection) {{
                return "ERROR: NO_SELECTION";
            }}
            
            var idsyntheticFill = stringIDToTypeID("syntheticFill");
            var desc = new ActionDescriptor();
            var ref = new ActionReference();
            ref.putEnumerated(stringIDToTypeID("document"), stringIDToTypeID("ordinal"), stringIDToTypeID("targetEnum"));
            desc.putReference(stringIDToTypeID("null"), ref);
            
            if ('{prompt_escaped}') {{
                desc.putString(stringIDToTypeID("text"), '{prompt_escaped}');
            }}
            
            executeAction(idsyntheticFill, desc, DialogModes.NO);
            return "success";
        }})();
        """
        
        res = execute_jsx(ctx, jsx_code)
        if not res["success"]:
            raise Exception(res.get("error", "生成式填充执行失败"))
            
        result_str = str(res.get("result", ""))
        if "ERROR: NO_SELECTION" in result_str:
            return {
                "success": False, 
                "error": "生成式填充已被拦截：当前没有有效活动选区。请先用套索、魔棒等工具创建目标选区，或者让我利用 AI '选择主体'选中区域后重试。"
            }
            
        # 决策 D-08: 提示变体选择
        return {
            "success": True, 
            "message": f"成功在图层 '{layer.Name}' 选区内应用生成式填充。已为您触发生成填充，请在 Photoshop 右侧的‘属性’面板中选择切换我为您生成的 3 个变体。"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def play_action(ctx: PhotoshopContext, action_name: str, action_set_name: str) -> dict:
    """执行 Photoshop 中的录制动作 (Action)。
    
    为避免带有阻塞性交互的动作（如调色弹窗）导致假死，此方法允许原生对话框弹出供用户干预。
    
    Args:
        action_name: 要执行的动作名称。
        action_set_name: 动作所在的动作集名称。
    """
    try:
        jsx_code = f"""
        (function() {{
            var idPlay = charIDToTypeID( "Ply " );
            var desc = new ActionDescriptor();
            var idnull = charIDToTypeID( "null" );
            var ref = new ActionReference();
            var idActn = charIDToTypeID( "Actn" );
            ref.putName( idActn, "{action_name}" );
            var idASet = charIDToTypeID( "ASet" );
            ref.putName( idASet, "{action_set_name}" );
            desc.putReference( idnull, ref );
            // 决策 D-02: 不强制静默，允许原生对话框
            executeAction( idPlay, desc, DialogModes.ALL );
            return "success";
        }})();
        """
        res = execute_jsx(ctx, jsx_code)
        if not res["success"]:
            raise Exception(res.get("error", "Action 执行失败"))
        return {"success": True, "message": f"动作 '{action_set_name} -> {action_name}' 已成功执行"}
    except Exception as e:
        return {"success": False, "error": f"调用动作失败 (请检查动作名称是否大小写完全匹配，或图层结构是否符合动作要求): {str(e)}"}

def execute_local_jsx(ctx: PhotoshopContext, script_path: str, user_confirmed: bool = False) -> dict:
    """加载并执行本地绝对或相对路径的 JSX 扩展脚本。
    
    Args:
        script_path: 要执行的 JSX 脚本文件路径。
        user_confirmed: 是否经过用户明确授权。安全机制要求不在白名单内的脚本必须由大模型前置询问用户，并在获得允许后传入 True。
    """
    try:
        script_path = os.path.abspath(script_path)
        whitelist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "resources", "scripts"))
        
        # 决策 D-01: 路径权限策略
        if not script_path.startswith(whitelist_dir):
            if not user_confirmed:
                return {
                    "success": False, 
                    "error": f"安全拦截: 执行外部脚本存在风险。请先向用户询问是否允许执行此路径的脚本 ({script_path})。如果用户同意，请带上 user_confirmed=True 重新调用。"
                }
                
        if not os.path.exists(script_path):
            return {"success": False, "error": f"脚本文件不存在: {script_path}"}
            
        with open(script_path, "r", encoding="utf-8") as f:
            jsx_code = f.read()
            
        res = execute_jsx(ctx, jsx_code)
        if not res["success"]:
            raise Exception(res.get("error", "本地 JSX 脚本执行失败"))
            
        return {"success": True, "message": f"成功执行本地脚本: {os.path.basename(script_path)}", "result": res.get("result", "")}
    except Exception as e:
        return {"success": False, "error": str(e)}

def export_for_web(ctx: PhotoshopContext, format: str = "PNG-24", export_path: str = "") -> dict:
    """自动将当前画布切片或全图以 Web 适用格式导出。
    
    Args:
        format: 导出格式，目前支持 "PNG-24", "JPEG"。默认为 "PNG-24" 以保持最佳质量。
        export_path: 可选的导出绝对路径。若未提供，默认输出至系统桌面。
    """
    try:
        doc = ctx.get_doc()
        
        # 防呆：文档尺寸检查
        if float(doc.Width) > 8192 or float(doc.Height) > 8192:
            return {"success": False, "error": "SaveForWeb 不支持边长超过 8192px 的图像，请先使用 resize_image 或 resize_canvas 缩小图像。"}
            
        if not export_path:
            desktop = os.path.expanduser("~/Desktop")
            timestamp = int(time.time())
            export_path = os.path.join(desktop, f"ps_ai_web_export_{timestamp}.png" if "PNG" in format else f"ps_ai_web_export_{timestamp}.jpg")
            
        export_path = os.path.abspath(export_path)
        
        # 转换斜杠以兼容 JSX
        jsx_path = export_path.replace("\\", "/")
        
        is_png = "PNG" in format.upper()
        
        # 使用 JSX 导出规避部分 COM 层级缺陷
        jsx_code = f"""
        (function() {{
            var doc = app.activeDocument;
            var file = new File("{jsx_path}");
            var options = new ExportOptionsSaveForWeb();
            
            if ({str(is_png).lower()}) {{
                options.format = SaveDocumentType.PNG;
                options.PNG8 = false;
            }} else {{
                options.format = SaveDocumentType.JPEG;
                options.quality = 80;
            }}
            
            doc.exportDocument(file, ExportType.SAVEFORWEB, options);
            return "success";
        }})();
        """
        
        res = execute_jsx(ctx, jsx_code)
        if not res["success"]:
            raise Exception(res.get("error", "导出脚本执行失败"))
            
        return {"success": True, "message": f"Web 切片成功导出至桌面 (或指定路径): {export_path}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
