---
status: testing
phase: 01-文档管理增强与架构扩充
source: [01-SUMMARY.md]
started: 2026-06-13T10:20:00Z
updated: 2026-06-13T10:20:00Z
---

## Current Test

number: 1
name: Get App Interface
expected: |
  在 Photoshop 未打开任何文档时，可以在 Python 代码中成功获取 Photoshop.Application 对象（通过 PhotoshopContext.get_app()）。
awaiting: user response

## Tests

### 1. Get App Interface
expected: 在 Photoshop 未打开任何文档时，可以在 Python 代码中成功获取 Photoshop.Application 对象（通过 PhotoshopContext.get_app()）。
result: [pending]

### 2. Execute JSX Script
expected: 在 Python 端调用 execute_jsx 工具函数向 Photoshop 注入 JSX ExtendScript，能够成功通过 DoJavaScript 在 Photoshop 实例中执行，并返回结果。
result: [pending]

### 3. Create Canvas and Open Document
expected: 在 Photoshop 没有打开任何文档的状态下，调用 create_document 能够无异常地创建新空白画布；调用 open_and_place 能够无异常地在画布中置入指定的本地图片。
result: [pending]

### 4. Save Document with Desktop Fallback
expected: 对一个全新未存盘的空白文档调用 save_document（不传入路径参数），文档能够自动以当前时间戳命名（形式为 ps_ai_export_{timestamp}.psd）另存至用户的 Windows 系统桌面上。
result: [pending]

### 5. Resize Image
expected: 调用 resize_image 工具函数，能够控制 Photoshop 直接调整当前活动画布图像的物理像素宽高。
result: [pending]

### 6. Color Mode Conversion
expected: 调用 change_color_mode 转换色彩模式（如 RGB、CMYK 或 Grayscale），模式能够顺利转换，且在这个过程中 Photoshop 不会弹出任何阻塞性的警告或合并提示弹框。
result: [pending]

### 7. Undo Operations
expected: 调用 history_control 工具，能够向 Photoshop 注入 undo 指令，从而撤销上一步操作。
result: [pending]

### 8. Zoom Canvas View
expected: 调用 zoom_view 工具，传入 'fit' 或 '100%' 指令，能够自动缩放 Photoshop 画布的显示比例，分别使其适合屏幕大小或达到实际像素（100%）。
result: [pending]

### 9. Register OpenAI Tools Schema
expected: 在 Python 代码中能够正常从 registry.get_openai_schemas() 导出包含上述 8 项新工具（如 execute_jsx、zoom_view 等）在内的完整 OpenAI tools 描述描述数据。
result: [pending]

## Summary

total: 9
passed: 0
issues: 0
pending: 9
skipped: 0

## Gaps

[none yet]
