# Phase 6 Discussion Log

## Area: API 清单的覆盖范围 (API Scope)
**Options Presented:**
- (推荐) 仅梳理大模型常用操作（图层、选区、图像处理、导出等），保持精简高效。
- 全面梳理所有 UXP 暴露的功能（包括滤镜、动画、3D等高级功能），提供完整的字典。

**User Selection:**
- Custom: 我想先梳理所有uxp功能, 然后选择常用的操作保持精简高效

**Notes:**
- 先宽后窄策略：提供全景供人类和未来扩展使用，提供精简版供当前 AI Context 使用，避免 Token 浪费。

---

## Area: API 清单的输出格式 (API Format)
**Options Presented:**
- (推荐) 两者兼顾：生成用于人类阅读的 Markdown 全景字典，并导出一份精简后的 JSON Schema 专门供大模型加载为 Tools。
- 仅作为 Markdown 文档留存，后续大模型使用时再单独提取。
- 直接输出完整的 JSON 结构，机器友好即可。

**User Selection:**
- (推荐) 两者兼顾：生成用于人类阅读的 Markdown 全景字典，并导出一份精简后的 JSON Schema 专门供大模型加载为 Tools。

**Notes:**
- 输出两个产物文件。

---

## Area: 开发规范的落地形式 (Guidelines Location)
**Options Presented:**
- (推荐) 将其写入项目根目录的 .planning/GEMINI.md 中，作为大模型在此项目中写代码时的全局上下文和铁律。
- 建立一个独立的独立规范文档（例如 docs/UXP-GUIDELINES.md），作为人类开发者和模型的查阅手册。
- 把防坑指南和规范以块注释的形式分散写在核心文件（如 modalQueue.ts, uxpTools.ts）的顶部。

**User Selection:**
- Custom: 结合1和2

**Notes:**
- 输出独立的 `UXP-GUIDELINES.md` 以供系统查阅，同时将最关键的铁律同步到 `.planning/GEMINI.md` 作为全局强制系统提示。
