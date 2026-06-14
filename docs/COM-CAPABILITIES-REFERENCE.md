# Photoshop COM 控制能力全景字典

本字典整理了通过 Python COM 接口（结合基础 DOM API 与高级 ExtendScript 注入）所能控制的所有 Photoshop 核心功能。通过这套机制，我们的 AI 助手可以达到与人类设计师完全对等的软件操作权限。

---

## 1. 📂 文档与视图管理 (Document & View)

控制画布的整体属性，是所有修图操作的基石。

| 功能名称 | 技术实现途径 | 功能描述 |
| :--- | :--- | :--- |
| **创建/打开/保存** | 基础 DOM | 新建白板文档，从本地路径打开图片，另存为不同格式（PSD/JPG/PNG）。 |
| **画布裁切与调整** | 基础 DOM | 修改图像大小（Resize Image）、修改画布大小（Resize Canvas）、裁剪（Crop）、显示全部（Reveal All）。 |
| **色彩模式转换** | 基础 DOM | 在 RGB、CMYK、灰度（Grayscale）之间无损切换。 |
| **历史记录控制** | 基础 DOM | 撤销（Undo）、重做（Redo）、跳转到指定历史记录状态（History States）。 |
| **视图缩放** | ExtendScript | 控制画面的缩放比例（放大、缩小、100% 视图、适应屏幕）。 |

---

## 2. 📑 图层与组操作 (Layer & Group)

这是 AI 助手目前已经部分掌握，且未来可以进一步强化的模块。

| 功能名称 | 技术实现途径 | 功能描述 |
| :--- | :--- | :--- |
| **CRUD 操作** | 基础 DOM | 新建、复制、删除图层；新建图层组（Group）；图层重命名。 |
| **属性调整** | 基础 DOM | 调整不透明度（Opacity）、填充透明度（Fill）、修改混合模式（如正片叠底、滤色、叠加）。 |
| **层级变换** | 基础 DOM | 移动图层顺序（上移、下移、置顶、置底）、移动图层在画布上的 X/Y 像素坐标。 |
| **栅格化与合并** | 基础 DOM / ExtendScript | 栅格化文字或智能对象、向下合并图层（Merge Down）、合并可见图层（Merge Visible）、拼合图像（Flatten）。 |
| **智能对象操作** | ExtendScript | 转换为智能对象（Convert to Smart Object）、编辑智能对象内容、替换内容。 |

---

## 3. 🎯 选区与蒙版 (Selection & Mask)

高级抠图和局部调整的核心。

| 功能名称 | 技术实现途径 | 功能描述 |
| :--- | :--- | :--- |
| **基础选区** | 基础 DOM | 矩形框选、椭圆框选、全选、反选（Invert）、取消选择。 |
| **选区修饰** | 基础 DOM / ExtendScript | 羽化选区（Feather）、扩展/收缩选区、平滑、边界。 |
| **AI 智能选择** | ExtendScript | **选择主体（Select Subject）**、**移除背景（Remove Background）**、色彩范围选择。 |
| **蒙版操作** | ExtendScript | 为图层添加图层蒙版（Add Layer Mask）、应用/删除蒙版、启用/禁用蒙版。 |
| **通道控制** | 基础 DOM / ExtendScript | 获取 Alpha 通道、载入通道作为选区、将选区存储为通道。 |

---

## 4. 🎨 专业调色与光影 (Color Correction)

用于对画面整体或局部进行色彩和明暗风格的重塑。

| 功能名称 | 技术实现途径 | 功能描述 |
| :--- | :--- | :--- |
| **基础曝光调色** | ExtendScript | 直接应用：亮度/对比度、色阶（Levels）、曲线（Curves）、曝光度。 |
| **基础色彩调色** | ExtendScript | 直接应用：色相/饱和度、色彩平衡、自然饱和度、黑白、照片滤镜。 |
| **调整图层应用** | ExtendScript | **(推荐)** 创建独立的“调整图层”（无损调色），如新建一个曲线调整图层，避免破坏原图。 |
| **前景色/背景色** | 基础 DOM | 设置工具栏当前使用的前景色和背景色（HEX/RGB 取值）。 |
| **填充与描边** | 基础 DOM | 对当前选区进行颜色填充（Fill）、内容识别填充（Content-Aware Fill）、描边（Stroke）。 |

---

## 5. 💄 高级滤镜与人像美化 (Filters & Retouching)

这是 P图 最具价值的核心领域，也是 AI 后续最能拉开差距的突破口。

| 功能名称 | 技术实现途径 | 功能描述 |
| :--- | :--- | :--- |
| **常见模糊与锐化** | ExtendScript | 高斯模糊（Gaussian Blur）、动感模糊、表面模糊、USM 锐化、智能锐化。 |
| **人像液化修饰** | ExtendScript | 唤起并应用“液化”滤镜参数（Liquify），用于瘦脸、大眼、形体调整。 |
| **Camera Raw 滤镜** | ExtendScript | 调用 Camera Raw 引擎进行一键专业后期参数套用。 |
| **AI 神经元滤镜** | ExtendScript | 触发 Neural Filters（如“智能肖像”、“皮肤平滑”、“超级缩放”、“着色”）。 |
| **经典商业磨皮** | ExtendScript复合 | 自动化多步执行：高反差保留（High Pass）+ 表面模糊 + 计算蒙版，实现专业级保留质感的自动磨皮。 |
| **AI 生成式填充** | ExtendScript | 触发最新的 Generative Fill，让 AI 根据选区和提示词直接在画布上无中生有。 |

---

## 6. 🛠️ 自动化与动作集成 (Automation & Actions)

如果有些操作代码过于复杂，可以直接复用您 Photoshop 现有的资产。

| 功能名称 | 技术实现途径 | 功能描述 |
| :--- | :--- | :--- |
| **触发动作 (Actions)** | ExtendScript | 直接调用您在 Photoshop“动作”面板中录制好的任意动作集合（如：执行“我的美化集”下的“一键日系调色”）。 |
| **触发脚本 (JSX)** | ExtendScript | 加载并运行本地硬盘上的任意 .jsx 扩展脚本文件。 |
| **导出切片** | 基础 DOM | 将设计图自动切片并执行“导出为 Web 所用格式”。 |

---

### 💡 技术实现原理解析
* **“基础 DOM”** 标记的功能：在 Python 中可以通过非常简单的对象属性直接调用（例如 `layer.Opacity = 50`）。
* **“ExtendScript”** 标记的功能：需要我们在 Python 端拼接一段相当于 ActionManager (底层录制机制) 的特征码，然后通过 `ps.DoJavaScript(代码)` 打入 Photoshop 执行。虽然实现稍费功夫，但**潜力无限**。
