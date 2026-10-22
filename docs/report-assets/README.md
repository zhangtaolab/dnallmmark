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

## Regeneration

Manual, per the repo's static-file philosophy — no CI job regenerates
these. TUI captures: run the real app through the snapshot-harness
constructor seams with the real r2 dispatch state and the live probe;
browser captures: real Chromium headless over a staged r2-derived data
tree (the 17-VERIFICATION "Visual Verification" harness).
