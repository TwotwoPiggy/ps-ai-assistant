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
