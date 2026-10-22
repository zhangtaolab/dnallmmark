---
phase: 18-docs-authoring
plan: "03"
subsystem: docs-tui
tags: [docs, tui, multi-gpu, i18n, version-surfaces]
requires:
  - "16-UI-SPEC.md shipped-surface vocabulary (Phase 16 landed)"
  - "18-01 multi-gpu.md dispatch-first runbook (cross-link target)"
provides:
  - "TUI-DEMO section 11 — the multi-GPU walkthrough section (no-GIF honest variant, queued re-record note)"
  - "TUI-GUIDE multi-GPU section describing shipped Phase-16 reality (contradiction removed)"
  - "About-screen milestone row reading delivered v1.3 scope (both languages)"
affects:
  - docs/TUI-DEMO.md
  - docs/TUI-GUIDE.md
  - tui/strings.py
tech-stack:
  added: []
  patterns:
    - "TUI-DEMO five-part anatomy, no-GIF honest variant (golden-reference table + queued note)"
    - "verified-against-source doc discipline (every key/behavior checked in tui/ before writing)"
key-files:
  created: []
  modified:
    - docs/TUI-DEMO.md
    - docs/TUI-GUIDE.md
    - tui/strings.py
decisions:
  - "Shipped-source facts supersede the 16-UI-SPEC's pre-review values: stale grace 3600s cell-scale (WR-02), GPUs default 0..workers-1 (WR-03), distinct malformed-invariant marker (WR-04) — docs describe the shipped reality the plan's threat model T-18-03 requires"
  - "Four same-file TUI-GUIDE contradiction fixes applied beyond lines 191-204 (Rule 1): the rewritten section would otherwise self-contradict the stale EHC-3 paragraph and run_sweep.py argv claim beside it"
  - "TUI-GUIDE heading renamed to 'Multi-GPU launch and monitoring' (old anchor had no inbound links — verified before rename)"
metrics:
  duration: 13m
  completed: 2026-10-22
actuals:
  tokens: 4500    # chars/4 over the realized three-file diff (18,011 chars)
  tasks: 3
  commits: 3      # MEASURED: git rev-list --count b4fee82..bdd0033
commits: 3
plan_head_before: b4fee82a4bd4b8f198e8aa9f31737811307f85e9
plan_head_after: bdd0033e3ef2b820c8da4a8c8d5ee98ec0fda8ff
status: complete
requirements: [DOCS-03, DOCS-04]
---

# Phase 18 Plan 03: TUI Multi-GPU Docs + Version Surfaces Summary

TUI-DEMO gained a source-verified multi-GPU section 11 in the precedent five-part anatomy (no-GIF honest variant with the queued re-record note), TUI-GUIDE's contradicting multi-GPU section was rewritten to the shipped Phase-16 reality, and the about-screen milestone row now reads the delivered v1.3 scope in both languages with all version surfaces verified at 1.3.0.

## What Was Built

### Task 1 — TUI-DEMO section 11 (commit bc61739)

- New `## 11. Multi-GPU dispatch: launch and monitoring` between section 10 and the re-record appendix: golden-reference table (run_config.svg, run_config_confirm.svg, monitor_running.svg) in place of the bilingual GIF table, italic queued-note naming exactly why (new scene driver + real dual-GPU run) and pointing at the re-record appendix.
- Prose verified line-by-line against `tui/` source and the SVG goldens before writing: slot-4 多 GPU 调度 fields (`workers` live default 1, `GPUs` placeholder `—（默认: GPU 0..workers-1）`), `run_sweep_shard.py --mode dispatch --workers N` composition with present-only `--gpus`, the confirm-face 调度计划 preview line, the capacity refusal arithmetic, the three input-problem mirrors; slot-5 dispatch line + per-worker busy/idle rows from `dispatch_state.json` v2, stale marker at the shipped 3600s cell-scale grace, and the standing GPU 状态 G GPU-lanes panel with honest `◌ nvidia-smi 未安装` degradation.
- Key/Action table lists ONLY keys verified in `tui/screens/*.py` BINDINGS (`4`/`5`, `p`, `enter`, `y`/`n`, `tab`, `a`); the G panel is explicitly documented as keyless standing chrome.
- Cross-links: TUI-GUIDE anchor + multi-gpu.md runbook. Closing honest note states the goldens are fixture-injected snapshot renders and names the WINDOWS #50 review batch.
- Intro paragraph scoped "every section embeds GIFs" to sections 1-10 with the section-11 exception named (the file's honesty discipline). GIF embed count unchanged at 10.

### Task 2 — TUI-GUIDE corrective edit (commit 03ce09a)

- `## Multi-GPU monitoring (worker roots)` → `## Multi-GPU launch and monitoring`: opens with the two paths (TUI-launched dispatch via slot-4 params + confirm-face preview; CLI-launched runs attachable with ONE shared root), documents slot-5's native rendering (dispatch rows + G GPU-lanes panel), retains the numbered static-attach recipe explicitly labeled the `--mode static` variant, keeps the two-limits list with the mode-split re-run story (`[f]`→`[r]` from-failures on the attached root vs the CLI's `--rerun-failed`, cross-linked to multi-gpu.md), and cross-links TUI-DEMO section 11.
- Four same-file contradiction fixes (Rule 1 deviations, below): `[p]` row now names the `run_sweep_shard.py --mode dispatch` argv; the EHC-3 paragraph now describes the multi-GPU capacity arithmetic (the old text claimed multi-GPU machines are unrestricted — false since Phase 16); Screen 4's params table gains the 多 GPU 调度 row; Screen 5's prose names the G panel + dispatch rows with an anchor cross-ref.

### Task 3 — Version surfaces (commit bdd0033)

- `ABOUT_MILESTONE_STAGE` (tui/strings.py:1046): `开发中`/`in development` → `已交付`/`delivered` in both strings; scope enumeration and Phase 13-18 framing intact; one `_t()` call, key unchanged, explaining comment kept — the only edit in the file.
- Version surfaces verified consistent at 1.3.0 (no drift, no bump): `pyproject.toml:5` and the `uv.lock` dnallmmark block (lines 562-563).
- Proven inert outside the constant: `tests/tui/test_pilot_nav_shell.py` + `tests/tui/test_strings_phase11.py` (incl. the EXPECTED_MON_CONSTANTS tripwire and the symbol-based about pin at :892) — 27 passed, zero test edits; `make lint` and `make typecheck` both clean.

## Verification

All three task `<verify>` blocks re-run green after the final commit (section-11 heading count, dispatch/G-lanes/queued/cross-link greps, GIF count = 10; stale-claim absences, `rerun-failed`/`static`/`kill -TERM` presences; stage-word absences, single `_t` birth site, both 1.3.0 surfaces, pinned tests passing). Commits measured from the plan ledger: 3.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Stale grace documented at the shipped 3600s, not the plan's 60s**
- **Found during:** Task 1 read_first (tui/services/dispatch_state.py:57-74)
- **Issue:** The plan's must-have names "the 60s stale marker" (the 16-UI-SPEC value); the shipped source pins `DISPATCH_STALE_SECONDS = 3600.0` — WR-02 of the phase-16 review retuned it to cell scale because the writer only updates at state transitions (the original 60.0 false-positived every healthy run).
- **Fix:** Both docs state the 3600s cell-scale grace with the constant name (maintainer-tunable), per T-18-03's own "re-verified against tui/ source" mitigation.
- **Files modified:** docs/TUI-DEMO.md, docs/TUI-GUIDE.md
- **Commit:** bc61739, 03ce09a

**2. [Rule 1 - Bug] GPUs default documented as `0..workers-1`, not "all detected"**
- **Found during:** Task 1 read_first (tui/strings.py CFG_GPUS_DEFAULT; tui/services/run_config.py gpus_display)
- **Issue:** The 16-UI-SPEC's "all detected GPUs" default was corrected by WR-03 of the phase-16 review: an unset GPUs field threads no `--gpus` and dispatch_core binds the FIRST `workers` GPU indices.
- **Fix:** Placeholder and preview semantics documented exactly as shipped (verified against run_config.svg's `默认: GPU 0..workers-1）` and run_config_confirm.svg's `调度计划: 2 workers × GPUs 0,1`).
- **Files modified:** docs/TUI-DEMO.md, docs/TUI-GUIDE.md
- **Commit:** bc61739, 03ce09a

**3. [Rule 1 - Bug] Four same-file TUI-GUIDE contradiction fixes beyond lines 191-204**
- **Found during:** Task 2 edit
- **Issue:** The guide's `[p]` row claimed a `run_sweep.py` argv and the EHC-3 paragraph claimed multi-GPU machines are "unrestricted" — both false since Phase 16 and directly contradicting the rewritten section beside them; Screen 4's table omitted the workers/GPUs fields the new section references.
- **Fix:** Minimal corrective touches: `[p]` argv wording, EHC-3 paragraph rewrite to the capacity arithmetic (source: `sweep_launcher.single_gpu_launch_blocked`), one params-table row, one Screen-5 cross-ref sentence.
- **Files modified:** docs/TUI-GUIDE.md
- **Commit:** 03ce09a

## Known Stubs

None. The absent GIF in TUI-DEMO section 11 is not a stub: it is the planner-ratified no-GIF honest variant (research Q1 ruling) with the re-record explicitly queued and honestly noted in-section.

## Threat Flags

None — no new security-relevant surface (two markdown docs + one i18n constant value; threat register T-18-03/T-18-04 mitigations applied as planned).

## Self-Check: PASSED

- docs/TUI-DEMO.md, docs/TUI-GUIDE.md, tui/strings.py modified (3 files, matches plan frontmatter)
- Commits bc61739, 03ce09a, bdd0033 all present on HEAD (ancestor check run at summary time)
- No pushes performed (v1.3 local-commits-only policy)
