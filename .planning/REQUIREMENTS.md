# Milestone v1.1 Requirements

## Active Requirements

### 基础设施 (Infrastructure)
- [ ] **INFRA-01**: 搭建 UXP 插件骨架与 manifest.json 声明
- [ ] **INFRA-02**: 实现 UXP 与 FastAPI 间的 WebSocket (Socket.IO) 双向通信
- [ ] **INFRA-03**: 实现 UXP 端统一的 `executeAsModal` 操作队列

### 能力探索与操作清单 (Capabilities)
- [ ] **CAP-01**: 梳理标准 DOM API 边界与 `batchPlay` 调用规范
- [ ] **CAP-02**: 测试图层 CRUD、画布调整等核心操作的替代方案
- [ ] **CAP-03**: 测试由 UXP 主动推送 PS 事件（如切换图层）的机制
- [ ] **CAP-04**: 输出全量的 UXP 支持的 API 操作清单与评估，用于后续决定扩展哪些新 Function

### 开发规范 (Guidelines)
- [ ] **GUIDE-01**: 制定 UXP 开发陷阱的防范规范 (沙盒限制、性能卡顿等)

## Future Requirements
- 扩展更多的 Photoshop 工具方法 (Functions) — 依赖于本里程碑的 CAP-04 研究结果
- 全量替换现有的 pywin32 COM 后端

## Out of Scope
- 在本研究里程碑内直接将现有的 pywin32 COM 调用全部删除（需等研究和测试完成、基础骨架和PoC验证后再在下一里程碑进行替换）

## Traceability

- **INFRA-01**: Phase 4
- **INFRA-02**: Phase 4
- **INFRA-03**: Phase 4
- **CAP-01**: Phase 5
- **CAP-02**: Phase 5
- **CAP-03**: Phase 5
- **CAP-04**: Phase 6
- **GUIDE-01**: Phase 6
