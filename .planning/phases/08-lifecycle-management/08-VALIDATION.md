---
phase: 08
slug: lifecycle-management
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-14
---

# Phase 08 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest / Node.js test |
| **Config file** | none — Wave 0 installs |
| **Quick run command** | `pytest tests/test_lifecycle.py` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_lifecycle.py`
- **After every plan wave:** Run `pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 08-01-01 | 01 | 1 | INST-01 | — | N/A | unit | `pytest tests/test_installer.py` | ❌ W0 | ⬜ pending |
| 08-01-02 | 01 | 1 | UPD-01 | — | N/A | unit | `pytest tests/test_updater.py` | ❌ W0 | ⬜ pending |
| 08-01-03 | 01 | 1 | UNINST-01 | — | N/A | unit | `pytest tests/test_uninstall.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_installer.py` — stubs for INST-01
- [ ] `tests/test_updater.py` — stubs for UPD-01
- [ ] `tests/test_uninstall.py` — stubs for UNINST-01

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 一键安装流程 | INST-01 | 涉及实际操作系统状态变更和快捷方式创建 | 在干净环境中双击安装脚本并检查桌面 |
| 彻底卸载 | UNINST-01 | 需要干预系统环境变量、文件锁等 | 运行卸载脚本，检查项目目录和快捷方式是否被彻底移除 |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
