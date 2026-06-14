from typing import Callable, Dict, List
from .schema import python_method_to_openai_schema
from . import ps_tools

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._schemas: Dict[str, dict] = {}

    def register(self, func: Callable):
        name = func.__name__
        self._tools[name] = func
        self._schemas[name] = python_method_to_openai_schema(func)
        return func

    def get_tool(self, name: str) -> Callable:
        return self._tools.get(name)

    def get_all_tools(self) -> List[Callable]:
        return list(self._tools.values())

    def get_openai_schemas(self) -> List[dict]:
        """返回所有注册工具的 OpenAI tools 格式描述"""
        return list(self._schemas.values())

    def execute_tool(self, name: str, args: dict, ctx: ps_tools.PhotoshopContext) -> dict:
        """执行指定工具并返回结果字典"""
        tool_func = self.get_tool(name)
        if not tool_func:
            return {"success": False, "error": f"找不到工具函数 '{name}'"}
        
        # 准备参数，解析传入的参数，注入 ctx
        kwargs = {}
        if args:
            if hasattr(args, "items"):
                kwargs = {k: v for k, v in args.items()}
            else:
                kwargs = dict(args)
        
        try:
            # 所有的 Photoshop 工具函数的第一个参数都是 ctx
            return tool_func(ctx, **kwargs)
        except Exception as e:
            return {"success": False, "error": str(e)}

# 初始化全局注册表
registry = ToolRegistry()

# 注册所有 11 个 Photoshop 工具
registry.register(ps_tools.get_layer_tree)
registry.register(ps_tools.get_canvas_snapshot)
registry.register(ps_tools.create_layer)
registry.register(ps_tools.delete_layer)
registry.register(ps_tools.rename_layer)
registry.register(ps_tools.set_layer_visibility)
registry.register(ps_tools.reorder_layer)
registry.register(ps_tools.adjust_brightness_contrast)
registry.register(ps_tools.crop_canvas)
registry.register(ps_tools.resize_canvas)
registry.register(ps_tools.flip_image)

# 注册文档管理与底层 JSX 执行相关工具
registry.register(ps_tools.execute_jsx)
registry.register(ps_tools.create_document)
registry.register(ps_tools.open_and_place)
registry.register(ps_tools.save_document)
registry.register(ps_tools.resize_image)
registry.register(ps_tools.change_color_mode)
registry.register(ps_tools.history_control)
registry.register(ps_tools.zoom_view)

# 注册图层进阶操作 8 项核心 API
registry.register(ps_tools.group_layers)
registry.register(ps_tools.set_layer_opacity_and_fill)
registry.register(ps_tools.set_layer_blend_mode)
registry.register(ps_tools.move_layer)
registry.register(ps_tools.merge_layers)
registry.register(ps_tools.duplicate_layer)
registry.register(ps_tools.rasterize_layer)
registry.register(ps_tools.convert_to_smart_object)

# 注册选区与蒙版控制工具
registry.register(ps_tools.basic_selection)
registry.register(ps_tools.modify_selection)
registry.register(ps_tools.smart_selection)
registry.register(ps_tools.mask_control)
registry.register(ps_tools.channel_control)

# 注册专业调色与光影实现工具
registry.register(ps_tools.set_color)
registry.register(ps_tools.fill_selection)
registry.register(ps_tools.color_correction)
registry.register(ps_tools.stroke_selection)

# 注册高级滤镜与美化工具
registry.register(ps_tools.apply_blur_sharpen)
registry.register(ps_tools.apply_liquify)
registry.register(ps_tools.apply_camera_raw_preset)
registry.register(ps_tools.apply_neural_filter)
registry.register(ps_tools.apply_commercial_retouch)
registry.register(ps_tools.apply_generative_fill)

# 注册自动化与动作集成工具
registry.register(ps_tools.play_action)
registry.register(ps_tools.execute_local_jsx)
registry.register(ps_tools.export_for_web)
