---
phase: quick-261015-pex
plan: 01
subsystem: tui-demo
tags: [tui, demo, docs, recording, asciinema, agg]
requires:
  - "tui/ console (Phases 8-12 + quick tasks through 261015-ehc)"
  - "make tui display runtime; asciinema 3.2.1 + agg (linuxbrew)"
provides:
  - "docs/TUI-DEMO.md — the recorded operator journey (the maintainer's demo 里面需要跑真实的任务，演示所有的功能 directive, 2026-10-15)"
  - "scripts/demo/record.sh SCENE LANG [SPEED] — one-command GIF regeneration"
  - "scripts/demo/record_tui_demo.py — the deterministic pexpect scene driver (anchors from tui/strings.py)"
  - "docs/demo/{casts,gifs} 20 recordings + RECORDED.md honesty ledger"
affects: []
tech-stack:
  added: []
  patterns:
    - "pexpect pty relay → asciinema rec → agg (no browser anywhere)"
    - "anchors resolve through tui/strings.py in the active scene language; clip-safe (styled glyph/keycap spans and ~54-col modal wraps break naive anchors)"
    - "phase-boundary flush of the anchor search cursor (stale frames from earlier phases must never satisfy later anchors)"
key-files:
  created:
    - scripts/demo/record_tui_demo.py
    - scripts/demo/record.sh
    - docs/TUI-DEMO.md
    - docs/demo/RECORDED.md
    - docs/demo/casts/*.cast (20)
    - docs/demo/gifs/*.gif (20)
  modified:
    - Makefile
    - .gitignore
    - README.md
    - docs/TUI-GUIDE.md
decisions:
  - "Demo roots nest under the gitignored REPO finetuned/ tree (./finetuned/demo, ./finetuned/demo-fail) instead of the plan's sibling ./finetuned-demo spelling — nesting keeps them inside the monitor's default DISCOVERY scan root, which the sibling spelling can never reach (the manual [a] attach and the launch auto-attach both proved render-flaky in rehearsal); the real pipeline/finetuned tree is never written and PEX-3's hygiene intent holds"
  - "launch-monitor-kill carries exactly ONE on-camera launch: the console reproducibly stops processing input after a second in-session launch on this box (WINDOWS #26), so the fast-failure sweep that feeds the rerun scene is produced off-camera through the maintainer CLI surface (run_sweep.py on the reset dataset) as documented scene prep"
  - "The kill lands mid-seed-42 rather than the plan's fold-then-kill sequencing: the monitor reproducibly stalls ~60s after a launch around the first cell's completion burst (WINDOWS #27), so seed-42 completion and everything after it is unreachable in one session"
  - "The dataset scene's reset lever (delete the iPro task dir + regenerate the committed n_audit, then restore the audit baseline byte-identically after recording) was applied at FIRST record because the box had all 50 datasets present — the plan's own re-record reset mechanism, used honestly and documented in RECORDED.md"
  - "The demo custom entry (demo-custom-model) was landed before recording via the real custom_entries.land seam carrying the plant-dnabert-6mer card values — the box carried no customs and PEX-3 anticipates customs visible in the real config root; the wizard scene keeps the plan's open/edit/cancel shape"
  - "epochs override = 1 on camera: the plan's ~6-8 minute GPU estimate assumes the Phase-7 77s/seed precedent (1 epoch); the config default is 3 epochs, which would have tripled the authorized budget"
  - "record.sh gates on the driver's meta sidecar exit code: asciinema rec does NOT propagate the wrapped command's status (three incomplete zh casts initially rendered as if successful)"
metrics:
  duration: 6h 20m
  tasks: 3
  date: 2026-10-16
status: complete
actuals:
  tokens: 148000
  tasks: 3
  commits: 4
---

# Quick Task 261015-pex: TUI demo doc (docs/TUI-DEMO.md, real tasks) Summary

One-liner: docs/TUI-DEMO.md ships the maintainer-directed recorded walkthrough — ten operator-journey sections × {en, zh} GIFs of the real console doing real work (real ModelScope model + dataset downloads with reconcile, the bounded plant-dnabert-6mer × iDNA_ABF_datasets__5mC training through the y-gate with enter shown inert, the EHC-3 stage-0 refusal, log tail, the q→k kill, and a from-failures rerun driven to completion), regenerable with one command per GIF.

## What Was Built

- **scripts/demo/record_tui_demo.py** — the deterministic pexpect scene driver: ten declarative timelines over the real console pty (100×30), a streaming relay thread (the child's bytes verbatim to stdout = the asciinema cast), anchors resolved from `tui/strings.py` in the active scene language, a live presence scan for download targets, per-scene guarded filesystem prep, per-recording fresh `DNALLMMARK_TUI_STATE_DIR`, the zh contract (L on camera, restored before quit), a `--recorded-row` mode refreshing the honesty ledger, and a meta sidecar carrying targets/notes/failure screens.
- **scripts/demo/record.sh** — asciinema rec (--idle-time-limit 3) → cast-header normalization to the pinned grid → agg --theme monokai → RECORDED.md row refresh, with a meta-exit gate (asciinema does not propagate exit codes).
- **docs/demo/** — 20 casts + 20 GIFs (29 MB total, none blank) + RECORDED.md (every row states real targets, resets, sizes, date).
- **docs/TUI-DEMO.md** — ten sections each embedding both GIFs, key tables, TUI-GUIDE deep links, what-actually-happened narratives (including the honest limits), and the re-record section (EHC-3 collision guard, the dataset reset lever with the audit restore, anchor authority).
- Inbound links: README (Operator Console + docs index) and TUI-GUIDE's see-also sentence.
- Makefile: `QUICK_PEX_DEMO` existence-guard joins make lint; .gitignore covers the demo roots and meta sidecars.

## Rehearsal outcome for the plan's MUTABLE question

"the failures source over a SIGTERM-killed group is the one uncertain link" — **resolved by reading + rehearsal: a TUI kill (SIGTERM to the process group) writes NO failure record** (run_sweep dies with the group; per-cell run_records land only via the sweep's own bookkeeping, and the cell-level trainer_state.json marker is copied only at completion). The plan's honest fallback therefore applied, in a stronger form: rather than re-training the hours-scale historical failure root, the demo's fail root is produced by a **deliberately-failing real sweep** (the missing reset dataset fails the cell in ~1s) — recorded in WINDOWS-adjacent notes on the RECORDED.md rows and the doc's section 7 narrative.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing functionality] The dataset-download scene had no target**
- **Found during:** Task 2 rehearsal
- **Issue:** The box had all 50 datasets present per the committed n_audit — the plan's fallback language (written for the model lane) did not cover it, and PEX-1's truth demands a real dataset download.
- **Fix:** Applied the plan's own re-record reset lever at first record: delete `pipeline/datasets/iPro-WAEL_datasets/Promoter_R_capsulatus`, regenerate `n_audit` (33s), record the real download + reconcile (`✓ 10581 rows match`, presence back to 50/50), and restore the audit baseline byte-identically afterwards. Documented in RECORDED.md + the doc.

**2. [Rule 3 - Blocking] The wizard's on-camera landing was unreachable**
- **Found during:** Task 2 rehearsal
- **Issue:** The plan assumed a pre-existing custom row; the box had none, and the wizard's selection-list interaction could not be driven reliably.
- **Fix:** Land `demo-custom-model` before recording via the real `custom_entries.land` seam (plant-dnabert-6mer card values); the wizard scene keeps the plan's open/edit/cancel shape and the custom-entries scene drives the landed row.

**3. [Rule 3 - Blocking] The demo roots could not be monitored at the plan's spelling**
- **Issue:** `./finetuned-demo` (repo-top sibling) is invisible to the monitor's default scan roots, and both the launch auto-attach and the manual `[a]` modal proved render-flaky.
- **Fix:** Nest as `./finetuned/demo` + `./finetuned/demo-fail` (gitignored `finetuned/` wholesale) — discovered natively, `enter` attaches deterministically.

**4. [Rule 1 - Bug] Three anchor sites resolved English fragments against zh renders**
- **Issue:** The EHC-3 refusal ("single-"), the download flip ("downloa"), and the enqueue/reconcile/presence words are strings.py values that differ per language; asciinema also does not propagate the driver's exit status, so three incomplete zh casts first rendered as if successful.
- **Fix:** All anchors resolve through `tui/strings.py` in the active language; record.sh gates on the meta sidecar exit code; the four affected zh recordings re-recorded.

### Documented plan-shape changes (WINDOWS-tracked, not fixable here — tui/ is byte-frozen)

- **WINDOWS #26:** the console stops processing input after a second in-session launch → the launch scene carries exactly one on-camera launch; the fail sweep is off-camera CLI prep.
- **WINDOWS #27:** the monitor stalls ~60s after a launch (first cell's completion burst) → the kill lands mid-seed-42; the fold-then-kill sequence and the launch-toast anchor are unreachable.
- **WINDOWS #28:** typing into the slot-4 filter while the screen is mid-mount crashes the console (`NoMatches` on `#cfg-picker`) → the driver anchors the populated picker first.

## GPU spend (bounded, pre-authorized envelope)

Rehearsals (~12 full or partial launch-scene runs) + 20 recordings: the bounded `plant-dnabert-6mer × iDNA_ABF_datasets__5mC` 1-epoch cells ran roughly 25 times (~77-95s each; ~40 min GPU total), plus four iPro rerun cells. One rehearsal artifact — an accidentally enqueued DNABERT-2-117M download (a wrong-row d press before the stay-filtered idiom landed) — was removed after it flipped two presence-dependent download-queue tests off the baseline; the suite returned to exactly 7 failed / 1795 passed. The other demo-downloaded models (caduceus-ph/ps, ModernBERT-DNA-v1-37M-hg38, PlantCaduceus_l24, plant-nucleotide-transformer-6mer, prokbert-mini) are real registry downloads and stay. No sweep exceeded the demo cells; full sweeps remain dual-gated and untouched.

## Auth Gates

None — no credentials or auth surfaces were involved.

## Known Stubs

None. Every GIF row in RECORDED.md states exactly what its footage shows, including the three honest-limit notes (fast-mirror tick coalescing on both download scenes, mid-seed-42 kill, off-camera fail-sweep prep).

## Self-Check: PASSED

- All 20 casts + 20 GIFs exist on disk; RECORDED.md rows == GIF count == cast count (20/20/20)
- No blank GIFs (all > 40KB); docs/demo total 29 MB (< ~60 MB budget)
- `plant-dnabert-6mer` present in the gate-scene casts; the demo root present in the preview casts; the zh top-bar anchor (环境检查) present in all 10 zh casts
- tui/ byte-untouched (`git diff --stat -- tui/` empty); all commits trailer-free
- make lint + make typecheck green; full make test at exactly the 7 failed / 1795 passed baseline (zero new tests)
- The committed n_audit baseline restored byte-identically; the real pipeline/finetuned tree never written
