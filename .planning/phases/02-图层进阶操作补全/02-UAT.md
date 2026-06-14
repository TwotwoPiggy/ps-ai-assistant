---
status: passed
phase: 02-图层进阶操作补全
source: [SUMMARY.md]
started: 2026-06-13T10:55:00Z
updated: 2026-06-13T10:55:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

number: 7
name: 测试栅格化与智能对象转化 (栅格化/转智能对象)
expected: |
  选择文字图层转为智能对象，再次执行操作看是否报错；之后执行栅格化操作，再重复执行看是否报错。验证幂等处理机制可防止重复报错且转化结果正确。
awaiting: none

## Tests

### 1. 测试图层编组 (group_layers)
expected: 使用 AI 助手调用 group_layers，指定图层名列表和一个新组名，验证 Photoshop 中是否新建了该组并将指定图层全部移入其中。
result: pass

### 2. 测试图层不透明度与填充调整 (set_layer_opacity_and_fill)
expected: 对某个图层或图层组调用设置透明度和填充。验证参数被正确应用。若针对图层组设置填充度，命令应当静默成功而不触发报错。
result: pass

### 3. 测试图层混合模式切换 (set_layer_blend_mode)
expected: 将某图层的混合模式设为正片叠底或叠加等，验证 Photoshop 界面上图层面板的混合模式相应发生改变。
result: pass

### 4. 测试移动图层 (move_layer)
expected: 指定 dx/dy（或绝对坐标）移动指定图层，验证图层在画布上发生对应的物理位移。
result: pass

### 5. 测试合并操作 (merge_layers)
expected: 选取多个图层并调用向下合并、合并可见或拼合图像命令，验证图层面板中的图层结构被正确压平。
result: pass

### 6. 测试复制图层 (duplicate_layer)
expected: 对一个图层进行复制操作并给与新名称，验证图层面板产生一个同内容的副本并正确命名。
result: pass

### 7. 测试栅格化与智能对象转化 (栅格化/转智能对象)
expected: 选择文字图层转为智能对象，再次执行操作看是否报错；之后执行栅格化操作，再重复执行看是否报错。验证幂等处理机制可防止重复报错且转化结果正确。
result: pass

## Summary

total: 7
passed: 7
issues: 0
pending: 0
skipped: 0

## Gaps

[none yet]
