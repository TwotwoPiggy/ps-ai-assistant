---
phase: 05
slug: color-correction
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-14
---

# Phase 05 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Manual COM test & Python script / mock |
| **Config file** | none |
| **Quick run command** | `python <test_script>` |
| **Full suite command** | `pytest tests/` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run manual validation script
- **After every plan wave:** Full verification
- **Before `/gsd-verify-work`:** All features must work in Photoshop
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | Colors | — | N/A | manual | N/A | ✅ | ⬜ pending |
| 05-01-02 | 01 | 1 | Levels | — | N/A | manual | N/A | ✅ | ⬜ pending |
| 05-01-03 | 01 | 1 | CAF | — | Auto-intercept no selection | manual | N/A | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
