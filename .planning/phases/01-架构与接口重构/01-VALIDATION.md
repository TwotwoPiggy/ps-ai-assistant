---
phase: 1
slug: 架构与接口重构
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-12
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | python (unittest/asyncio standard scripts) |
| **Config file** | none |
| **Quick run command** | `python scratch/test_tools.py` |
| **Full suite command** | `python scratch/test_providers.py && python scratch/test_tools.py && python scratch/test_integration.py` |
| **Estimated runtime** | ~2 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python scratch/test_tools.py`
- **After every plan wave:** Run full suite command
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 2 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | ARCH-01 | — | Photoshop tools decoupled into functions | unit | `python scratch/test_tools.py` | ✅ | ✅ green |
| 01-01-02 | 01 | 1 | ARCH-02 | — | Dynamically generate schemas | unit | `python scratch/test_tools.py` | ✅ | ✅ green |
| 01-01-03 | 01 | 1 | ARCH-03 | — | BaseProvider interface methods | unit | `python scratch/test_providers.py` | ✅ | ✅ green |
| 01-01-04 | 01 | 1 | ARCH-04 | — | GeminiProvider adapter implementation | unit | `python scratch/test_providers.py` | ✅ | ✅ green |
| 01-01-05 | 01 | 1 | ARCH-05 | — | OpenAICompatProvider adapter implementation | unit | `python scratch/test_providers.py` | ✅ | ✅ green |
| 01-01-06 | 01 | 1 | CONF-01 | — | Config architecture multi-provider storage | integration | `python scratch/test_integration.py` | ✅ | ✅ green |
| 01-01-07 | 01 | 1 | CONF-02 | T-01-CONF | Safe API Key masking and merging | integration | `python scratch/test_integration.py` | ✅ | ✅ green |

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
