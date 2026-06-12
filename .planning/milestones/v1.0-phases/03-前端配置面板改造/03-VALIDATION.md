---
phase: 3
slug: 前端配置面板改造
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-12
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | vite + typescript (compiler check) |
| **Config file** | frontend/tsconfig.json |
| **Quick run command** | `npm run build` |
| **Full suite command** | `npm run build` |
| **Estimated runtime** | ~1.5 seconds |

---

## Sampling Rate

- **After every task commit:** Run compilation build check
- **After every plan wave:** Run full production build
- **Before `/gsd-verify-work`:** Build must be green
- **Max feedback latency:** 2 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 03-03-01 | 03 | 1 | CONF-03 | — | Dynamic Provider dropdown selectors in UI | static | `npm run build` | ✅ | ✅ green |
| 03-03-02 | 03 | 1 | CONF-04 | — | Auto-fill lock fields on predefined provider select | static | `npm run build` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Web UI state transitions and form interaction | CONF-03, CONF-04 | Involves browser interactions, CSS visual alignments, and user click actions | 1. Open the configuration panel.<br>2. Select various providers (e.g. MiMo, custom, Gemini).<br>3. Verify that fields like Base URL hide/show according to selected provider rules. |
| Stream ThinkingBox expansion animation | CONF-03 | Requires live Socket.IO events for R1 reasoning and visual micro-animations | 1. Run backend server and trigger R1 model.<br>2. Confirm the folding Accordion thinking block expands during reasoning streaming and can be toggled manually. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-06-12
