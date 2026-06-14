---
phase: 06
slug: filters-retouching
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-14
---

# Phase 06 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | none |
| **Quick run command** | `pytest tests/test_phase06_filters.py` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_phase06_filters.py`
- **After every plan wave:** Run `pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 0 | Wave 0 | — | N/A | setup | N/A | ✅ W0 | ✅ green |
| 06-01-02 | 01 | 1 | FIL-01 | — | N/A | integration | `pytest tests/test_phase06_filters.py -k test_gaussian_blur` | ✅ W0 | ✅ green |
| 06-01-03 | 01 | 1 | FIL-01 | — | N/A | integration | `pytest tests/test_phase06_filters.py -k test_usm_sharpen` | ✅ W0 | ✅ green |
| 06-01-04 | 01 | 1 | FIL-01 | — | N/A | integration | `pytest tests/test_phase06_filters.py -k test_surface_blur` | ✅ W0 | ✅ green |
| 06-01-05 | 01 | 1 | FIL-02 | — | N/A | integration | `pytest tests/test_phase06_filters.py -k test_liquify_smart_object` | ✅ W0 | ✅ green |
| 06-01-06 | 01 | 2 | FIL-03 | — | N/A | integration | `pytest tests/test_phase06_filters.py -k test_camera_raw_preset` | ✅ W0 | ✅ green |
| 06-01-07 | 01 | 2 | AI-01 | — | N/A | integration | `pytest tests/test_phase06_filters.py -k test_neural_filters_graceful_fallback` | ✅ W0 | ✅ green |
| 06-01-08 | 01 | 2 | AI-02 | — | N/A | integration | `pytest tests/test_phase06_filters.py -k test_commercial_retouch` | ✅ W0 | ✅ green |
| 06-01-09 | 01 | 2 | AI-03 | — | N/A | integration | `pytest tests/test_phase06_filters.py -k test_generative_fill` | ✅ W0 | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_phase06_filters.py` — pytest stubs for all 6 requirements (FIL-01 to AI-03)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 神经网络滤镜/液化的交互式弹出 | AI-01, FIL-02 | 涉及 Photoshop 的原生模态 UI 交互，Headless pytest 无法直接点击确认 | 调用接口触发，手动在 Photoshop 弹窗中点击取消或确定，确认 Python 后端无报错且能正确挂起及恢复。 |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-06-14
