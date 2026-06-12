import os
import sys
import time
import base64
import tempfile
import win32com.client
from pathlib import Path
from google import genai
from google.genai import types

class PhotoshopAgent:
    def __init__(self, api_key: str, model: str = 'gemini-2.5-flash'):
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.conversations: dict[str, list[types.Content]] = {}  # sid -> list of Content
        self.ps_app = None
        self.layer_id_map = {}
        self.next_id_val = 1
        
    def clear_conversations(self, sid: str):
        """清空当前会话的历史聊天记录"""
        if sid in self.conversations:
            self.conversations[sid] = []
            
    def _get_doc(self):
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except Exception:
            pass
        ps_app = win32com.client.Dispatch("Photoshop.Application")
        if ps_app.Documents.Count == 0:
            raise Exception("当前 Photoshop 中没有打开的文档，请先在 Photoshop 中打开或创建一个文档。")
        return ps_app.ActiveDocument

    def _resolve_layer(self, doc, layer_identify: str):
        # Resolve layer ID like "layer_1" to the actual layer object using index path
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
    # Gemini Tools Definitions
    # ==========================================
    
    def get_layer_tree(self) -> dict:
        """获取当前 Photoshop 文档的完整图层树结构，包括图层名称、ID、类型、可见性等。
        当你需要修改、删除、重命名图层或了解文档图层结构时，必须首先调用此函数获取最新的图层 ID。
        """
        try:
            doc = self._get_doc()
            self.layer_id_map = {}
            self.next_id_val = 1
            
            def traverse(container, path_prefix):
                nodes = []
                for i in range(1, container.Count + 1):
                    layer = container.Item(i)
                    current_path = path_prefix + [i]
                    
                    layer_id = f"layer_{self.next_id_val}"
                    self.next_id_val += 1
                    self.layer_id_map[layer_id] = current_path
                    
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

    def get_canvas_snapshot(self) -> dict:
        """获取当前 Photoshop 画布的最新截图快照。
        当需要理解画面视觉内容（例如调整亮度和对比度、剪裁、或者根据视觉指示进行操作）时调用此函数。
        """
        temp_file = os.path.join(tempfile.gettempdir(), f"ps_snap_{int(time.time())}.jpg")
        try:
            doc = self._get_doc()
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

    def create_layer(self, name: str, opacity: float = 100.0, above: str = None) -> dict:
        """在 Photoshop 中创建一个新普通图层。
        
        Args:
            name: 新图层名称
            opacity: 不透明度百分比 (0 到 100)，默认 100
            above: 可选。目标图层标识符（如 'layer_1'）。如果指定，新图层将被移到该图层上方；不指定则放在最顶层。
        """
        try:
            doc = self._get_doc()
            new_layer = doc.ArtLayers.Add()
            new_layer.Name = name
            try:
                new_layer.Opacity = opacity
            except Exception:
                pass
            
            if above:
                target = self._resolve_layer(doc, above)
                new_layer.Move(target, 3)  # psPlaceBefore = 3
                
            return {"success": True, "message": f"成功创建图层 '{name}'"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_layer(self, layer_identify: str) -> dict:
        """删除 Photoshop 中的指定图层。
        
        Args:
            layer_identify: 目标图层标识符 (例如 'layer_1')
        """
        try:
            doc = self._get_doc()
            layer = self._resolve_layer(doc, layer_identify)
            layer_name = layer.Name
            layer.Delete()
            return {"success": True, "message": f"成功删除图层 '{layer_name}'"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def rename_layer(self, layer_identify: str, new_name: str) -> dict:
        """重命名 Photoshop 中的指定图层。
        
        Args:
            layer_identify: 目标图层标识符 (例如 'layer_1')
            new_name: 新的图层名称
        """
        try:
            doc = self._get_doc()
            layer = self._resolve_layer(doc, layer_identify)
            old_name = layer.Name
            layer.Name = new_name
            return {"success": True, "message": f"已将图层 '{old_name}' 重命名为 '{new_name}'"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def set_layer_visibility(self, layer_identify: str, visible: bool) -> dict:
        """设置 Photoshop 中指定图层的可见性 (显示或隐藏)。
        
        Args:
            layer_identify: 目标图层标识符 (例如 'layer_1')
            visible: true 表示显示图层，false 表示隐藏图层
        """
        try:
            doc = self._get_doc()
            layer = self._resolve_layer(doc, layer_identify)
            layer.Visible = visible
            state = "显示" if visible else "隐藏"
            return {"success": True, "message": f"已将图层 '{layer.Name}' 设置为{state}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def reorder_layer(self, layer_identify: str, target_identify: str, placement: str) -> dict:
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
            doc = self._get_doc()
            layer = self._resolve_layer(doc, layer_identify)
            target = self._resolve_layer(doc, target_identify)
            
            layer_name = layer.Name
            target_name = target.Name
            
            layer.Move(target, placement_map[placement])
            return {"success": True, "message": f"已将图层 '{layer_name}' 移至 '{target_name}' 的 {placement} 位置"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def adjust_brightness_contrast(self, brightness: int, contrast: int, layer_identify: str = None) -> dict:
        """调整图层中图像的亮度和对比度。
        注意：必须在包含像素图像数据的图层上进行调整。如果是新创建的空白图层或图层组，操作将抛出错误。
        
        Args:
            brightness: 亮度变化量 (-150 到 150)
            contrast: 对比度变化量 (-50 到 100)
            layer_identify: 可选。指定图层标识符。如果不提供，将应用于当前激活/选中的图层。
        """
        try:
            doc = self._get_doc()
            if layer_identify:
                layer = self._resolve_layer(doc, layer_identify)
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

    def crop_canvas(self, top: float, left: float, bottom: float, right: float) -> dict:
        """裁剪画布至指定的像素边界。
        
        Args:
            top: 裁剪区域上边界的像素坐标
            left: 裁剪区域左边界的像素坐标
            bottom: 裁剪区域下边界的像素坐标
            right: 裁剪区域右边界的像素坐标
        """
        try:
            doc = self._get_doc()
            doc.Crop([left, top, right, bottom])
            return {"success": True, "message": f"画布成功裁剪至区域: left={left}, top={top}, right={right}, bottom={bottom}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def resize_canvas(self, width: int, height: int, anchor: str = 'middleCenter') -> dict:
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
            doc = self._get_doc()
            doc.ResizeCanvas(width, height, anchor_map[anchor])
            return {"success": True, "message": f"画布尺寸已成功调整为 {width}x{height}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def flip_image(self, direction: str) -> dict:
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
            doc = self._get_doc()
            doc.FlipCanvas(direction_map[direction])
            return {"success": True, "message": f"画布已成功进行了 {direction} 翻转"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================================
    # Main Agent Process Loop
    # ==========================================
    
    async def handle_message(self, sid: str, message: str, status_callback=None) -> str:
        """处理来自前端 Chat UI 的用户自然语言消息，返回 AI 回复"""
        # Ensure we have conversation history
        if sid not in self.conversations:
            self.conversations[sid] = []
            
        # Clean history to prevent legacy large base64 strings from causing token limit errors
        cleaned_history = []
        for content in self.conversations[sid]:
            cleaned_parts = []
            for part in content.parts:
                # Check if it's a function response containing base64
                if part.function_response:
                    try:
                        resp = part.function_response.response
                        if isinstance(resp, dict) and "imageBase64" in resp:
                            # Clean it
                            resp_copy = resp.copy()
                            del resp_copy["imageBase64"]
                            resp_copy["message"] = "（历史快照数据已清理以节省 Token）"
                            part.function_response.response = resp_copy
                    except Exception:
                        pass
                cleaned_parts.append(part)
            content.parts = cleaned_parts
            cleaned_history.append(content)
        self.conversations[sid] = cleaned_history

        # Add user message
        self.conversations[sid].append(types.Content(
            role="user",
            parts=[types.Part.from_text(text=message)]
        ))
        
        # Tools list for Gemini
        tools = [
            self.get_layer_tree,
            self.get_canvas_snapshot,
            self.create_layer,
            self.delete_layer,
            self.rename_layer,
            self.set_layer_visibility,
            self.reorder_layer,
            self.adjust_brightness_contrast,
            self.crop_canvas,
            self.resize_canvas,
            self.flip_image
        ]
        
        system_instruction = (
            "你是一个功能强大的 Photoshop AI 助手，能够直接通过执行 Python COM 操作来修改当前的 Photoshop 文档。\n"
            "你可以使用一系列定义好的工具（Tools）来完成用户的指令，包含图层基础操作和画布基本编辑。\n"
            "【操作准则】:\n"
            "1. 务必始终使用【简体中文】与用户进行回复和交流。\n"
            "2. 当用户请求任何与图层相关的操作时，你没有默认图层的标识符。你【必须】首先调用 `get_layer_tree` 获取当前图层树以取得目标的 `layer_identify` (如 layer_1)，之后再利用它进行具体操作。不要猜测或使用用户提到的名字作为 ID 传入其他操作参数中。\n"
            "3. 如果用户发出的指令非常依赖视觉理解（如'把画面变亮点'、'裁剪掉左上角'等），你应该优先调用 `get_canvas_snapshot` 获取当前画面，结合视觉特征后再做出调用工具或回复的判断。\n"
            "4. 一次回复里，你可以决定调用一个或多个工具。多步操作应当按照合理顺序连贯调用，直到完成指令。\n"
            "5. 当所有的工具调用执行完毕并得到结果后，你应该将执行情况及最终画布状态汇总成简明且易读的简体中文回复告诉用户。\n"
            "6. 如果某个操作返回了错误（例如无法调整空白图层的亮度），请在最终回复中诚实告知用户，并提供指导或建议。"
        )
        
        config = types.GenerateContentConfig(
            tools=tools,
            system_instruction=system_instruction
        )
        
        max_turns = 10
        turn = 0
        
        while turn < max_turns:
            turn += 1
            if status_callback:
                await status_callback("thinking", f"AI 正在思考中... (第 {turn} 轮)")
                
            # Send message to Gemini with retry logic for 429 (Resource Exhausted) and 503 (Unavailable) errors
            from google.genai import errors
            import asyncio
            
            max_retries = 3
            response = None
            
            # [DEBUG] Dump contents to disk to analyze size
            try:
                import tempfile
                import os
                debug_path = os.path.join(tempfile.gettempdir(), f"ps_ai_debug_{turn}.txt")
                with open(debug_path, "w", encoding="utf-8") as f:
                    f.write(str(self.conversations[sid]))
                print(f"[DEBUG] Wrote conversation state to {debug_path}")
            except Exception as e:
                print(f"[DEBUG] Failed to write debug: {e}")
                
            for attempt in range(max_retries):
                try:
                    response = self.client.models.generate_content(
                        model=self.model,
                        contents=self.conversations[sid],
                        config=config
                    )
                    break
                except errors.APIError as e:
                    # Check if error is rate limit (429) or service unavailable (503)
                    code = getattr(e, "code", None) or getattr(e, "status_code", None)
                    if code in (429, 503) and attempt < max_retries - 1:
                        sleep_time = (attempt * 15) + 20  # Try 20s then 35s
                        if status_callback:
                            await status_callback("thinking", f"接口繁忙或受限 (错误 {code})，将在 {sleep_time} 秒后重试...")
                        await asyncio.sleep(sleep_time)
                    else:
                        raise e
            
            # Record AI's response (with potential function calls) in history
            model_content = response.candidates[0].content
            self.conversations[sid].append(model_content)
            
            # Check if Gemini wants to call functions
            if not response.function_calls:
                # No function calls, this is the final answer
                final_text = response.text or ""
                if status_callback:
                    await status_callback("done", "完成回复")
                return final_text
                
            # Execute function calls
            resp_parts = []
            for function_call in response.function_calls:
                name = function_call.name
                args = function_call.args
                
                if status_callback:
                    await status_callback("executing", f"正在执行 PS 操作: {name}...")
                    
                # Call tool
                tool_func = getattr(self, name, None)
                if not tool_func:
                    result = {"success": False, "error": f"找不到工具函数 '{name}'"}
                else:
                    # Execute synchronous COM operations
                    try:
                        # Extract kwargs from args mapping
                        kwargs = {}
                        if args:
                            # Convert to Python dict if necessary
                            if hasattr(args, "items"):
                                kwargs = {k: v for k, v in args.items()}
                            else:
                                kwargs = dict(args)
                        
                        # Call method
                        result = tool_func(**kwargs)
                    except Exception as e:
                        result = {"success": False, "error": str(e)}
                        
                # 剔除超大的 Base64 字符串，避免将其作为文本发送给模型消耗数十万 token
                func_resp_data = result.copy() if isinstance(result, dict) else result
                if isinstance(func_resp_data, dict) and "imageBase64" in func_resp_data:
                    del func_resp_data["imageBase64"]
                    func_resp_data["message"] = "截图数据已作为独立的图像实体(Part)附在当前消息中提供给您进行视觉分析。"
                        
                # Create function response part
                resp_parts.append(types.Part.from_function_response(
                    name=name,
                    response=func_resp_data
                ))
                
                # Special Multimodal injection: if get_canvas_snapshot was run, 
                # inject the actual image data as a Part in the same message response 
                # so the model can visually see the snapshot in subsequent turns.
                if name == "get_canvas_snapshot" and result.get("success") and "imageBase64" in result:
                    try:
                        img_bytes = base64.b64decode(result["imageBase64"])
                        image_part = types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")
                        resp_parts.append(image_part)
                    except Exception as e:
                        print("Failed to decode snapshot image bytes:", str(e))
                        
            # Record tool responses as the user role content
            self.conversations[sid].append(types.Content(
                role="user",
                parts=resp_parts
            ))
            
        if status_callback:
            await status_callback("done", "AI 回复超时")
        return "抱歉，由于操作步骤过多，AI 回复已超时。"
