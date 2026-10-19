---
schema_version: 1
open_count: 8
waived_count: 6
fixed_count: 28
total_count: 42
last_updated: 2026-10-19T14:56:56.393Z
---

# Broken Windows Ledger

> Cross-phase defect register. With `workflow.windows_enforce` enabled, `/gsd-ship` blocks while `open_count > 0`.
> Waive with `gsd-tools windows waive <id> "<reason>"` (reason required).
> Mark fixed with `gsd-tools windows fixed <id>`.

| id | phase | kind | file | line | description | status | reason | recorded_at | resolved_at |
|----|-------|------|------|------|-------------|--------|--------|-------------|-------------|
| 1 | 01 | stub | AUDIT.md | 132 | Secret-scan evidence section is an intentional placeholder filled by plan 01-03 task 3 (REL-05 gitleaks run) | waived | gitleaks evidence landed in 01-SECURITY.md (plan 01-03 task 3, REL-05) | 2026-10-08T14:33:35.112Z | 2026-10-19T13:57:22.521Z |
| 2 | 4 | stub | pipeline/models_info.json |  | Chaoba card: series/architecture/context_len/species/type/huggingface/modelscope are empty-string (no locatable upstream page) — 04-04 | open |  | 2026-10-10T03:13:03.112Z |  |
| 3 | 4 | stub | pipeline/models_info.json |  | Chaoba_all_species card: series/architecture/context_len/species/type/huggingface/modelscope are empty-string (no locatable upstream page) — 04-04 | open |  | 2026-10-10T03:13:03.177Z |  |
| 4 | 4 | stub | pipeline/models_info.json |  | Chaoba_denseMamba card: series/architecture/context_len/species/type/huggingface/modelscope are empty-string (no locatable upstream page) — 04-04 | open |  | 2026-10-10T03:13:03.243Z |  |
| 5 | 4 | stub | pipeline/models_info.json |  | denseSSM_plant_genome card: series/architecture/context_len/species/type/huggingface/modelscope are empty-string (no locatable upstream page) — 04-04 | open |  | 2026-10-10T03:13:03.337Z |  |
| 6 | 4 | stub | pipeline/models_info.json |  | mamba2_370M card: series/architecture/context_len/species/type/huggingface/modelscope are empty-string (no locatable upstream page) — 04-04 | open |  | 2026-10-10T03:13:03.403Z |  |
| 7 | 4 | stub | pipeline/models_info.json |  | mamba2_plant_genome card: series/architecture/context_len/species/type/huggingface/modelscope are empty-string (no locatable upstream page) — 04-04 | open |  | 2026-10-10T03:13:03.490Z |  |
| 8 | 4 | stub | pipeline/models_info.json |  | prokbert card: series/architecture/context_len/species/type/huggingface/modelscope are empty-string (no locatable upstream page) — 04-04 | open |  | 2026-10-10T03:13:03.577Z |  |
| 9 | 4 | deviation | tests/test_export_runs.py | 466 | D-15 evaluate cross-check covers the scipy-backed evaluate metrics (pearsonr/spearmanr) only — evaluate's accuracy/f1/mcc modules import scikit-learn, which is outside the sanctioned scipy+evaluate dependency pair; extending coverage needs a maintainer-approved scikit-learn addition | fixed |  | 2026-10-10T05:22:49.317Z | 2026-10-19T13:57:22.133Z |
| 10 | 05 | unrun-verify | .github/workflows/ci.yml |  | First real GitHub-runner execution of ci.yml happens on the maintainer's next push (badge green + <15-min/job + branch-protection setup queued in 05-USER-SETUP.md) | fixed |  | 2026-10-10T10:04:38.260Z | 2026-10-19T13:57:21.876Z |
| 11 | 05 | unrun-verify | dnallm-mark/js/main.js |  | 05-02 Task 3 human-check (visual localhost confirmation of weighted default view, raw-rank toggle, stamped footer) deferred to the phase-level UAT gate — behavioral seams pinned by tests/js/main-view-toggle.test.js | waived | 05-02 weighted-default visual check confirmed at landing (behavioral seams pinned by js tests) | 2026-10-10T10:52:34.776Z | 2026-10-19T13:57:22.601Z |
| 12 | 5 | unrun-verify | pipeline/run_finetune.py |  | 05-03: --subset_file seam + pipeline/eval_subsets.json consumption execute only at E2' (GPU, maintainer dual-gated); CPU-side stub/contract tests + real-artifact validation proof pin the behavior — first real GPU consumption pending launch | fixed |  | 2026-10-10T11:22:28.566Z | 2026-10-19T14:56:56.393Z |
| 13 | 05 | deviation | pipeline/sweep_priorities.json |  | 05-04 Task 4 blocking-human gate (tier-2 arena curation, D-17/OQ4): tier 2 shipped EMPTY at Task 2 awaiting maintainer decision — resolved 2026-10-10, maintainer selected per-arena one representative (animal GENERanno-eukaryote-0.5b-base / plant PlantCAD2-Small-l24-d0768 / microbe Omni-DNA-700M), landed in 6598e45 | fixed |  | 2026-10-10T12:27:48.027Z | 2026-10-10T12:27:53.830Z |
| 14 | 06 | deviation | pipeline/env_smoke.py |  | matmul expected constant corrected 64.0->512.0 (Rule 1, found by first executed smoke) | fixed |  | 2026-10-10T18:29:17.849Z | 2026-10-19T13:57:21.940Z |
| 15 | 06 | deviation | dnallm-mark/data/provenance.csv |  | 06-04 Task 4 blocking-human gate (maintainer provenance review, CONTEXT Area 2): execution paused at the gate with the Unspecified-default state committed — resolved 2026-10-11, maintainer selected 'reviewed 接受现状' (accept as-is; 35/7/9 Unspecified rows stand as honest unknowns), landed in c59f5f8 | fixed |  | 2026-10-10T23:55:42.192Z | 2026-10-10T23:55:51.180Z |
| 16 | 07 | deviation | schemas/flops_report.json |  | layer_details/total_flops_exact typed number not integer (Rule-1: verbatim Hyena FFT formula emits fractional FLOPs) — resolved, documented in 07-01-SUMMARY | fixed |  | 2026-10-11T06:45:51.224Z | 2026-10-11T06:46:26.720Z |
| 17 | 9 | stub | tui/screens/wizard.py | 381 | gauntlet phase renders a minimal pending view (title + 待检 line) — the real subprocess panel is 09-05's deliverable over the on_valid seam | fixed | 09-05 Task 1: the real gauntlet panel landed over the phase slot (async run-id-tagged rows, land-only-on-all-pass, drill-down); the minimal pending view remains only for the no-service construction | 2026-10-12T04:54:51.935Z | 2026-10-12T05:55:00.000Z |
| 18 | 9 | stub | tui/screens/wizard.py | 470 | f binding routes to the on_import seam with no view behind it — the file-import view is 09-05's deliverable (planned functionality gap, D-11) | fixed | 09-05 Task 2: f routes to the import path prompt + per-entry sequential gauntlet with entry-level rollback (D-11 view behind the seam) | 2026-10-12T04:54:57.893Z | 2026-10-12T05:55:00.000Z |
| 19 | 9 | stub | tui/screens/wizard.py | 475 | o binding routes to the on_export seam with no view behind it — the registry-export view is 09-05's deliverable (planned functionality gap, D-11) | fixed | 09-05 Task 2: o routes to the empty-state-checked export path prompt + the verbatim registry copy (D-11 view behind the seam) | 2026-10-12T04:54:57.963Z | 2026-10-12T05:55:00.000Z |
| 20 | 11 | deviation | .planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-07-SUMMARY.md |  | GB10 smoke (SC5 execution half) pending maintainer run — procedure in 11-07-SUMMARY, not executor-executable (D-15) | fixed | executed live 2026-10-13 (11-UAT.md status passed 2/2, maintainer-authorized bounded smoke incl. the E2'-blocks proof); artifacts re-read on disk by the 2026-10-16 refresh verifiers (finetuned-smoke/ both cells + trainer_state markers) — ledger row left open by bookkeeping oversight, closed 2026-10-16 | 2026-10-13T06:06:35.033Z | 2026-10-13T00:00:00.000Z |
| 21 | 12 | unrun-verify | .planning/phases/12-multi-gpu-orchestration-console-hardening/12-05-SUMMARY.md |  | N=2 multi-GPU smoke (MGPU validation half) pending maintainer run on the OTHER machine — 9-step procedure in docs/multi-gpu.md + 12-05-SUMMARY, not executor-executable (D-05: this machine is dev/test only, single GPU) | open |  | 2026-10-13T13:38:34.565Z |  |
| 22 | quick-261014-c2l | unmet-truth | tests/test_schemas.py |  | Full make-test gate blocked by 10 PRE-EXISTING base failures (5 schema/determinism pins stale after data commit 9e803ca, 5 root-user chmod persist-failure sims) — verified failing identically at base 8f3af3c; this task's own lanes + lint + typecheck + node(26) green (see deferred-items.md) | fixed |  | 2026-10-14T01:21:59.202Z | 2026-10-19T13:57:22.004Z |
| 23 | quick-261014-dcl | deviation | tests/tui/__snapshots__/wizard.svg |  | wizard.svg golden collateral drift: the wizard golden pins env-screen pixels at its left edge, so the 261014-dcl eighth env row drifted it (committed with the change per D-03; the plan pinned exactly four SVG diffs) | fixed | absorbed by the D-03-approved full golden refresh (d5cb44b, 2026-10-15): wizard.svg regenerated with the other 8 goldens and committed under maintainer review | 2026-10-14T03:38:33.288Z | 2026-10-15T06:45:36.321Z |
| 24 | quick-261014-f4w | deviation | tests/tui/__snapshots__/wizard.svg |  | wizard.svg golden collateral drift again during make snapshot-update (render-state flake documented in dcl deferred-items, ~2/17 loads, pre-existing at base): committed with the change per D-03 alongside the plan-pinned run_config.svg + env_check.svg | fixed | absorbed by the D-03-approved full golden refresh (d5cb44b, 2026-10-15); the render-state flake itself stays documented in dcl deferred-items | 2026-10-14T05:14:07.356Z | 2026-10-15T06:45:36.243Z |
| 25 | quick-261014-mlc | deviation | tests/tui/test_snapshots.py |  | All 9 SVG goldens strict-xfail pending maintainer make snapshot-update + D-03 review (slot-2/3 rework + locked nav rename) | fixed | maintainer D-03 review approved 2026-10-15; all 9 goldens regenerated via make snapshot-update (zh pin) and committed in d5cb44b with the strict-xfail markers retired; suite at the 7F baseline with the 9 goldens passing | 2026-10-14T10:25:24.246Z | 2026-10-15T06:45:17.867Z |
| 26 | quick-261015-pex | unmet-truth | tui/app.py |  | Post-second-launch console input death (pex rehearsals): after a SECOND in-session gated launch the console stops processing navigation while renders continue (the launch toast/auto-switch render late or never); the demo restructured to exactly one on-camera launch and the fast-failure sweep moved to CLI prep | fixed |  | 2026-10-15T23:59:00.000Z | 2026-10-19T14:22:50.525Z |
| 27 | quick-261015-pex | unmet-truth | tui/screens/monitor.py |  | Monitor stalls ~60s after a TUI launch on this box (around the first cell's completion output burst): the stats cadence stops and keys stop processing; the fold-then-kill demo sequence (seed 42 completes, kill seed 43) is unreachable - the demo kill lands mid-seed-42 | fixed |  | 2026-10-15T23:59:00.000Z | 2026-10-19T14:22:50.589Z |
| 28 | quick-261015-pex | unmet-truth | tui/screens/run_config.py | 1618 | Typing into the slot-4 filter while the screen is mid-mount crashes the console: on_input_changed -> _render_picker -> query_one('#cfg-picker') raises NoMatches (observed once in pex rehearsal; the demo driver works around it by anchoring the populated picker before typing) | waived | not reproducible in 12 aggressive tries (2026-10-19); structural closure verified: entries-empty guard before _render_picker, fresh RunConfigScreen per navigation, digits cannot navigate while filter focused. Latent unguarded query_one family in run_config.py event handlers noted — real fix only if entries ever load synchronously or screens get cached | 2026-10-15T23:59:00.000Z | 2026-10-19T14:22:50.654Z |
| 29 | quick-261016-vxr | deviation | tests/tui/__snapshots__/monitor_running.svg |  | monitor_running.svg AND monitor_empty.svg regenerated (the slot-5 [k] 停止 keycap row) via make snapshot-update, deliberately UNCOMMITTED pending the maintainer's D-03 review - the committed tree fails test_snapshots on exactly these two until they land (run_config.svg byte-preserved, sha256 afa89e7e...) | fixed | D-03 review approved 2026-10-17; the three SVGs landed in f2a772a | 2026-10-17T00:00:00.000Z | 2026-10-17T01:34:00.000Z |
| 30 | quick-261017-eea | deviation | schemas/model_performance.json |  | Rule-2 deviation (eea commit 9a83066): the 141 helixgen entries carry FLOPs empty-string where the schema demanded strict number — schema conformed to the sibling anyOf [number, const ''] shape (1 line) after verifying the  documents '' as the missing-value convention, all 13 sibling metrics already use anyOf, summarize is ''-safe, and no test pins FLOPs strictness; fabricating numbers forbidden | fixed |  | 2026-10-17T02:55:52.918Z | 2026-10-19T13:57:22.196Z |
| 31 | quick | deviation | pipeline/run_finetune.py | 849 | run_finetune sibling hard-index sites deliberately unfixed (07-CR-01 batch covered only the model-loop reads): :849 probe-branch row[Model_name], :1077 dataset-loop row[Dataset_name], :1322 row[length] — schema-legal minimal custom entries crash these paths; future maintainer-ruled batch (see 261017-klw-SUMMARY Maintainer Items) | fixed |  | 2026-10-17T07:36:01.293Z | 2026-10-19T13:57:22.260Z |
| 32 | quick-261017-mad | deviation | tests/tui/test_snapshots.py | 944 | test_monitor_running_golden load-timing flake (pre-existing, observed once at the 261017-mad pre-task baseline): the SVG terminal-id is an adler32 hash over every rendered segment, and one full-suite run under load rendered one differing segment; identical rerun green, module green 11/11 in isolation, all fixture data frozen — root cause a load-dependent refresh artifact at export time, not reproduced by 261017-mad changes | fixed |  | 2026-10-17T08:50:31.381Z | 2026-10-19T13:57:22.067Z |
| 33 | quick-261017-mad-followup | unmet-truth | tui/services/run_config.py |  | Storage-overview ✗ semantics for lazily-created dirs: the cache_dir row renders the same red ✗ as a missing model/dataset root, but a nonexistent cache dir is the healthy never-written-yet state (HF creates it on first use) — misleading failure signal; consider a neutral glyph or an on-demand note for the cache row | fixed |  | 2026-10-17T09:02:07.464Z | 2026-10-19T14:51:26.876Z |
| 34 | quick-261017-feedback | unmet-truth | tui/screens/monitor.py |  | Monitor status conflation: interrupted cells (dir + no trainer_state marker + no live process) render the same 运行/running state as genuinely-running cells — maintainer hit it reading finetuned-smoke history (PlantHelixSeek 10-16 kill + dnamamba 10-15 interruption both show ⠋ 运行). Needs a three-state derivation (done / running-with-live-process / interrupted) or at least a distinct interrupted glyph | fixed | 261017-uwr: the three-state derivation landed (live-matrix evidence via argv_matrix/probe + CELL_INTERRUPTED ⏸ glyph + live-on-top ordering + context header); the PlantHelixSeek/dnamamba residue now derives interrupted | 2026-10-17T14:12:12.091Z | 2026-10-17T14:57:36.000Z |
| 35 | quick-261017-uwr | deviation | tests/tui/__snapshots__/monitor_running.svg |  | monitor_running.svg AND monitor_empty.svg regenerated via make snapshot-update, deliberately UNCOMMITTED pending the maintainer's D-03 review (all 7 non-monitor SVGs sha256-identical). AMENDED 261018-kvj: the uwr worktree pair was SUPERSEDED by the two-tab redesign's regeneration — the CURRENT uncommitted bytes are the ONE combined D-03 monitor-golden handoff for both batches (uwr + kvj tabbed surface); run_config.svg's #39 item stays separate on the tree | fixed |  | 2026-10-17T14:57:36.000Z | 2026-10-18T14:54:33.376Z |
| 36 | quick-261018-08g | deviation | tui/__main__.py |  | Esc-lag disposition (SOAK-2/F3 leg): the soak read lone-ESC modal dismissal as dead (modal up 1.5-4s); execution-time measurement in a clean 40x120 pty shows dismissal in 0.16-0.26s at the DEFAULT ESCDELAY and IDENTICAL at 30ms/10ms — ESCDELAY has no measurable effect, so no env mitigation landed in __main__.py (the plan's measure-first mandate); the soak's lag plausibly rode the same degraded-render family as F1 (now fixed); the pty lane pins esc-dismiss within a generous window, y/n remain the instant keys | waived | lone-ESC dismissal non-reproducing in clean pty (08g measure-first disposition; pty pin holds the window) | 2026-10-17T16:49:25.824Z | 2026-10-19T13:57:22.324Z |
| 37 | quick-261018-08g | deviation | tui/screens/run_config.py |  | Blank-screen-for-seconds-after-Enter (soak P5, tied to F5): NOT reproduced across two clean-pty planning probes AND the execution-time pty run — ProblemsModal/gate refusal copy renders within ~1.5s in a clean session (now pinned by the permanent pty lane's test_slot4_gate_refusal_is_visible); re-investigate only if it recurs AFTER the F1 fix lands, on the theory it was the same degraded-render family (F1 dominated every soak repro) | waived | blank-screen-after-Enter non-reproducing (soak P5/F5; pty pin test_slot4_gate_refusal_is_visible holds the window) | 2026-10-17T16:57:44.895Z | 2026-10-19T13:57:22.389Z |
| 38 | quick-261018-08g | deviation | docs/TUI-DEMO.md |  | Zellij scrollback compounding hypothesis (soak F6/P5): zellij 0.45.1 could not be driven from a bare pexpect pty (DCS handshake flood, 3 configs tried) so the scrollback-pause repro stays unverified in-harness; unchanged by the 261018-08g batch — F1 reproduces the exact reported symptoms in a clean pty and is now fixed; the maintainer's manual PageUp->Esc pass remains the standing note | waived | zellij compounding hypothesis not drivable in-harness; F1 root fixed, manual PageUp->Esc note stands | 2026-10-17T16:57:44.998Z | 2026-10-19T13:57:22.457Z |
| 39 | quick-261018-08g | deviation | tests/tui/__snapshots__/run_config.svg |  | run_config.svg regenerated (the F5 [m] picker-title hint changed the slot-4 title row — the only surface delta; the other 6 non-monitor SVGs regenerated byte-identical, and the 2 monitor goldens keep the uwr worktree shas) via make snapshot-update, deliberately UNCOMMITTED pending the maintainer's D-03 review — the WINDOWS #35 precedent; committed tree fails test_run_config_golden on exactly this file until it lands | fixed |  | 2026-10-17T17:07:04.679Z | 2026-10-18T14:54:33.445Z |
| 40 | quick-261018-feedback | unmet-truth | tui/screens/monitor.py |  | Slot-5 master-detail affordance: the two stacked tables (discovered sweep roots above, selected root's model-x-dataset cells below) read as peers rather than master-detail — no action-oriented titles, no selection echo, no drill guidance (maintainer: '上下半部分逻辑不好理解'). Batch with #40 next UX round: (a) action-oriented pane titles, (b) selected-root echo on the cells title, (c) consider single-tree merge | fixed | 261018-kvj: closed BY the redesign itself — the maintainer-approved (2026-10-18 15:01) two-tab contract replaces the master-detail dual table entirely (Running cards + History rows + per-run drill); no pane titles or selection echo remain to fix, the master-detail view is deleted | 2026-10-18T02:41:55.858Z | 2026-10-18T07:53:29.922Z |
| 41 | quick-261018-feedback | unmet-truth | tui/screens/monitor.py |  | #40 optimistic first paint: slot-5 entry with a live sweep waits ~3.5s for the scan worker before content (screen blank-but-responsive meanwhile) — render a skeleton + scanning header immediately, fill on worker completion | fixed | 261018-kvj: the mount composes the tab-header skeleton + the scanning note IMMEDIATELY (zero scan round-trips, zero fabricated rows); the first scan message clears the note and fills the tabs — Pilot-pinned (gated fake) and pty-pinned | 2026-10-18T02:41:55.929Z | 2026-10-18T07:53:29.992Z |
| 42 | quick-261019-f0x | deviation | tests/tui/__snapshots__/monitor_running.svg |  | monitor_running.svg AND monitor_empty.svg regenerated via make snapshot-update for the slot-5 B-skeleton + D-right-pane redesign (the summary strip + matrix + the ~40-col right pane changed the Running tab's render; the frozen-clock context manager _frozen_mon_clock pins the ETA wall clock for the export window), deliberately UNCOMMITTED pending the maintainer's D-03 review — the WINDOWS #35/#39 precedent; the committed tree fails test_monitor_running_golden + test_monitor_empty_golden on exactly these two files until the review lands; the other 7 goldens regenerated byte-identical | fixed |  | 2026-10-19T00:00:00.000Z | 2026-10-19T19:57:00+08:00 |

````json
[
  {
    "id": 1,
    "kind": "stub",
    "phase": "01",
    "file": "AUDIT.md",
    "line": 132,
    "description": "Secret-scan evidence section is an intentional placeholder filled by plan 01-03 task 3 (REL-05 gitleaks run)",
    "status": "waived",
    "reason": "gitleaks evidence landed in 01-SECURITY.md (plan 01-03 task 3, REL-05)",
    "recorded_at": "2026-10-08T14:33:35.112Z",
    "resolved_at": "2026-10-19T13:57:22.521Z",
    "milestone": "v0.7.1"
  },
  {
    "id": 2,
    "kind": "stub",
    "phase": "4",
    "file": "pipeline/models_info.json",
    "line": null,
    "description": "Chaoba card: series/architecture/context_len/species/type/huggingface/modelscope are empty-string (no locatable upstream page) — 04-04",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-10T03:13:03.112Z",
    "resolved_at": null,
    "milestone": "v0.7.1"
  },
  {
    "id": 3,
    "kind": "stub",
    "phase": "4",
    "file": "pipeline/models_info.json",
    "line": null,
    "description": "Chaoba_all_species card: series/architecture/context_len/species/type/huggingface/modelscope are empty-string (no locatable upstream page) — 04-04",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-10T03:13:03.177Z",
    "resolved_at": null,
    "milestone": "v0.7.1"
  },
  {
    "id": 4,
    "kind": "stub",
    "phase": "4",
    "file": "pipeline/models_info.json",
    "line": null,
    "description": "Chaoba_denseMamba card: series/architecture/context_len/species/type/huggingface/modelscope are empty-string (no locatable upstream page) — 04-04",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-10T03:13:03.243Z",
    "resolved_at": null,
    "milestone": "v0.7.1"
  },
  {
    "id": 5,
    "kind": "stub",
    "phase": "4",
    "file": "pipeline/models_info.json",
    "line": null,
    "description": "denseSSM_plant_genome card: series/architecture/context_len/species/type/huggingface/modelscope are empty-string (no locatable upstream page) — 04-04",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-10T03:13:03.337Z",
    "resolved_at": null,
    "milestone": "v0.7.1"
  },
  {
    "id": 6,
    "kind": "stub",
    "phase": "4",
    "file": "pipeline/models_info.json",
    "line": null,
    "description": "mamba2_370M card: series/architecture/context_len/species/type/huggingface/modelscope are empty-string (no locatable upstream page) — 04-04",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-10T03:13:03.403Z",
    "resolved_at": null,
    "milestone": "v0.7.1"
  },
  {
    "id": 7,
    "kind": "stub",
    "phase": "4",
    "file": "pipeline/models_info.json",
    "line": null,
    "description": "mamba2_plant_genome card: series/architecture/context_len/species/type/huggingface/modelscope are empty-string (no locatable upstream page) — 04-04",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-10T03:13:03.490Z",
    "resolved_at": null,
    "milestone": "v0.7.1"
  },
  {
    "id": 8,
    "kind": "stub",
    "phase": "4",
    "file": "pipeline/models_info.json",
    "line": null,
    "description": "prokbert card: series/architecture/context_len/species/type/huggingface/modelscope are empty-string (no locatable upstream page) — 04-04",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-10T03:13:03.577Z",
    "resolved_at": null,
    "milestone": "v0.7.1"
  },
  {
    "id": 9,
    "kind": "deviation",
    "phase": "4",
    "file": "tests/test_export_runs.py",
    "line": 466,
    "description": "D-15 evaluate cross-check covers the scipy-backed evaluate metrics (pearsonr/spearmanr) only — evaluate's accuracy/f1/mcc modules import scikit-learn, which is outside the sanctioned scipy+evaluate dependency pair; extending coverage needs a maintainer-approved scikit-learn addition",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-10-10T05:22:49.317Z",
    "resolved_at": "2026-10-19T13:57:22.133Z",
    "milestone": "v0.7.1"
  },
  {
    "id": 10,
    "kind": "unrun-verify",
    "phase": "05",
    "file": ".github/workflows/ci.yml",
    "line": null,
    "description": "First real GitHub-runner execution of ci.yml happens on the maintainer's next push (badge green + <15-min/job + branch-protection setup queued in 05-USER-SETUP.md)",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-10-10T10:04:38.260Z",
    "resolved_at": "2026-10-19T13:57:21.876Z",
    "milestone": "v0.7.1"
  },
  {
    "id": 11,
    "kind": "unrun-verify",
    "phase": "05",
    "file": "dnallm-mark/js/main.js",
    "line": null,
    "description": "05-02 Task 3 human-check (visual localhost confirmation of weighted default view, raw-rank toggle, stamped footer) deferred to the phase-level UAT gate — behavioral seams pinned by tests/js/main-view-toggle.test.js",
    "status": "waived",
    "reason": "05-02 weighted-default visual check confirmed at landing (behavioral seams pinned by js tests)",
    "recorded_at": "2026-10-10T10:52:34.776Z",
    "resolved_at": "2026-10-19T13:57:22.601Z",
    "milestone": "v0.7.1"
  },
  {
    "id": 12,
    "kind": "unrun-verify",
    "phase": "5",
    "file": "pipeline/run_finetune.py",
    "line": null,
    "description": "05-03: --subset_file seam + pipeline/eval_subsets.json consumption execute only at E2' (GPU, maintainer dual-gated); CPU-side stub/contract tests + real-artifact validation proof pin the behavior — first real GPU consumption pending launch",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-10-10T11:22:28.566Z",
    "resolved_at": "2026-10-19T14:56:56.393Z",
    "milestone": "v0.7.1"
  },
  {
    "id": 13,
    "kind": "deviation",
    "phase": "05",
    "file": "pipeline/sweep_priorities.json",
    "line": null,
    "description": "05-04 Task 4 blocking-human gate (tier-2 arena curation, D-17/OQ4): tier 2 shipped EMPTY at Task 2 awaiting maintainer decision — resolved 2026-10-10, maintainer selected per-arena one representative (animal GENERanno-eukaryote-0.5b-base / plant PlantCAD2-Small-l24-d0768 / microbe Omni-DNA-700M), landed in 6598e45",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-10-10T12:27:48.027Z",
    "resolved_at": "2026-10-10T12:27:53.830Z",
    "milestone": "v0.7.1"
  },
  {
    "id": 14,
    "kind": "deviation",
    "phase": "06",
    "file": "pipeline/env_smoke.py",
    "line": null,
    "description": "matmul expected constant corrected 64.0->512.0 (Rule 1, found by first executed smoke)",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-10-10T18:29:17.849Z",
    "resolved_at": "2026-10-19T13:57:21.940Z",
    "milestone": "v0.7.1"
  },
  {
    "id": 15,
    "kind": "deviation",
    "phase": "06",
    "file": "dnallm-mark/data/provenance.csv",
    "line": null,
    "description": "06-04 Task 4 blocking-human gate (maintainer provenance review, CONTEXT Area 2): execution paused at the gate with the Unspecified-default state committed — resolved 2026-10-11, maintainer selected 'reviewed 接受现状' (accept as-is; 35/7/9 Unspecified rows stand as honest unknowns), landed in c59f5f8",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-10-10T23:55:42.192Z",
    "resolved_at": "2026-10-10T23:55:51.180Z",
    "milestone": "v0.7.1"
  },
  {
    "id": 16,
    "kind": "deviation",
    "phase": "07",
    "file": "schemas/flops_report.json",
    "line": null,
    "description": "layer_details/total_flops_exact typed number not integer (Rule-1: verbatim Hyena FFT formula emits fractional FLOPs) — resolved, documented in 07-01-SUMMARY",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-10-11T06:45:51.224Z",
    "resolved_at": "2026-10-11T06:46:26.720Z",
    "milestone": "v1.2"
  },
  {
    "id": 17,
    "kind": "stub",
    "phase": "9",
    "file": "tui/screens/wizard.py",
    "line": 381,
    "description": "gauntlet phase renders a minimal pending view (title + 待检 line) — the real subprocess panel is 09-05's deliverable over the on_valid seam",
    "status": "fixed",
    "reason": "09-05 Task 1: the real gauntlet panel landed over the phase slot (async run-id-tagged rows, land-only-on-all-pass, drill-down); the minimal pending view remains only for the no-service construction",
    "recorded_at": "2026-10-12T04:54:51.935Z",
    "resolved_at": "2026-10-12T05:55:00.000Z",
    "milestone": "v1.2"
  },
  {
    "id": 18,
    "kind": "stub",
    "phase": "9",
    "file": "tui/screens/wizard.py",
    "line": 470,
    "description": "f binding routes to the on_import seam with no view behind it — the file-import view is 09-05's deliverable (planned functionality gap, D-11)",
    "status": "fixed",
    "reason": "09-05 Task 2: f routes to the import path prompt + per-entry sequential gauntlet with entry-level rollback (D-11 view behind the seam)",
    "recorded_at": "2026-10-12T04:54:57.893Z",
    "resolved_at": "2026-10-12T05:55:00.000Z",
    "milestone": "v1.2"
  },
  {
    "id": 19,
    "kind": "stub",
    "phase": "9",
    "file": "tui/screens/wizard.py",
    "line": 475,
    "description": "o binding routes to the on_export seam with no view behind it — the registry-export view is 09-05's deliverable (planned functionality gap, D-11)",
    "status": "fixed",
    "reason": "09-05 Task 2: o routes to the empty-state-checked export path prompt + the verbatim registry copy (D-11 view behind the seam)",
    "recorded_at": "2026-10-12T04:54:57.963Z",
    "resolved_at": "2026-10-12T05:55:00.000Z",
    "milestone": "v1.2"
  },
  {
    "id": 20,
    "kind": "deviation",
    "phase": "11",
    "file": ".planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-07-SUMMARY.md",
    "line": null,
    "description": "GB10 smoke (SC5 execution half) pending maintainer run — procedure in 11-07-SUMMARY, not executor-executable (D-15)",
    "status": "fixed",
    "reason": "executed live 2026-10-13 (11-UAT.md status passed 2/2, maintainer-authorized bounded smoke incl. the E2'-blocks proof); artifacts re-read on disk by the 2026-10-16 refresh verifiers (finetuned-smoke/ both cells + trainer_state markers) — ledger row left open by bookkeeping oversight, closed 2026-10-16",
    "recorded_at": "2026-10-13T06:06:35.033Z",
    "resolved_at": "2026-10-13T00:00:00.000Z",
    "milestone": "v1.2"
  },
  {
    "id": 21,
    "kind": "unrun-verify",
    "phase": "12",
    "file": ".planning/phases/12-multi-gpu-orchestration-console-hardening/12-05-SUMMARY.md",
    "line": null,
    "description": "N=2 multi-GPU smoke (MGPU validation half) pending maintainer run on the OTHER machine — 9-step procedure in docs/multi-gpu.md + 12-05-SUMMARY, not executor-executable (D-05: this machine is dev/test only, single GPU)",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-13T13:38:34.565Z",
    "resolved_at": null,
    "milestone": "v1.2"
  },
  {
    "id": 22,
    "kind": "unmet-truth",
    "phase": "quick-261014-c2l",
    "file": "tests/test_schemas.py",
    "line": null,
    "description": "Full make-test gate blocked by 10 PRE-EXISTING base failures (5 schema/determinism pins stale after data commit 9e803ca, 5 root-user chmod persist-failure sims) — verified failing identically at base 8f3af3c; this task's own lanes + lint + typecheck + node(26) green (see deferred-items.md)",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-10-14T01:21:59.202Z",
    "resolved_at": "2026-10-19T13:57:22.004Z",
    "milestone": "v1.2"
  },
  {
    "id": 23,
    "kind": "deviation",
    "phase": "quick-261014-dcl",
    "file": "tests/tui/__snapshots__/wizard.svg",
    "line": null,
    "description": "wizard.svg golden collateral drift: the wizard golden pins env-screen pixels at its left edge, so the 261014-dcl eighth env row drifted it (committed with the change per D-03; the plan pinned exactly four SVG diffs)",
    "status": "fixed",
    "reason": "absorbed by the D-03-approved full golden refresh (d5cb44b, 2026-10-15): wizard.svg regenerated with the other 8 goldens and committed under maintainer review",
    "recorded_at": "2026-10-14T03:38:33.288Z",
    "resolved_at": "2026-10-15T06:45:36.321Z",
    "milestone": "v1.2"
  },
  {
    "id": 24,
    "kind": "deviation",
    "phase": "quick-261014-f4w",
    "file": "tests/tui/__snapshots__/wizard.svg",
    "line": null,
    "description": "wizard.svg golden collateral drift again during make snapshot-update (render-state flake documented in dcl deferred-items, ~2/17 loads, pre-existing at base): committed with the change per D-03 alongside the plan-pinned run_config.svg + env_check.svg",
    "status": "fixed",
    "reason": "absorbed by the D-03-approved full golden refresh (d5cb44b, 2026-10-15); the render-state flake itself stays documented in dcl deferred-items",
    "recorded_at": "2026-10-14T05:14:07.356Z",
    "resolved_at": "2026-10-15T06:45:36.243Z",
    "milestone": "v1.2"
  },
  {
    "id": 25,
    "kind": "deviation",
    "phase": "quick-261014-mlc",
    "file": "tests/tui/test_snapshots.py",
    "line": null,
    "description": "All 9 SVG goldens strict-xfail pending maintainer make snapshot-update + D-03 review (slot-2/3 rework + locked nav rename)",
    "status": "fixed",
    "reason": "maintainer D-03 review approved 2026-10-15; all 9 goldens regenerated via make snapshot-update (zh pin) and committed in d5cb44b with the strict-xfail markers retired; suite at the 7F baseline with the 9 goldens passing",
    "recorded_at": "2026-10-14T10:25:24.246Z",
    "resolved_at": "2026-10-15T06:45:17.867Z",
    "milestone": "v1.2"
  },
  {
    "id": 26,
    "kind": "unmet-truth",
    "phase": "quick-261015-pex",
    "file": "tui/app.py",
    "line": null,
    "description": "Post-second-launch console input death (pex rehearsals): after a SECOND in-session gated launch the console stops processing navigation while renders continue (the launch toast/auto-switch render late or never); the demo restructured to exactly one on-camera launch and the fast-failure sweep moved to CLI prep",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-10-15T23:59:00.000Z",
    "resolved_at": "2026-10-19T14:22:50.525Z",
    "milestone": "v1.2"
  },
  {
    "id": 27,
    "kind": "unmet-truth",
    "phase": "quick-261015-pex",
    "file": "tui/screens/monitor.py",
    "line": null,
    "description": "Monitor stalls ~60s after a TUI launch on this box (around the first cell's completion output burst): the stats cadence stops and keys stop processing; the fold-then-kill demo sequence (seed 42 completes, kill seed 43) is unreachable - the demo kill lands mid-seed-42",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-10-15T23:59:00.000Z",
    "resolved_at": "2026-10-19T14:22:50.589Z",
    "milestone": "v1.2"
  },
  {
    "id": 28,
    "kind": "unmet-truth",
    "phase": "quick-261015-pex",
    "file": "tui/screens/run_config.py",
    "line": 1618,
    "description": "Typing into the slot-4 filter while the screen is mid-mount crashes the console: on_input_changed -> _render_picker -> query_one('#cfg-picker') raises NoMatches (observed once in pex rehearsal; the demo driver works around it by anchoring the populated picker before typing)",
    "status": "waived",
    "reason": "not reproducible in 12 aggressive tries (2026-10-19); structural closure verified: entries-empty guard before _render_picker, fresh RunConfigScreen per navigation, digits cannot navigate while filter focused. Latent unguarded query_one family in run_config.py event handlers noted — real fix only if entries ever load synchronously or screens get cached",
    "recorded_at": "2026-10-15T23:59:00.000Z",
    "resolved_at": "2026-10-19T14:22:50.654Z",
    "milestone": "v1.2"
  },
  {
    "id": 29,
    "kind": "deviation",
    "phase": "quick-261016-vxr",
    "file": "tests/tui/__snapshots__/monitor_running.svg",
    "line": null,
    "description": "monitor_running.svg AND monitor_empty.svg regenerated (the slot-5 [k] 停止 keycap row) via make snapshot-update, deliberately UNCOMMITTED pending the maintainer's D-03 review - the committed tree fails test_snapshots on exactly these two until they land (run_config.svg byte-preserved, sha256 afa89e7e...)",
    "status": "fixed",
    "reason": "D-03 review approved 2026-10-17; the three SVGs landed in f2a772a",
    "recorded_at": "2026-10-17T00:00:00.000Z",
    "resolved_at": "2026-10-17T01:34:00.000Z",
    "milestone": "v1.2"
  },
  {
    "id": 30,
    "kind": "deviation",
    "phase": "quick-261017-eea",
    "file": "schemas/model_performance.json",
    "line": null,
    "description": "Rule-2 deviation (eea commit 9a83066): the 141 helixgen entries carry FLOPs empty-string where the schema demanded strict number — schema conformed to the sibling anyOf [number, const ''] shape (1 line) after verifying the  documents '' as the missing-value convention, all 13 sibling metrics already use anyOf, summarize is ''-safe, and no test pins FLOPs strictness; fabricating numbers forbidden",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-10-17T02:55:52.918Z",
    "resolved_at": "2026-10-19T13:57:22.196Z",
    "milestone": "v1.2"
  },
  {
    "id": 31,
    "kind": "deviation",
    "phase": "quick",
    "file": "pipeline/run_finetune.py",
    "line": 849,
    "description": "run_finetune sibling hard-index sites deliberately unfixed (07-CR-01 batch covered only the model-loop reads): :849 probe-branch row[Model_name], :1077 dataset-loop row[Dataset_name], :1322 row[length] — schema-legal minimal custom entries crash these paths; future maintainer-ruled batch (see 261017-klw-SUMMARY Maintainer Items)",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-10-17T07:36:01.293Z",
    "resolved_at": "2026-10-19T13:57:22.260Z",
    "milestone": "v1.2"
  },
  {
    "id": 32,
    "kind": "deviation",
    "phase": "quick-261017-mad",
    "file": "tests/tui/test_snapshots.py",
    "line": 944,
    "description": "test_monitor_running_golden load-timing flake (pre-existing, observed once at the 261017-mad pre-task baseline): the SVG terminal-id is an adler32 hash over every rendered segment, and one full-suite run under load rendered one differing segment; identical rerun green, module green 11/11 in isolation, all fixture data frozen — root cause a load-dependent refresh artifact at export time, not reproduced by 261017-mad changes",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-10-17T08:50:31.381Z",
    "resolved_at": "2026-10-19T13:57:22.067Z",
    "milestone": "v1.2"
  },
  {
    "id": 33,
    "kind": "unmet-truth",
    "phase": "quick-261017-mad-followup",
    "file": "tui/services/run_config.py",
    "line": null,
    "description": "Storage-overview ✗ semantics for lazily-created dirs: the cache_dir row renders the same red ✗ as a missing model/dataset root, but a nonexistent cache dir is the healthy never-written-yet state (HF creates it on first use) — misleading failure signal; consider a neutral glyph or an on-demand note for the cache row",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-10-17T09:02:07.464Z",
    "resolved_at": "2026-10-19T14:51:26.876Z",
    "milestone": "v1.2"
  },
  {
    "id": 34,
    "kind": "unmet-truth",
    "phase": "quick-261017-feedback",
    "file": "tui/screens/monitor.py",
    "line": null,
    "description": "Monitor status conflation: interrupted cells (dir + no trainer_state marker + no live process) render the same 运行/running state as genuinely-running cells — maintainer hit it reading finetuned-smoke history (PlantHelixSeek 10-16 kill + dnamamba 10-15 interruption both show ⠋ 运行). Needs a three-state derivation (done / running-with-live-process / interrupted) or at least a distinct interrupted glyph",
    "status": "fixed",
    "reason": "261017-uwr: the three-state derivation landed (live-matrix evidence via argv_matrix/probe + CELL_INTERRUPTED ⏸ glyph + live-on-top ordering + context header); the PlantHelixSeek/dnamamba residue now derives interrupted",
    "recorded_at": "2026-10-17T14:12:12.091Z",
    "resolved_at": "2026-10-17T14:57:36.000Z",
    "milestone": "v1.2"
  },
  {
    "id": 35,
    "kind": "deviation",
    "phase": "quick-261017-uwr",
    "file": "tests/tui/__snapshots__/monitor_running.svg",
    "line": null,
    "description": "monitor_running.svg AND monitor_empty.svg regenerated via make snapshot-update, deliberately UNCOMMITTED pending the maintainer's D-03 review (all 7 non-monitor SVGs sha256-identical). AMENDED 261018-kvj: the uwr worktree pair was SUPERSEDED by the two-tab redesign's regeneration — the CURRENT uncommitted bytes are the ONE combined D-03 monitor-golden handoff for both batches (uwr + kvj tabbed surface); run_config.svg's #39 item stays separate on the tree",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-10-17T14:57:36.000Z",
    "resolved_at": "2026-10-18T14:54:33.376Z",
    "milestone": "v1.2"
  },
  {
    "id": 36,
    "kind": "deviation",
    "phase": "quick-261018-08g",
    "file": "tui/__main__.py",
    "line": null,
    "description": "Esc-lag disposition (SOAK-2/F3 leg): the soak read lone-ESC modal dismissal as dead (modal up 1.5-4s); execution-time measurement in a clean 40x120 pty shows dismissal in 0.16-0.26s at the DEFAULT ESCDELAY and IDENTICAL at 30ms/10ms — ESCDELAY has no measurable effect, so no env mitigation landed in __main__.py (the plan's measure-first mandate); the soak's lag plausibly rode the same degraded-render family as F1 (now fixed); the pty lane pins esc-dismiss within a generous window, y/n remain the instant keys",
    "status": "waived",
    "reason": "lone-ESC dismissal non-reproducing in clean pty (08g measure-first disposition; pty pin holds the window)",
    "recorded_at": "2026-10-17T16:49:25.824Z",
    "resolved_at": "2026-10-19T13:57:22.324Z",
    "milestone": "v1.2"
  },
  {
    "id": 37,
    "kind": "deviation",
    "phase": "quick-261018-08g",
    "file": "tui/screens/run_config.py",
    "line": null,
    "description": "Blank-screen-for-seconds-after-Enter (soak P5, tied to F5): NOT reproduced across two clean-pty planning probes AND the execution-time pty run — ProblemsModal/gate refusal copy renders within ~1.5s in a clean session (now pinned by the permanent pty lane's test_slot4_gate_refusal_is_visible); re-investigate only if it recurs AFTER the F1 fix lands, on the theory it was the same degraded-render family (F1 dominated every soak repro)",
    "status": "waived",
    "reason": "blank-screen-after-Enter non-reproducing (soak P5/F5; pty pin test_slot4_gate_refusal_is_visible holds the window)",
    "recorded_at": "2026-10-17T16:57:44.895Z",
    "resolved_at": "2026-10-19T13:57:22.389Z",
    "milestone": "v1.2"
  },
  {
    "id": 38,
    "kind": "deviation",
    "phase": "quick-261018-08g",
    "file": "docs/TUI-DEMO.md",
    "line": null,
    "description": "Zellij scrollback compounding hypothesis (soak F6/P5): zellij 0.45.1 could not be driven from a bare pexpect pty (DCS handshake flood, 3 configs tried) so the scrollback-pause repro stays unverified in-harness; unchanged by the 261018-08g batch — F1 reproduces the exact reported symptoms in a clean pty and is now fixed; the maintainer's manual PageUp->Esc pass remains the standing note",
    "status": "waived",
    "reason": "zellij compounding hypothesis not drivable in-harness; F1 root fixed, manual PageUp->Esc note stands",
    "recorded_at": "2026-10-17T16:57:44.998Z",
    "resolved_at": "2026-10-19T13:57:22.457Z",
    "milestone": "v1.2"
  },
  {
    "id": 39,
    "kind": "deviation",
    "phase": "quick-261018-08g",
    "file": "tests/tui/__snapshots__/run_config.svg",
    "line": null,
    "description": "run_config.svg regenerated (the F5 [m] picker-title hint changed the slot-4 title row — the only surface delta; the other 6 non-monitor SVGs regenerated byte-identical, and the 2 monitor goldens keep the uwr worktree shas) via make snapshot-update, deliberately UNCOMMITTED pending the maintainer's D-03 review — the WINDOWS #35 precedent; committed tree fails test_run_config_golden on exactly this file until it lands",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-10-17T17:07:04.679Z",
    "resolved_at": "2026-10-18T14:54:33.445Z",
    "milestone": "v1.2"
  },
  {
    "id": 40,
    "kind": "unmet-truth",
    "phase": "quick-261018-feedback",
    "file": "tui/screens/monitor.py",
    "line": null,
    "description": "Slot-5 master-detail affordance: the two stacked tables (discovered sweep roots above, selected root's model-x-dataset cells below) read as peers rather than master-detail — no action-oriented titles, no selection echo, no drill guidance (maintainer: '上下半部分逻辑不好理解'). Batch with #40 next UX round: (a) action-oriented pane titles, (b) selected-root echo on the cells title, (c) consider single-tree merge",
    "status": "fixed",
    "reason": "261018-kvj: closed BY the redesign itself — the maintainer-approved (2026-10-18 15:01) two-tab contract replaces the master-detail dual table entirely (Running cards + History rows + per-run drill); no pane titles or selection echo remain to fix, the master-detail view is deleted",
    "recorded_at": "2026-10-18T02:41:55.858Z",
    "resolved_at": "2026-10-18T07:53:29.922Z",
    "milestone": "v1.2"
  },
  {
    "id": 41,
    "kind": "unmet-truth",
    "phase": "quick-261018-feedback",
    "file": "tui/screens/monitor.py",
    "line": null,
    "description": "#40 optimistic first paint: slot-5 entry with a live sweep waits ~3.5s for the scan worker before content (screen blank-but-responsive meanwhile) — render a skeleton + scanning header immediately, fill on worker completion",
    "status": "fixed",
    "reason": "261018-kvj: the mount composes the tab-header skeleton + the scanning note IMMEDIATELY (zero scan round-trips, zero fabricated rows); the first scan message clears the note and fills the tabs — Pilot-pinned (gated fake) and pty-pinned",
    "recorded_at": "2026-10-18T02:41:55.929Z",
    "resolved_at": "2026-10-18T07:53:29.992Z",
    "milestone": "v1.2"
  },
  {
    "id": 42,
    "kind": "deviation",
    "phase": "quick-261019-f0x",
    "file": "tests/tui/__snapshots__/monitor_running.svg",
    "line": null,
    "description": "monitor_running.svg AND monitor_empty.svg regenerated via make snapshot-update for the slot-5 B-skeleton + D-right-pane redesign (the summary strip + matrix + the ~40-col right pane changed the Running tab's render; the frozen-clock context manager _frozen_mon_clock pins the ETA wall clock for the export window), deliberately UNCOMMITTED pending the maintainer's D-03 review — the WINDOWS #35/#39 precedent; the committed tree fails test_monitor_running_golden + test_monitor_empty_golden on exactly these two files until the review lands; the other 7 goldens regenerated byte-identical",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-10-19T00:00:00.000Z",
    "resolved_at": "2026-10-19T19:57:00+08:00",
    "milestone": "v1.2"
  }
]
````
