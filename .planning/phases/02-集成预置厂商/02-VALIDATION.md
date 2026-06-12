---
phase: 2
slug: 集成预置厂商
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-12
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | python (unittest/mock/asyncio standard scripts) |
| **Config file** | none |
| **Quick run command** | `python scratch/test_phase2_integration.py` |
| **Full suite command** | `python scratch/test_phase2_integration.py` |
| **Estimated runtime** | ~1 second |

---

## Sampling Rate

- **After every task commit:** Run `python scratch/test_phase2_integration.py`
- **After every plan wave:** Run full suite command
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 1 second

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-02-01 | 02 | 1 | PROV-01 | — | Stream response & reasoning extraction for DeepSeek | unit | `python scratch/test_phase2_integration.py` | ✅ | ✅ green |
| 02-02-02 | 02 | 1 | PROV-02 | — | Stream response & compatibility for Qwen | unit | `python scratch/test_phase2_integration.py` | ✅ | ✅ green |
| 02-02-03 | 02 | 1 | PROV-03 | — | Stream response & compatibility for MiMo | unit | `python scratch/test_phase2_integration.py` | ✅ | ✅ green |
| 02-02-04 | 02 | 1 | PROV-04 | — | Custom OpenAI Compat support | unit | `python scratch/test_phase2_integration.py` | ✅ | ✅ green |
| 02-02-05 | 02 | 1 | PROV-05 | T-02-PROV | Image filtering & fallback on visual absence | integration | `python scratch/test_phase2_integration.py` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements.

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-06-12
