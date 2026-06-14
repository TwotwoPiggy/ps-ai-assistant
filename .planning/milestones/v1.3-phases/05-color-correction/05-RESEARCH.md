# Phase 05 Research: 专业调色与光影实现

**Date:** 2026-06-14
**Status:** Completed

## 1. Domain Exploration (Photoshop Color API & COM Object)

### 1.1 Colors & SolidColor Object
在 Photoshop COM 接口中，前景色和背景色可以通过 `app.ForegroundColor` 和 `app.BackgroundColor` 属性进行直接赋值。
赋值时需要传递一个 `SolidColor` COM 对象。
```python
color = win32com.client.Dispatch("Photoshop.SolidColor")
color.RGB.Red = 255
color.RGB.Green = 0
color.RGB.Blue = 0
app.ForegroundColor = color
```
**多格式解析策略**: 由于要求 API 统一接受 Hex/RGB/HSB/CMYK，在 `set_foreground_background_color` 函数中，我们需要实现一个解析器将前端传来的各类色值安全转换为 `SolidColor` 的设置，如针对 `HSB` 就设置 `color.HSB.Hue`, `color.HSB.Saturation`, `color.HSB.Brightness`。

### 1.2 ActionManager 与调色
Photoshop 区分“破坏性调整（直接修改像素）”和“调整图层（无损效果）”：
- **破坏性调整**: 调用特定的工具指令，例如 `Lvls` (色阶), `ClrB` (色彩平衡), `HStr` (色相/饱和度)。它会直接操作当前被选中的目标图层。
- **调整图层**: 调用 `Mk  ` (Make) 指令，目标类设为 `AdjL` (Adjustment Layer)，并在其 `Usng` 属性内嵌入调色字典（如 `Lvls` 描述）。

### 1.3 内容识别填充 (Content-Aware Fill)
在 ActionManager 中，内容识别填充通过 `Fl  ` (Fill) 执行，关键参数为：
- `Usng` -> Enum: `FlCn` -> Value: `CntA` (Content-Aware)

**核心防御逻辑（无选区拦截）**:
由于 CAF 操作在没有选区时无法合理进行。在执行前，必须探测选区是否存在。
可以通过 `app.ActiveDocument.Selection.Bounds` 探测。如果该操作触发 COM `com_error`，则说明当前文档不存在激活选区。此时必须按 CONTEXT.md 规定中断并抛出特定提示，拦截填充。

### 1.4 色阶(Levels)等高级参数的组装
对于色阶等进阶工具，支持按通道调整。
通道标识：
- `Chnl` -> Enum `Chnl` -> `Rd  ` (红), `Grn ` (绿), `Bl  ` (蓝) 或者组合通道（主通道 `Cmpc` / Composite）。
我们需要提供给大模型一个类似 `master_levels`, `red_levels`, `green_levels`, `blue_levels` 的可选入参。每个通道的常用参数包括：
- `Inpt` (Input levels): 数组，如 [0, 255]
- `Otpt` (Output levels): 数组，如 [0, 255]
- `Gmm ` (Gamma/Midtone): float，如 1.0

## 2. API Design Draft

为支持 Phase 05 CONTEXT.md 的契约，提议以下几项核心 Tools:
1. `set_color(target="foreground", hex="#...|rgb(...)")` - 解析色值并注入 COM。
2. `fill_selection(fill_type="color|content_aware|pattern", color=None)` - 进行颜色或 CAF 填充，内置空选区探测器。
3. `color_correction(type="levels|color_balance", is_adjustment_layer=True, params={...})` - 一揽子调色入口，可无损可破坏。

## 3. Potential Gotchas & Blockers
1. **SolidColor.CMYK vs SolidColor.RGB**: Photoshop 环境本身的色彩空间（比如文档是 RGB）如果强行注入 CMYK SolidColor 可能产生轻微色偏。需以文档模式匹配最佳。
2. **调整图层生成后焦点改变**: 新建调整层后，活动图层变为该调整层自身自带的蒙版，若需继续操作下面图层，需要焦点恢复逻辑（视需处理）。

## 4. Conclusion
后端的 Python 实现非常明确，核心挑战是如何将多模态能力和交互式反问在系统交互层面有效拉起。后端的首要任务是严格实现参数解析和安全拦截机制。
