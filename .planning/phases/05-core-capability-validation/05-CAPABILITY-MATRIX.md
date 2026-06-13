# Phase 5: 核心能力评估矩阵 (Core Capability Validation Matrix)

根据对 Photoshop UXP DOM API v2 和 batchPlay 双通道引擎的对比测试（结合 `tests/capability_results.json`），我们得出了以下 11 个核心工具在各架构下的支持度、表现与推荐落地方案，以指导 Phase 6 及其后的架构大迁徙。

## 能力对比矩阵

| 工具名 | COM 方案状态 | UXP DOM 测试状态 | batchPlay 测试状态 | 推荐落地方案 | 备注与限制 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **get_layer_tree** | 稳定支持 | ✅ 成功，遍历速度快且类型友好 | ❌ 无此封装，需复杂 Action 组合 | **DOM API** | 获取树结构属于高频操作，DOM 性能更优且更易于维护。 |
| **get_canvas_snapshot**| 稳定支持 | ✅ 成功，通过 Storage API 导出 JPG | ❌ 不直接支持导出图像流 | **DOM API** | DOM 结合 UXP Storage API `doc.saveAs.jpeg` 是唯一可靠手段，但需注意沙盒文件系统限制。 |
| **create_layer** | 稳定支持 | ✅ 成功 | ✅ 成功 | **DOM API** | DOM 更加语义化，支持直观的参数如 `name`, `opacity` 等。 |
| **delete_layer** | 稳定支持 | ✅ 成功 | ✅ 成功 | **DOM API** | DOM 接口简洁 `layer.delete()`，完全足够。 |
| **rename_layer** | 稳定支持 | ✅ 成功 | ✅ 成功 | **DOM API** | 直接赋值 `layer.name = ...` 即可，性能无差异。 |
| **set_layer_visibility** | 稳定支持 | ✅ 成功 | ✅ 成功 | **DOM API** | 同上，DOM 修改属性更直观。 |
| **reorder_layer** | 稳定支持 | ✅ 成功，支持 ElementPlacement | ❌ 回退或实现繁琐 | **DOM API** | DOM 中有原生的 `move(target, placement)` 方法，逻辑清晰。 |
| **adjust_brightness_contrast**| 稳定支持 | ✅ 成功 | ✅ 成功，与 DOM 一样稳定 | **batchPlay (可选)** | 复杂的调色/滤镜操作使用 batchPlay 通常能提供更多的可调节参数，而 DOM 有时包装不完整。混合使用。 |
| **crop_canvas** | 稳定支持 | ✅ 成功 | ✅ 成功 | **DOM API** | DOM `crop()` 方法已足够稳定支持基本裁切。 |
| **resize_canvas** | 稳定支持 | ✅ 成功 | ✅ 成功 | **DOM API** | DOM 配合 `AnchorPosition` 完全可覆盖。 |
| **flip_image** | 稳定支持 | ✅ 成功 | ✅ 成功 | **DOM API** | `flipCanvas` 简单可靠。 |

**总结：混合策略（Mixed Strategy）的落地建议**
绝大多数的基础 CRUD 操作和数据获取推荐优先使用 **UXP DOM API v2**，因为其具有完整的类型提示、代码易读性高、无需拼装冗长的 JSON Descriptor。
当涉及到 Photoshop 高级滤镜、复杂的 Action 触发，或者是 DOM API 尚未封装的新特性时，才采用 **batchPlay** 进行增补。目前的架构中，使用 `_use_batchplay` 标志动态调度的机制已得到验证。

---

## 验证结论：PS 事件反向推送 (CAP-03)

在本次 PoC 验证中，我们成功在 `socket.ts` 前端注册了全局的 `addNotificationListener`，并且在 FastAPI 服务端 (`server.py`) 中接收到了实时的推送信息。

**测试结论：**
1. **可靠性**：监听 `select`, `open`, `close` 等核心事件极其可靠。一旦用户在 Photoshop 界面中手工点击图层或者开闭文档，UXP 插件均能在毫秒级捕获事件并包装为 descriptor。
2. **通信畅通**：通过现存的 `Socket.IO` 连接使用 `socket.emit("ps_event", payload)`，可以做到极低延迟推送给 Python 后端，证明了此长连接架构足以支撑双向指令/状态同步需求。
3. **后续计划 (Phase 6+)**：后续在真实对接大模型场景中，后端可实时更新上下文状态，实现“当用户切图层时，AI 自动知道当前所在图层”的智能化体验。需要注意频繁选择图层时的防抖 (Debounce) 处理，避免事件风暴塞满 Socket 队列。
