# Phase 3: AI 认知升级与集成测试 - UAT

## Objective
验证大模型在拥有 15 个独立工具接口时，能够正确理解用户的语义并在复杂的连贯任务中组合调用相应的工具，避免混淆。

## Setup
1. 启动 `python main.py`
2. 打开客户端 Web UI
3. 在 Photoshop 中新建一个带有少量图层的测试文档。

## Current Test
number: 4
name: 测试复合操作连招 (composite_operation)
expected: |
  大模型能够连续进行多步调用（创建图层 -> 获取图层树 -> 转智能对象），并且能够妥善处理 Photoshop 返回的异常。
awaiting: none

## Tests

### 1. 提示词加载验证 (system_prompt_load)
expected: 后端正常启动时不报错。在前端发出指令时，能在后台终端日志中看到 Provider 被成功调用，并且未发生由于 system_instruction 未找到而导致的崩溃。
result: [pass]

### 2. 测试场景辨析：调整画布大小 (resize_canvas)
expected: 发送指令“请把当前画布向右侧扩展 200 个像素”，大模型应成功调用 `resize_canvas`，且图像内容本身没有被拉伸（仅工作区变大）。
result: [pass]

### 3. 测试场景辨析：缩放图像 (resize_image)
expected: 发送指令“请把整个图片的尺寸缩小一半”，大模型应成功调用 `resize_image`，画面整体等比例缩小。
result: [pass]

### 4. 测试复合操作连招 (composite_operation)
expected: 发送连贯指令（如“新建测试图层并转换为智能对象”），大模型应先后连贯调用 `create_layer`、`get_layer_tree` 和 `convert_to_smart_object`，并能妥善处理异常情况。
result: [pass]

## Summary

total: 4
passed: 4
issues: 0
pending: 0
skipped: 0

## Gaps
None.
