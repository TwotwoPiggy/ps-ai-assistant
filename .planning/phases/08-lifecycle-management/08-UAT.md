---
status: testing
phase: 08-lifecycle-management
source: [08-01-SUMMARY.md]
started: 2026-06-14T22:54:00+08:00
updated: 2026-06-14T22:54:00+08:00
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

number: 2
name: Updater Script
expected: |
  Running `python updater.py` successfully updates the codebase (via Git or ZIP fallback) without overwriting `backend/store/` or `.venv`, and restarts the application via `start_silent.vbs`.
awaiting: user response

## Tests

### 1. Installation Script
expected: Running `install.bat` prompts for admin privileges if needed, checks/installs Python and Node.js, sets up a virtual environment, builds dependencies, and creates a desktop shortcut pointing to `start_silent.vbs`.
result: issue
reported: "能指定路径吗"
severity: major

### 2. Updater Script
expected: Running `python updater.py` successfully updates the codebase (via Git or ZIP fallback) without overwriting `backend/store/` or `.venv`, and restarts the application via `start_silent.vbs`.
result: [pending]

### 3. Uninstallation Script
expected: Running `uninstall.bat` prompts for admin privileges, safely removes the desktop shortcut, kills the application's processes (via `.pid`), completely deletes the application folder, and cleans up after itself.
result: [pending]

## Summary

total: 3
passed: 0
issues: 1
pending: 2
skipped: 0

## Gaps

- truth: "Running `install.bat` prompts for admin privileges if needed, checks/installs Python and Node.js, sets up a virtual environment, builds dependencies, and creates a desktop shortcut pointing to `start_silent.vbs`."
  status: failed
  reason: "User reported: 能指定路径吗"
  severity: major
  test: 1
  artifacts: []
  missing: []

