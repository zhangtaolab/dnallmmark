# Report assets — honesty ledger

Per-asset provenance for every image embedded in
[`../v1.3-test-report.html`](../v1.3-test-report.html), in the
`docs/demo/RECORDED.md` precedent: one row per asset naming its origin,
the capture context (what process really ran, over what data), and its
review status. Copies live here; the originals stay where they were
produced.

| Asset | Origin | Capture context | Review status |
|---|---|---|---|
| `shot-scatter.png` | Phase-17 browser verification pack (runtime evidence dir, uncommitted by design; findings recorded in `.planning/phases/17-web-multiseed-error-bars/17-VERIFICATION.md` "Visual Verification — Delegated to Orchestrator") | Real Chromium headless (playwright-core) over a staged gitignored preview serving the Phase-15 r2 sweep re-run through the real export→summarize chain with the Phase-17 aggregation code; repo untouched. Plugin `errorbars` live-registered; std point std=0.0488/n=3; marker ink pixel-verified. Captured 2026-10-22. | Shown with ✓ PASS in the report |
| `monitor_running.svg` | Generated 2026-10-22 by a throwaway driver running the REAL app through the existing golden-harness constructor seams (`tests/tui/test_snapshots.py` machinery; the driver is not committed — the 12-05 throwaway-probe precedent) | Real app instance (the real `MonitorScreen` via `App.run_test` + `App.export_screenshot`). Dispatch rows = the REAL archived mid-run `dispatch_state` of the r2 sweep (`dispatch_state.midrun-sweep-r2.json`: running, 6/12, queue 4, workers in-flight on `plant-dnamamba-6mer × GUE__emp_H3` seeds 42/43), parsed by the real `tui.services.dispatch_state.read_dispatch_state`; G lanes = the REAL live `nvidia-smi` probe at capture time (2× GPUs idle post-milestone); card cell grid = harness fixture reconstructed from that archived state. Snapshot-dir golden namesake `tests/tui/__snapshots__/monitor_running.svg` stays uncommitted (WINDOWS #50). | Shown with ◌ PENDING-REVIEW in the report |
| `shot-scatter-tooltip.png` | Fresh capture at report generation (2026-10-22), same harness as above | Real Chromium headless over the same staged r2-derived site; pointer moved to the std point's live pixel (x=54, y=489, read back from the chart instance — matches `geometry.json`); live chart state read back before the shutter: tooltip opacity=1, 1 active element, 1 body line. (The earlier same-named capture in the runtime pack was byte-identical to `shot-scatter.png` — the tooltip had not fired before the shutter — and was replaced by this verified capture.) | Shown with ✓ PASS |
| `shot-bars.png` | Phase-17 browser verification pack (runtime evidence dir) | Same real Chromium session over the staged r2 chain; task bar chart (5mC): live dataset = 2 floating-bar arrays exactly mean±std; bar ink and both whisker caps pixel-asserted at predicted pixels. Captured 2026-10-22. | Shown with ✓ PASS |
| `shot-bars-tooltip.png` | Phase-17 browser verification pack (runtime evidence dir) | Same real Chromium session; pointer hovered a bar — the tooltip renders the model row with the ±std seed-spread line (the closure-read review fix). Captured 2026-10-22. | Shown with ✓ PASS |
| `run_config.svg` | Generated 2026-10-22 by the same throwaway real-app driver as `monitor_running.svg` (snapshot-harness constructor seams; driver not committed) | Real app instance (the real slot-4 screen). Picker entries = the REAL overlay-merged registries on the validation machine (模型 2/62 · 数据集 2/50: 59 official + 3 local custom models, 50 datasets); marks/params = the executed r2 matrix (2 models × 2 tasks, seeds 42/43/44, workers=2, GPUs 0,1); preview line "干跑: 2 模型 × 2 任务 × 3 种子 = 12 训练项" computed by the real preview; params/argv legs delegate to the real service module; screen state + path rows are harness fixtures. Snapshot-dir namesake `tests/tui/__snapshots__/run_config.svg` stays uncommitted (WINDOWS #50). | Shown with ◌ PENDING-REVIEW |
| `run_config_confirm.svg` | Generated 2026-10-22 by the same throwaway real-app driver | Real app instance — the real gate chain (enumeration → problems → capacity → preflight → confirm) over the same real r2 spec; the gate summary computed from the spec by the real `gate_confirm_data` arithmetic (调度计划: 2 workers × GPUs 0,1 · 排队 12; the four real model×task pairs); the modal renders, never computes. Snapshot-dir namesake `tests/tui/__snapshots__/run_config_confirm.svg` stays uncommitted (WINDOWS #50). | Shown with ◌ PENDING-REVIEW |

## Regeneration

Manual, per the repo's static-file philosophy — no CI job regenerates
these. TUI captures: run the real app through the snapshot-harness
constructor seams with the real r2 dispatch state and the live probe;
browser captures: real Chromium headless over a staged r2-derived data
tree (the 17-VERIFICATION "Visual Verification" harness).
