import inspect
import re
from typing import get_type_hints

def python_method_to_openai_schema(func) -> dict:
    """将 Python 函数签名和 docstring 自动转换为 OpenAI 兼容的 tools JSON Schema"""
    name = func.__name__
    doc = func.__doc__ or ""
    
    description = ""
    param_descriptions = {}
    
    # 将 doc 按行拆分
    doc_lines = [line.strip() for line in doc.split('\n')]
    
    # 寻找 Args: 或者是 Parameters: 的起始位置
    args_start = -1
    for i, line in enumerate(doc_lines):
        if re.match(r'^(Args|Parameters):', line, re.IGNORECASE):
            args_start = i
            break
            
    if args_start != -1:
        # Args 之前的内容是描述
        description = "\n".join(doc_lines[:args_start]).strip()
        current_param = None
        for line in doc_lines[args_start + 1:]:
            # 匹配 "name: 描述" 或者 "name (str): 描述"
            match = re.match(r'^([\w_]+)\s*(?:\([^)]+\))?\s*:\s*(.*)', line)
            if match:
                current_param = match.group(1)
                param_descriptions[current_param] = match.group(2).strip()
            elif current_param and line:
                # 拼接多行描述
                param_descriptions[current_param] += " " + line.strip()
    else:
        description = doc.strip()
        
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)
    
    properties = {}
    required = []
    
    # 类型映射
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object"
    }
    
    for param_name, param in sig.parameters.items():
        # 排除 context / ctx 参数，这个由系统自动注入，不对模型公开
        if param_name in ('ctx', 'context'):
            continue
            
        param_type = type_hints.get(param_name, param.annotation)
        
        # 处理 typing.Optional / typing.Union
        if hasattr(param_type, "__origin__"):
            origin = param_type.__origin__
            # 判断是否为 Union
            import typing
            # python 3.8+ compatibility
            is_union = origin is typing.Union or (hasattr(typing, "_UnionGenericAlias") and isinstance(param_type, typing._UnionGenericAlias))
            if is_union:
                args = param_type.__args__
                # 获取非 None 的真实类型
                non_none_args = [arg for arg in args if arg is not type(None)]
                if non_none_args:
                    param_type = non_none_args[0]
                    
        json_type = type_map.get(param_type, "string")
        
        param_desc = param_descriptions.get(param_name, "")
        
        properties[param_name] = {
            "type": json_type,
            "description": param_desc
        }
        
        if json_type == "array":
            properties[param_name]["items"] = {"type": "string"}
        
        # 是否必填
        if param.default is inspect.Parameter.empty:
            required.append(param_name)
            
    schema = {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    }
    
    return schema
