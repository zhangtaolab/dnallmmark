---
phase: 18-docs-authoring
plan: "04"
subsystem: docs-report
tags: [report, milestone, evidence, html, static-document, figures]
requires:
  - "18-01/18-02/18-03 landed docs (the phase-18 section describes them as landed truth)"
  - "the ratified 18-UI-SPEC (structure, tokens, badge vocabulary, figure contract, print stylesheet, zero-external-request gate)"
  - "the evidence corpus: five VERIFICATION frontmatters, 15-01/15-03 SUMMARYs, 17-VERIFICATION.md, the phase15/phase17 runtime evidence packs"
provides:
  - "docs/v1.3-test-report.html — the v1.3 milestone test-results report (D18-05..D18-08): six phase sections in the uniform shape, two gap-closure callouts, GPU run evidence with correctly-paired run ids, lanes-and-exclusions with the environmental detail, print stylesheet, zero external requests"
  - "docs/report-assets/ — eight committed assets with the per-asset honesty ledger (README.md)"
  - "README docs-index bullet linking the report (D18-08)"
affects:
  - "README.md (docs index)"
tech-stack:
  added: []
  patterns:
    - "real-data figure capture: the real app via the golden-harness constructor seams threaded with REAL data (archived r2 dispatch state, live probe, real registry view) — never a hand-authored mock"
    - "fresh-vs-recorded lane labeling (a fresh re-run is dated FRESH and never mixed unlabeled with recorded numbers)"
key-files:
  created:
    - docs/v1.3-test-report.html
    - docs/report-assets/README.md
    - docs/report-assets/shot-scatter.png
    - docs/report-assets/shot-scatter-tooltip.png
    - docs/report-assets/shot-bars.png
    - docs/report-assets/shot-bars-tooltip.png
    - docs/report-assets/monitor_running.svg
    - docs/report-assets/run_config.svg
    - docs/report-assets/run_config_confirm.svg
  modified:
    - README.md
decisions:
  - "The three TUI SVG figures are FRESH real-data captures (the orchestrator's binding maintainer rule 2026-10-22), not copies of the fixture-driven WINDOWS #50 goldens the plan letter named: same filenames (gate-compatible), PENDING-REVIEW badges retained (fresh + unreviewed; #50 named in-caption/footer), captions state exactly what ran"
  - "The scatter-tooltip figure was re-captured live at generation time because the runtime pack's copy was byte-identical to shot-scatter.png (the tooltip had not fired before the original shutter); the committed asset is the new capture with live-state verification (tooltip opacity=1, 1 active element)"
  - "Q4 ruling honored: the recorded 2236/6 counts are cited with the 17-VERIFICATION.md:121 proxy caveat verbatim and the milestone-close gate owns the fresh full-suite run; the two cheap lanes WERE re-run fresh and are dated as such"
metrics:
  duration: 18 min
  completed: 2026-10-22
  tasks: 3
  files: 10
status: complete
actuals:
  tokens: 83800   # chars/4 over the realized text diff (335,109 chars — the three SVG text assets dominate; PNG binaries excluded) vs estimate 75000
  tasks: 3
  commits: 3      # MEASURED: git rev-list --count 92669b9..HEAD
plan_head_before: 92669b9149ba9c33c9209f0c2b31e65611892575
plan_head_after: d9098fffc20aae974bd89986476e2745a318f8b4
---

# Phase 18 Plan 04: v1.3 Milestone Test-Results Report Summary

**One-liner:** docs/v1.3-test-report.html — a self-contained, offline-viewable HTML report covering all six v1.3 phases (uniform Goal/Shipped/Evidence/Analysis), both gap-closure callouts, GPU runs with correctly-paired run ids, and the per-lane test summary with itemized environmental exclusions — with eight committed assets under docs/report-assets/, three of them fresh real-data TUI captures (real app + real r2 dispatch state + live probe + real registry view), linked from the README docs index.

## What Was Executed

### Task 1 — TRACER: skeleton end-to-end (commit c4e89ee)

- `docs/report-assets/` created; first two assets committed: the
  scatter browser-verification PNG (real Chromium over the staged r2
  data chain) and — per the maintainer figure rule, in place of a blind
  golden copy — a FRESH `monitor_running.svg` real-data capture (see
  Deviations 1). Ledger `docs/report-assets/README.md`: one row per
  asset naming origin, capture context, review status.
- `docs/v1.3-test-report.html` skeleton exactly per the ratified
  18-UI-SPEC: single inline `<style>` mirroring the
  `dnallm-mark/css/variables.css` tokens verbatim as literals (system
  font stack, spacing 4/8/16/24/32/48, the Color table's surfaces and
  exactly the four derived AA badge tones — the only new hex), 1100px
  centered column, the single 768px breakpoint, the print stylesheet
  (phase page-breaks, TOC hidden, pre wrapped).
- Skeleton content: header + verbatim generation date (2026-10-22,
  hand-written), in-page TOC, summary verdict line ("All 20 v1.3
  requirements delivered; every lane green at the documented baseline
  with 6 environmental exclusions"), the 7-row lane summary table with
  citations and the four-badge legend row directly beneath, the
  COMPLETE phase-13 section, Figures 1-2 with the two-line caption
  contract and alt text.
- README docs-index bullet added (D18-08).
- Tracer feedback gate: automated-only verify re-run end-to-end — all
  green (files, zero-external-request grep, no /root paths, verdict /
  legend / 23/23 / caption / print / responsive markers, README link).

### Task 2 — six sections + callouts + GPU evidence + five assets (commit a4a2af2)

- Phases 14/15/16/18 in the uniform shape (goals quoted from ROADMAP;
  shipped from the phase SUMMARYs; evidence rows with the verification
  scores 28/28 · 7/7 · 41/41 · 16/16 and named tests; one hard-problem
  analysis each); phase 17 completed (What Shipped + evidence rows +
  analysis). The phase-18 section cites the landed 18-01..18-03
  deliverables by path plus this report itself.
- Two teal gap-closure callouts: 15-04 (dispatch run_record writer —
  the Phase-13 A3 supersession) and 15-05 (the WINDOWS #45 option-A
  eval merge), arcs quoted from the named SUMMARYs.
- GPU-evidence section: smoke (155 s, exit 0, 2 cells, run_id
  `7759c2cc…` — both cited to 15-01-SUMMARY.md:102,108) and sweep
  (272 s, done 12/12, 0 failed/skipped, both GPUs, run_id
  `4e74c92d…` — cited to 15-03-SUMMARY.md:145-147); the terminal
  dispatch_state JSON and the live dispatcher log head as escaped pre
  blocks inside `<details>` disclosures. The superseded r1 run id
  appears nowhere (gate-asserted).
- Five more assets committed with ledger rows: `shot-scatter-tooltip.png`
  (the FRESH capture — Deviations 2), `shot-bars.png`,
  `shot-bars-tooltip.png`, `run_config.svg`, `run_config_confirm.svg`
  (both fresh real-data captures). Figures 3-7 embedded with the
  caption contract; SVG figures PENDING-REVIEW, PNGs PASS.

### Task 3 — lanes detail + footer + full final gate suite (commit d9098ff)

- Lanes-and-exclusions section: the six root-chmod exclusions itemized
  (test_pilot_data_manager.py ×1 + test_services_download_queue.py ×5)
  with the mandatory reason string (chmod-000 write-block simulations
  that root ignores; citations 17-03-SUMMARY.md:159-161); the recorded
  2236/6 baseline quoted with the 17-VERIFICATION.md:121 proxy caveat
  VERBATIM and the Q4 ruling stated (no fresh full-suite in-phase; the
  milestone-close gate owns it).
- Fresh dated lane re-runs at generation (FRESH 2026-10-22):
  `node --test tests/js/*.test.js` → 44 tests, 44 pass, 0 fail
  (246 ms); `pytest tests/test_determinism.py
  tests/test_vendored_stats.py -q` → 10 passed in 2.58s — each labeled
  fresh, never mixed unlabeled with recorded numbers.
- Footer colophon: the regeneration sentence verbatim ("This report is
  a committed static artifact; regeneration is manual per the repo's
  static-file philosophy (no CI job, D18-08)."), the generation date
  matching the header, the WINDOWS #50 pending-review note, the
  commit/state stamp (a4a2af2 @ autorun).
- Final gate suite green: zero-external-request grep = 0 hits, no
  absolute machine paths, pairing greps (both r2 ids present,
  `aff2faa3` absent), badge legend present, 7 `<figure>` × 7 `Proves:`
  lines, six `id="phase-1[3-8]"` sections, README link resolves,
  ci.yml hash `33d2252eb594e0faecece9e8015a332d8d6479ef` byte-pinned,
  `dnallm-mark/data/` porcelain-clean, `make lint` + `make typecheck`
  both "All checks passed!".

### What actually ran, per figure (the maintainer figure rule)

| Figure | Asset | Process + data source |
|---|---|---|
| 1 — slot-5 Monitor | monitor_running.svg | REAL app instance (real MonitorScreen via `App.run_test` + `App.export_screenshot`, the snapshot-harness constructor seams); dispatch rows = REAL archived mid-run dispatch_state of the r2 sweep (running 6/12, queue 4, both workers in-flight on `plant-dnamamba-6mer × GUE__emp_H3` seeds 42/43) parsed by the real `read_dispatch_state`; G lanes = REAL live nvidia-smi probe at capture time (2× idle, 28 °C); card cell grid = harness fixture reconstructed from that archived state |
| 2 — slot-4 run-config | run_config.svg | REAL app instance; picker = the REAL overlay-merged registry view on this machine (模型 2/62 · 数据集 2/50 — 59 official + 3 local custom models, 50 datasets); marks/params = the executed r2 matrix (2 models × 2 tasks, seeds 42/43/44, workers=2, GPUs 0,1); preview line 干跑 2×2×3=12 computed by the real preview; screen state = harness fixture |
| 3 — launch confirm | run_config_confirm.svg | REAL app instance; the real gate chain (enumeration → problems → capacity → preflight → confirm) over the same spec; gate summary computed by the real `gate_confirm_data` arithmetic (调度计划: 2 workers × GPUs 0,1 · 排队 12; the four real model×task pairs); the modal renders, never computes |
| 4 — scatter | shot-scatter.png | Real Chromium headless (playwright-core) over the staged r2 re-run through the real export→summarize chain; plugin live-registered; std point 0.0488/n=3; marker ink pixel-verified (17-VERIFICATION "Visual Verification") |
| 5 — scatter tooltip | shot-scatter-tooltip.png | FRESH capture 2026-10-22 at report generation: pointer moved to the std point's live pixel (x=54, y=489 — matches the recorded geometry.json); live chart state read back before the shutter: tooltip opacity=1, 1 active element, 1 body line |
| 6 — task bars | shot-bars.png | Same real Chromium session; live dataset = 2 floating-bar arrays exactly mean±std; bar ink + both whisker caps pixel-asserted at predicted pixels (17-VERIFICATION) |
| 7 — bars tooltip | shot-bars-tooltip.png | Same real Chromium session; tooltip on hover rendering the ±std seed-spread line (the closure-read review fix) |

Plus the two `<details>` pre blocks: the terminal dispatch_state JSON
(read from `pipeline/finetuned-sweep-r2/dispatch_state.json`) and the
live dispatcher log head — both HTML-escaped (T-18-05).

### Browser render check (recorded per Task 3)

Real Chromium headless over `file://…/docs/v1.3-test-report.html`
(relative assets, no server): all 7 images `complete=true` with
`naturalWidth > 0`; rendered figure boxes correct (SVGs 1068×740 ≈ the
UI-SPEC's predicted ~72-74% scale of the 1482-wide renders inside the
1100px column; PNGs 1068×687); the 4-badge legend renders; 6
PENDING-REVIEW badges; all 10 TOC anchors resolve to existing section
ids; body background #FFFFFF. The print-to-PDF pass remains the
end-of-phase human review item per the 18-UI-SPEC backstop row.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - honest-figure-data] TUI SVGs are fresh real-data captures, not copies of the WINDOWS #50 goldens**
- **Found during:** Task 1 asset preparation
- **Issue:** The plan letter says commit "the monitor-running SVG golden (a copy…)"; the orchestrator's binding maintainer rule (2026-10-22) requires every figure to state what really ran, naming the golden-harness real-data capture as the sanctioned path — a copied fixture-driven golden captioned as the figure would understate what ran.
- **Fix:** All three TUI SVGs were generated at report time by a throwaway driver (not committed — the 12-05 throwaway-probe precedent) running the REAL app through the existing snapshot-harness constructor seams threaded with REAL data (archived r2 mid-run dispatch state via the real parser, live nvidia-smi probe, real overlay-merged registry view, the real r2 matrix spec, real gate arithmetic). Same filenames as planned (all gates pass unchanged); PENDING-REVIEW badges retained per the plan (fresh, unreviewed; #50 named in-caption and footer); captions and the asset ledger state precisely which legs are real and which are fixture.
- **Files modified:** docs/report-assets/{monitor_running,run_config,run_config_confirm}.svg
- **Commit:** c4e89ee, a4a2af2

**2. [Rule 1 - figure honesty] The runtime scatter-tooltip PNG was byte-identical to the plain scatter shot**
- **Found during:** Task 1 asset inventory (cmp of the phase17-preview pack)
- **Issue:** `shot-scatter-tooltip.png` in the runtime evidence pack is byte-identical to `shot-scatter.png` — the tooltip had not fired before the original shutter. Committing it as a distinct "tooltip" figure would have misrepresented the capture.
- **Fix:** Re-captured live at generation time (the staged r2-derived site re-served; pointer moved to the std point's live pixel read back from the chart instance; tooltip verified live before the shutter: opacity=1, 1 active element). The committed asset is the new 66,294-byte capture; the ledger row documents the replacement.
- **Files modified:** docs/report-assets/shot-scatter-tooltip.png
- **Commit:** a4a2af2

**3. [Rule 3 - blocking] The structural grep gate collided with the report's own prose**
- **Found during:** Task 2 verify
- **Issue:** The phase-18 evidence bullet describing the gates ("no script tags, no @import, no url(http)") matched the Task-3 zero-external-request grep pattern, failing the structural gate on descriptive words.
- **Fix:** Reworded the bullet to non-colliding phrasing ("no scripting of any kind, no CSS imports, no external URLs, no web fonts"). Gate = 0 hits.
- **Files modified:** docs/v1.3-test-report.html
- **Commit:** a4a2af2

Also fixed inline (same-commit typo repair): a missing space in
"and 5%" and the phase-15 goal quote restored to the ROADMAP wording.

## Auth Gates

None.

## Known Stubs

None — no placeholders, no fabricated captures. The pty live-capture
figure was NOT attempted as a pty run: the orchestrator's ACCEPTABLE
fallback (real app via the golden-harness constructor seams + real r2
dispatch data + real probe) was used and is captioned as exactly that;
the pty capture + TUI-DEMO GIF re-record stay queued (named in the
lanes section's deferred items, per the ratified honest-degradation
path).

## Threat Flags

None beyond the plan's threat model. T-18-05 (evidence tampering via
pasted text): every pre block is HTML-escaped (no raw `<`/`&` in any
pasted JSON or log line; prose comparators written as `&lt;`).
T-18-06/T-18-07: zero-external-request and no-absolute-path gates = 0
hits. T-18-08: pairing gates green (7759c2cc + 155 s together, 4e74c92d
+ 272 s together, `aff2faa3` absent). T-18-09: three PENDING-REVIEW
figure badges + the footer note naming the #50 batch.

## Self-Check: PASSED

- All nine artifacts exist on disk (docs/v1.3-test-report.html; the
  eight report-assets incl. the ledger README.md).
- Commits c4e89ee, a4a2af2, d9098ff present on `autorun`, ancestors
  of HEAD; ledger base 92669b91…; measured commit count 3.
- No push performed (v1.3 local-commits-only policy held).
