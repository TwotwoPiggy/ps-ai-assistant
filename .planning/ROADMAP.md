# Roadmap: Milestone v1.1

## Phase 4: 搭建 UXP 基础环境与通信 (Infrastructure Setup)
**Objective**: 构建 UXP 插件的底层基础脚手架，实现与后端的双向通信，并建立统一的模态操作队列以防止界面阻塞。

**Requirements**: 
- **INFRA-01**: 搭建 UXP 插件骨架与 manifest.json 声明
- **INFRA-02**: 实现 UXP 与 FastAPI 间的 WebSocket (Socket.IO) 双向通信
- **INFRA-03**: 实现 UXP 端统一的 `executeAsModal` 操作队列

**Success Criteria**:
- UXP 插件工程基础骨架创建完毕，且能在 Adobe UDT 中顺利加载并运行。
- FastAPI 后端与 UXP 客户端的 WebSocket (Socket.IO) 能够成功握手并进行双向消息收发。
- `executeAsModal` 操作队列可正常运行，验证能稳定接收外部请求执行文档修改，且不导致 PS 崩溃或界面长时间卡顿。

## Phase 5: 验证核心功能与事件机制 (Core Capability Validation)
**Objective**: 验证现有关键操作 (如图层和画布调整) 在 UXP 架构中的可行替代方案，并测试事件反向推送机制。

**Requirements**:
- **CAP-01**: 梳理标准 DOM API 边界与 `batchPlay` 调用规范
- **CAP-02**: 测试图层 CRUD、画布调整等核心操作的替代方案
- **CAP-03**: 测试由 UXP 主动推送 PS 事件（如切换图层）的机制

**Success Criteria**:
- DOM API 与 `batchPlay` 的调用方式被清晰梳理并经实际代码测试跑通。
- 成功完成一组图层 CRUD（增删改查）与画布修改操作在 UXP 环境下的等效替换方案的概念验证 (PoC)。
- 当用户在 Photoshop 界面中主动执行操作（如图层切换）时，UXP 能够捕捉相关事件并通过 WebSocket 实时推送到服务端日志中。

## Phase 6: 整理全量 API 清单与输出开发规范 (Research Documentation & Guidelines)
**Objective**: 汇总整个里程碑的探索成果，输出全面细致的 UXP 接口能力清单以及防陷阱开发指南，为后续里程碑的全面重构奠定基础。

**Requirements**:
- **CAP-04**: 输出全量的 UXP 支持的 API 操作清单与评估，用于后续决定扩展哪些新 Function
- **GUIDE-01**: 制定 UXP 开发陷阱的防范规范 (沙盒限制、性能卡顿等)

**Success Criteria**:
- 一份完整且结构化的 UXP API 能力评估文档落地，清晰界定可通过 DOM API 或 batchPlay 实现的功能及边界。
- 总结并归档 UXP 开发避坑指南（包括但不限于沙盒隔离限制、避免 UI 线程大图传输拥堵等性能保障策略）。
- 所有研究产出文档通过最终审查并入库，为下个版本全面替换 `pywin32` 扫清认知障碍。
