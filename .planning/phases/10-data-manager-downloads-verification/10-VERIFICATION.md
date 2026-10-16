---
phase: 10-data-manager-downloads-verification
verified: 2026-10-16T07:23:52Z
status: passed
score: 5/5 must-haves verified
covered_files:
  - .planning/phases/10-data-manager-downloads-verification/10-01-PLAN.md
  - .planning/phases/10-data-manager-downloads-verification/10-01-SUMMARY.md
  - .planning/phases/10-data-manager-downloads-verification/10-02-PLAN.md
  - .planning/phases/10-data-manager-downloads-verification/10-02-SUMMARY.md
  - .planning/phases/10-data-manager-downloads-verification/10-03-PLAN.md
  - .planning/phases/10-data-manager-downloads-verification/10-03-SUMMARY.md
  - .planning/phases/10-data-manager-downloads-verification/10-04-PLAN.md
  - .planning/phases/10-data-manager-downloads-verification/10-04-SUMMARY.md
  - .planning/phases/10-data-manager-downloads-verification/10-05-PLAN.md
  - .planning/phases/10-data-manager-downloads-verification/10-05-SUMMARY.md
  - .planning/phases/10-data-manager-downloads-verification/10-06-PLAN.md
  - .planning/phases/10-data-manager-downloads-verification/10-06-SUMMARY.md
  - .planning/phases/10-data-manager-downloads-verification/10-07-PLAN.md
  - .planning/phases/10-data-manager-downloads-verification/10-07-SUMMARY.md
  - pipeline/directories_config.py
  - tests/tui/fixtures/modelscope_stderr_interrupted.txt
  - tests/tui/fixtures/modelscope_stderr_success.txt
  - tests/tui/test_pilot_data_manager.py
  - tests/tui/test_pilot_nav_shell.py
  - tests/tui/test_pilot_selection.py
  - tests/tui/test_pilot_selection_custom.py
  - tests/tui/test_services_download_queue.py
  - tests/tui/test_services_gauntlet.py
  - tests/tui/test_services_zenodo_bundle.py
  - tui/__main__.py
  - tui/app.py
  - tui/screens/data_manager.py
  - tui/screens/nav.py
  - tui/screens/selection.py
  - tui/services/download_queue.py
  - tui/services/env_check.py
  - tui/services/gauntlet.py
  - tui/services/registries.py
  - tui/services/run_config.py
  - tui/services/selection.py
  - tui/services/zenodo_bundle.py
  - tui/strings.py
  - tui/styles.tcss
covered_digest: "v3:sha256:14d6970a13313c546f6359327b302cde5de9db6c8c7068ff1cdc5f54d38059bf"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 5/5
  gaps_closed: []
  gaps_remaining: []
  regressions: []
advisory:
  - finding: "WR-01 (carried) — a failed KIND_MODEL download can flip the selection models 下载 column: model_presence gates on is_dir only (tui/services/selection.py:501+) while the model-lane done gate requires config.json (MODEL_DONE_MARKER)"
    category: other
    reason: "Carried forward unchanged through the c4j/ehc/a4f/hhx delta (model_presence re-read at this pass: still the is_dir seam). Model presence column is dcl/mlc scope layered after phase 10; models are not n_audit subjects; no phase-10 SC covers it. Disposition-open in 10-REVIEW-DISPOSITION.md"
    evidence_status: "code-read at this pass: is_dir seam intact at tui/services/selection.py:501"
  - finding: "IN-01 (carried) — z pressed during the mount probe-in-flight window fires DL_ZENODO_DISABLED_TOAST while _zenodo_state is still None (tui/screens/data_manager.py:640 init; the != PROBE_PUBLIC arm at :1300)"
    category: other
    reason: "Carried forward unchanged. Transient copy issue; SC4 reachability and never-silent behavior unaffected (a toast always fires). Disposition-open"
    evidence_status: "code-read at this pass: _zenodo_state init None at :640; the disabled arm fires for any non-public state including None"
  - finding: "IN-02 (carried) — ABOUT_MILESTONE_STAGE stale (names phase 9) in tui/strings.py:997-1000"
    category: other
    reason: "Carried forward (now bilingual via _t but the text still says 本相位: 9 / current: Phase 9). Cosmetic milestone metadata; no SC relevance. Disposition-open"
    evidence_status: "code-read at this pass: still 'delivered: Phases 7-8 · current: Phase 9'"
---

# Phase 10: Data Manager (Downloads & Verification) Verification Report — Convergence Re-Verification (Staleness Refresh, Round 4)

**Phase Goal:** Dataset gaps are closable in-session before launch — one-click ModelScope download driven by the registry's authoritative `download_url`, a persistent resumable queue, and row-count reconciliation against n_audit — so an env-check presence FAIL is always diagnosable and fixable from the console
**Verified:** 2026-10-16T07:23:52Z at HEAD 2e8dcfa (branch autorun)
**Status:** passed — 5/5 SCs hold at the refreshed HEAD; zero regressions from the c4j/ehc/a4f/hhx delta
**Re-verification:** Yes — staleness refresh. Prior pass 5/5 at HEAD 646bcd5 (2026-10-14T17:42:32Z, digest `v3:sha256:5a877ff9…`). Since then four quicks touched this phase's covered files: **c4j** (slot-2 live model-download surface + slot-3 dataset-only queue split), **ehc** (bilingual strings registry + live L language toggle + download speed on the slot-2/3 progress surfaces), **a4f** (env-screen cluster fixes), **hhx** (render-time i18n for data_manager's frozen structures + the zenodo persist-failure rollback). The delta on these exact files was code-reviewed by the scoped incremental review at `.planning/phases/08-tui-foundation-env-check-selection/08-REVIEW.md` (diff base 2341f1c — a superset diff covering everything since bdf4ea0); its disposition (08-REVIEW-DISPOSITION.md) records 7/8 findings fixed via a4f + hhx (CR-01 f9528e3, WR-01..03/IN-01..03 190d1c4), one cosmetic info item open (IN-04 filter-grammar degenerate tokens — outside phase-10 SCs).

**Method:** goal-backward re-verification of every SC chain against the CURRENT code on disk, focused on the delta axes; 324 green test executions by this verifier across five covered lanes (queue module, zenodo module, data-manager pilot, selection-custom pilot, golden snapshots); scoped ruff + ty; an independent AST import check; and the demo layer (quick-261015-pex casts, re-recorded pure-zh post-hhx in c76c315) as live corroboration of REAL ModelScope downloads through this exact data manager. Full suite NOT re-run per caller instruction — caller-provided known-good gates on this exact tree (source unchanged since): 1808 passed at exactly the pinned 7F baseline membership (test_determinism 1, test_schemas 5, test_services_run_config 1), node 26/26, ruff+ty green, 9 golden SVGs green.

---

## Goal Achievement

### Observable Truths

| # | Truth (ROADMAP SC) | Status | Evidence |
|---|--------------------|--------|----------|
| 1 | SC1 one-click download via registry `download_url`; on landing, presence flips to ✓ in the selection table AND the environment check | ✓ VERIFIED | **The CR-01 reroute and both flip halves survive the delta intact — re-proven at HEAD.** Chain code-read: `_datasets_base()` (download_queue.py:1211-1241) reads `run_config.resolve_dirs(run_config.load_state()).dataset_root_abs` per call, never memoized; the consumption side binds the SAME chain (env_check.py:182 `dirs = run_config.resolve_dirs(run_config.load_state())`, `_dataset_dirs` kernel on `dirs.dataset_root_abs`); `compose_argv` threads `--dataset_root` via `_abs_against_repo_root` (run_config.py:1159-1160); the reconcile staged `Dataset_path` absolutization joins against `self._datasets_base()` (download_queue.py:2548). Six landing legs live at :2204/:2233/:2409/:2480/:2548/:2998. Selection half: `SelectionBackend` builds presence over `reconciled_rows()` + `merge_presence` (selection.py:382-383), `apply_queue_event` refreshes on done (selection.py:1518), `d` enqueues through the shared service and calls `app.kick_download_queue()` (selection.py:1955); `merge_presence` overlays reconcile-PASS keys only — mismatch never flips (semantic 6, docstring-pinned). Data-manager half: `d` binding → `action_enqueue_cursor`; channel resolution reads the registry `download_url` first (R-01, untouched by the delta); ENV_ROUTE_MISSING_DATASETS keeps the `[3]` keycap hint (strings.py:286-292, bilingual `_t` form). Behavioral: the three `_cr01` agreement tests (:4145 spec-without-file, :4169 relative-file CWD≠repo, :4191 default control) plus `test_missing_datasets_flips_over_done_reconciled_entries_cr01` / `test_merged_audit_tasks_overlays_this_services_state_path_cr01` / `test_presence_rows_missing_set_equals_missing_datasets_keys_cr01` all green in this verifier's 202-pass queue lane. Live corroboration: `docs/demo/casts/dataset-download-en.cast` — REAL ModelScope download of iPro-WAEL_datasets__Promoter_R_capsulatus through this exact screen with queue percent + progress bar + rate, reconcile flip, queue-row drill-down (RECORDED.md:111). |
| 2 | SC2 queue persists across TUI exit/crash and resumes where it stopped after restart | ✓ VERIFIED | Persistence spine unchanged by the delta: state at `settings.state_dir()/download_queue.json` through `settings.atomic_write`, the credential-free 12-field `_ENTRY_FIELDS` set (:236-239), `load()` tolerant recovery (downloading→pending with `interrupted=true`, `.corrupt` sidecar + diagnostic). App spine re-read at HEAD: ONE shared `DownloadQueueService()` (app.py:470-471, constructor-injectable), the exclusive `@work(exclusive=True, thread=True)` driver loop (app.py:657) posting `QueueEventMessage`, `kick_download_queue` busy-guard (app.py:634), `boot_resume_queue` (app.py:755-767) scheduled by `tui/__main__.py:100` (`app.call_later(app.boot_resume_queue)` BEFORE `run`). Behavioral: restart-resume end-to-end + interrupted downgrade + QUEUE_RESTART_NOTE rows in the 202-pass queue lane; `test_boot_resume_rehydrates_and_kicks_once` and `test_boot_resume_without_pending_never_kicks` green in the 61-pass data-manager pilot lane. |
| 3 | SC3 every landed download reconciles rows vs n_audit; mismatches prominent, never silently accepted | ✓ VERIFIED | Reconcile kernel intact under the delta: candidate-only temp registry with ABSOLUTE `Dataset_path` joined against the rerouted base (:2548), inert temp datasets-root, temp outputs, empty-overlay env; `merge_presence` overlays done keys only; mismatch state carries declared/measured and NEVER auto-deletes (D-07). Presentation re-read at HEAD: `_render_banners` mounts one `QUEUE_BANNER_MISMATCH` block per number-carrying mismatch (newest last; KIND_MODEL explicitly excluded), `_sorted_entries` sorts mismatch+failed to the top; `_reconcile_cell` renders pass/running/mismatch. Behavioral: `test_mismatch_banner_block_and_sort_to_top` green (61-lane); the real-subprocess reconcile pair, `test_committed_artifacts_byte_unchanged_across_real_reconcile_run`, and `test_reaudit_argv_exactly_interpreter_and_script_no_flags` green in the 202-pass lane. The g re-audit stays the explicit-only worktree path (R-03). |
| 4 | SC4 Zenodo bulk bundle (record 19135551, once public) reachable as alternate whole-package entry | ✓ VERIFIED | Constants intact (zenodo_bundle.py:50-59: `ZENODO_RECORD_ID = "19135551"`, frozen `ZENODO_API_URL`, PROBE_PUBLIC/NOT_PUBLIC/FAILED); the screen's four-state `_render_zenodo_line` (probing dim / not-public HH:MM / public ✓ actionable / failed ⚠) plus the Zenodo line in the missing-section title row. `action_zenodo_bundle`: z enqueues only when `PROBE_PUBLIC`, otherwise the never-silent `DL_ZENODO_DISABLED_TOAST`; the hhx WR-02 fix added the persist-failure rollback on the bundle lane (download_queue.py:1580-1589: `_persist_locked()` failure pops the appended entry and answers `ACTION_PERSIST_FAILED` — no ghost row) with its error-toast arm on the screen. Behavioral: 23 zenodo-module tests green; `test_z_enqueues_only_when_public_never_silent_otherwise` (61-lane) and `test_enqueue_zenodo_persist_failure_refused_no_ghost_row` (202-lane, the chmod-0o500 pattern) green. The queue pane keeps the bundle row while filtering KIND_MODEL (`_sorted_entries`) — the bundle is the dataset lane's alternate by design. |
| 5 | SC5 subprocess/thread-worker discipline (console never freezes); zero credentials stored or echoed | ✓ VERIFIED | Popen discipline re-read at HEAD: LIST argv + `start_new_session=True` + PIPEs + `env=dict(os.environ)` at download_queue.py:1846 and :2006 (dataset + model lanes); the exclusive thread-worker driver + kick busy-flag guard (app.py:657/:634) keep the console free. Zero modelscope imports: this verifier's own AST walk of download_queue.py returns zero Import/ImportFrom nodes naming modelscope (the :227 textual hit is inside `MODEL_DOWNLOAD_PROGRAM` — the FIXED `-c` child program string, argv data, never a module import); `test_service_module_never_imports_modelscope` green (202-lane). Credential surface: `_ENTRY_FIELDS` is exactly the 12-field credential-free set; env is passed through with zero overrides (credentials stay the CLI's own ~/.modelscope). Delta additions conform: `parse_speed` (EHC-4) returns the rate token verbatim as data, and the model-lane `progress_cb` threading (C4J-1) rides the same pump discipline. |

**Score:** 5/5 truths verified (0 present-but-behavior-unverified).

### The delta's interaction with the SC chains (checked, disjoint or additive)

1. **c4j slot-2/3 split vs SC1-SC4 surfaces** — the split is a PRESENTATION restructure: slot 3's queue pane renders dataset-side entries only (`_sorted_entries` filters `KIND_MODEL`; the bundle row stays), the model-download surface moved to slot 2 (selection models table with the live download overlay). Every phase-10 SC surface survives on slot 3: missing-datasets list, five-state queue glyphs (◌ ⠋ ✓ ✗ ⚠), progress cells (now with verbatim rate tokens), reconcile cells, mismatch banners + sort-to-top, drill-down modal (RichLog: full key, registry URL, LIST argv, reconcile numbers, verbatim log), Zenodo line, d/r/x/a/enter/g/z bindings, `below_minimum_grid` modal guards (:1240/:1282/:1349).
2. **ehc bilingual strings vs the DL_/QUEUE_ contract** — the single home survives as module attributes: 57 `DL_`/`QUEUE_` constants defined via `_t(key, zh, en)` in strings.py (:1010-1142+), consumed as `S.<CONST>` by data_manager/selection; the ENV_ROUTE `[3]` amendment is byte-stable in both languages. No second copy-home exists (08-REVIEW IN-03 fixed the one SEL_ reuse).
3. **ehc speed parsing + c4j model-lane progress vs the engine** — purely additive to download_queue.py: `SPEED_RE`/`parse_speed` + the (percent, speed) pair dedupe on the dataset lane, and `_run_model_download` gaining best-effort percent/speed via the same closure (model lane, not an n_audit subject — no reconcile, done gate still config.json). `_finish` now carries the last-fired percent. The dataset landing/reconcile legs and `_datasets_base` are untouched by these additions (verified by diff read: the delta adds code around the legs, never inside them).
4. **hhx zenodo persist rollback vs SC2/SC4** — strengthens the persistence contract (the WR-04 rollback discipline extended to the bundle lane); tested green; no SC regression.
5. **a4f env_check cluster vs SC1's env conjunct** — the env-screen fixes (fail-close non-dict registry, guarded persist tail) sit on the env screen's registry/persist paths; the dataset_dirs kernel still binds the same `resolve_dirs(load_state())` chain, so landing/consumption agreement (the CR-01 property) is undisturbed — pinned green by the three `_cr01` tests at HEAD.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tui/services/download_queue.py` | The phase engine: rerouted `_datasets_base`, six landing legs, reconcile kernel, Popen discipline, zenodo branch, credential-free schema | ✓ VERIFIED | 125-line delta since 646bcd5 is additive (speed parse, model-lane progress, zenodo rollback); reroute live at :1211-1241; legs at :2204/:2233/:2409/:2480/:2548/:2998; module lane 202 green |
| `tui/services/zenodo_bundle.py` | Four-state probe + guarded bundle driver (record 19135551) | ✓ VERIFIED | Constants :50-59 intact; 23 module tests green |
| `tui/screens/data_manager.py` | Slot-3 data-manager screen: two-pane layout, five-state glyphs, banners, drill-down, Zenodo line, d/r/x/a/enter/g/z | ✓ VERIFIED | All surfaces present post-c4j/ehc/hhx; Protocol backend + apply_queue_event/progress with the KIND_MODEL ignore-then-pop discipline (08-REVIEW IN-01 fix confirmed in code); 61 pilot tests green |
| `tui/app.py` | Shared queue service, exclusive driver worker, kick guard, boot resume, QueueEventMessage forward | ✓ VERIFIED | :430-471 seam, :634 kick, :657 worker, :755-767 boot resume; pilot lanes green |
| `tui/__main__.py` | D-06 boot path | ✓ VERIFIED | `app.call_later(app.boot_resume_queue)` at :100, before `run` |
| `tui/strings.py` | The DL_/QUEUE_ operator-copy single home (+ENV_ROUTE amendment) | ✓ VERIFIED | 57 module-attribute constants via `_t` bilingual registry; ENV_ROUTE `[3]` intact |
| `tests/tui/test_services_download_queue.py` | Three `_cr01` agreement tests + transition table + reconcile + persist-rollback + parse_speed lanes | ✓ VERIFIED | 202 passed in 0.63s at HEAD (was 195 — delta added persist-failure + parse_speed tests) |
| `tests/tui/test_services_zenodo_bundle.py` | Probe/bundle/never-silent lanes | ✓ VERIFIED | 23 passed in 0.12s |
| `tests/tui/test_pilot_data_manager.py` | Screen-tier Pilot proofs incl. mismatch banner, z-never-silent, boot resume, slot-3 geometry | ✓ VERIFIED | 61 passed in 16.81s |
| `tests/tui/test_pilot_selection_custom.py` | Selection d binding + overlay + toasts | ✓ VERIFIED | 27 passed in 8.79s |
| Golden snapshots (data_manager.svg, data_manager_presence.svg, …) | D-03-approved golden refresh (d5cb44b) matches current render | ✓ VERIFIED | Snapshot lane 11 passed in 6.22s — goldens green unmodified on this tree |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `DownloadQueueService._datasets_base()` | `run_config.resolve_dirs(run_config.load_state()).dataset_root_abs` | the same chain the env-check `dataset_dirs` kernel (env_check.py:182) and `compose_argv`'s `--dataset_root` (run_config.py:1159-1160) consume | ✓ WIRED | Code-read at HEAD + three green `_cr01` agreement tests in the 202-pass lane |
| `tui/app` shared service | driver worker → `QueueEventMessage` → `DataManagerScreen.apply_queue_event` / `SelectionScreen.apply_queue_event` + toasts | the 10-04/10-05 spine | ✓ WIRED | app.py:470-471/:657/:769; selection.py:1518; both pilot lanes green |
| `tui/__main__` | `app.boot_resume_queue` | `call_later` before `run` (:100) | ✓ WIRED | `test_boot_resume_rehydrates_and_kicks_once` green |
| `SelectionBackend` | `download_queue.reconciled_rows` + `merge_presence` → `registries.presence_for` | the D-11 overlay (pure read, no service instance) | ✓ WIRED | selection.py:382-383; overlay tests green in the queue + selection lanes |
| `tui/screens/nav` NAV_SLOTS slot 3 | `data_manager` target | `action_nav` routing (nav.py:87) | ✓ WIRED | slot 3 carries `S.NAV_LABEL_DATA` + target `data_manager`; nav-shell lane covered by caller's full-suite baseline (prior pass green; nav.py delta is label-source only) |
| `tui/screens/data_manager` | `download_queue` + `zenodo_bundle` (Protocol seam) → `S.` strings | service results only, screen computes nothing | ✓ WIRED | DataManagerServiceProtocol at :267-308; 61 pilot tests green |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `_datasets_base()` | `dirs.dataset_root_abs` | `run_config.load_state()` (spec seeded from directories.json) → `resolve_dirs` (REPO_ROOT-anchored) | ✓ | FLOWING — read per call, never memoized; `_cr01` tests pin landing/consumption agreement across all three configurations |
| `_render_missing` / `MissingSnapshot` | `snapshot.missing` / `rows` | `registries.load_n_audit` + disk scan through the Backend | ✓ | FLOWING — overlay tests + presence-rows `_cr01` test green |
| `_progress_cell` + `apply_queue_progress` | percent / speed | real stderr pump → `parse_progress`/`parse_speed` (last-token, verbatim) | ✓ | FLOWING — `parse_speed` trio green; demo cast shows live rate ticks |
| `_reconcile_cell` | declared/measured | the audit subprocess's temp n_audit.json verdict | ✓ | FLOWING — real-subprocess reconcile pair green |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|--------|---------|--------|--------|
| Queue module lane (3 `_cr01` + AST ban + reconcile + persist rollback + parse_speed + 190 others) | `.venv/bin/python -m pytest tests/tui/test_services_download_queue.py -q` | 202 passed in 0.63s | ✓ PASS |
| Zenodo module lane | `.venv/bin/python -m pytest tests/tui/test_services_zenodo_bundle.py -q` | 23 passed in 0.12s | ✓ PASS |
| Data-manager pilot lane (mismatch banner, z-never-silent, boot resume, slot-3 geometry, drill-down) | `.venv/bin/python -m pytest tests/tui/test_pilot_data_manager.py -q` | 61 passed in 16.81s | ✓ PASS |
| Selection-custom pilot lane (d binding, overlay, toasts) | `.venv/bin/python -m pytest tests/tui/test_pilot_selection_custom.py -q` | 27 passed in 8.79s | ✓ PASS |
| Golden snapshots incl. data_manager goldens | `.venv/bin/python -m pytest tests/tui/test_snapshots.py -q` | 11 passed in 6.22s | ✓ PASS |
| Zero modelscope imports (independent of the pinned test) | `.venv/bin/python -c "ast.walk …"` over download_queue.py | 0 Import/ImportFrom nodes naming modelscope | ✓ PASS |
| ruff (scoped to the 10 covered production + 3 covered test files) | `.venv/bin/python -m ruff check …` | All checks passed | ✓ PASS |
| ty (scoped to the covered production files) | `.venv/bin/python -m ty check …` | All checks passed | ✓ PASS |
| Debt markers (TBD/FIXME/XXX/TODO/HACK) over 10 covered production files | grep -n -E … | 0 hits across all files | ✓ PASS |

Full-suite note (caller-provided box evidence, not re-run here per instruction — single-lane discipline): 1808 passed at exactly the pinned 7F baseline membership (test_determinism 1, test_schemas 5, test_services_run_config 1), node 26/26, ruff+ty green, 9 golden SVGs green unmodified on this exact tree. This verifier's own five lanes (324 executions) are fully green at HEAD.

### Probe Execution

No probe scripts are declared for this phase (plans' verify blocks are pytest/make lanes) — N/A.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| DATA-01 | 10-01, 10-04, 10-05, 10-07 | One-click ModelScope download, registry `download_url` sole authority; presence flips in selection table AND env check | ✓ SATISFIED | SC1 row: chain code-read at HEAD + three `_cr01` agreement tests + overlay/flip tests green + real-download demo cast |
| DATA-02 | 10-01, 10-04, 10-06 | Persistent queue + resume across crash/restart | ✓ SATISFIED | SC2 row: persistence spine + boot path code-read; restart-resume and boot-resume tests green |
| DATA-03 | 10-02, 10-06 | Row-count reconciliation vs n_audit; mismatches prominent, never silent | ✓ SATISFIED | SC3 row: kernel + banner/sort presentation code-read; real-subprocess reconcile + banner tests green |
| DATA-04 | 10-03, 10-06 | Zenodo whole-package alternate entry (record 19135551) | ✓ SATISFIED | SC4 row: constants + four-state line + z semantics + persist rollback, 23 + named tests green |

No orphaned requirements (REQUIREMENTS.md maps exactly DATA-01..04 to Phase 10; all four marked Complete; every ID claimed in at least one plan's `requirements` frontmatter).

### Decision Coverage

`check.decision-coverage-verify --phase 10` returned `skipped` (reason: "CONTEXT.md missing" — the phase carries `10-CONTEXT.md`, which the verb's resolver does not match). Non-blocking gate; prior-pass coverage (16/16 honored) is unchanged in substance since the delta introduced no new decisions touching phase-10 D-rules.

### Anti-Patterns Found

None. Debt-marker greps (`TBD|FIXME|XXX`, `TODO|HACK`) return zero hits across all ten covered production files. No stub patterns, no empty implementations. The one textual `from modelscope…` hit (:227) is the FIXED subprocess child program (`MODEL_DOWNLOAD_PROGRAM` — argv data by design, AST-verified not an import).

### Advisory (Out-of-SC, carried forward)

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | WR-01 failed KIND_MODEL download → models 下载 column 已下载 (is_dir presence vs config.json done gate) | other | Reproduced earlier; re-read this pass — still the is_dir seam. Model presence column is dcl/mlc scope, no phase-10 SC covers it; disposition-open in 10-REVIEW-DISPOSITION.md |
| 2 | IN-01 z probe-in-flight window asserts the disabled toast as fact | other | Transient copy issue; SC4 reachability and never-silent behavior unaffected; disposition-open |
| 3 | IN-02 ABOUT_MILESTONE_STAGE names phase 9 (strings.py:997) | other | Cosmetic milestone metadata; no SC relevance; re-read this pass, still stale in both languages |

**Closed this round:** the prior pass's WR-02 (slot-3 drill-down renders `unknown_key` for healthy KIND_MODEL queue rows) is structurally moot after c4j — `_sorted_entries` filters `entry.kind != KIND_MODEL` from the slot-3 queue render (data_manager.py:493-503), so no model row is drillable there; the model surface lives on slot 2. Also noted: 08-REVIEW IN-04 (filter grammar degenerate tokens) remains open in that review's disposition — cosmetic, outside phase-10 SCs.

### Human Verification Required

None. Both prior live items remain discharged (10-UAT.md, 2026-10-13: the GB10 live smoke incl. the presence flip, and the `g` four-artifact check). This refresh's delta (c4j/ehc/a4f/hhx) was itself code-reviewed by the scoped 08 incremental review with 7/8 findings fixed (CR-01 + WR-01..03 + IN-01..03) and its golden refresh D-03-approved; the phase-10 SC behaviors are re-proven mechanically here (324 green executions incl. the agreement, flip, banner, boot-resume, z-never-silent, and persist-rollback tests), and the re-recorded demo layer (docs/demo/, post-CR-01 pure-zh c76c315) shows REAL ModelScope model + dataset downloads with percent/rate ticks, reconcile flip, and drill-down through this exact data manager — live corroboration on camera.

### Gaps Summary

None. The staleness trigger (four quicks touching six covered files) is fully cleared: the c4j split is presentation-only with every SC surface intact on slot 3; the ehc bilingual conversion preserves the DL_/QUEUE_ single-home contract (57 constants) and adds only additive parsed-data (speed); the hhx rollback strengthens the SC2/SC4 persistence discipline; the SC1 dataset chain (`_datasets_base` → `resolve_dirs(load_state())` → env kernel / compose_argv) is byte-stable in its semantics and pinned green by the `_cr01` agreement matrix; SC2-SC5 lanes all green; zero regressions.

### Fingerprint Refresh

`covered_files`/`covered_digest` in the frontmatter are the verbatim `verification.fingerprint` output at HEAD 2e8dcfa (supersedes `v3:sha256:5a877ff9…` of the 646bcd5 pass; identical file scope, new digest reflecting the c4j/ehc/a4f/hhx edits to download_queue.py, data_manager.py, app.py, __main__.py, selection.py, strings.py, styles.tcss, the covered test files, and the D-03-approved golden refresh).

---

_Verified: 2026-10-16T07:23:52Z (HEAD 2e8dcfa)_
_Verifier: Claude (gsd-verifier, convergence staleness refresh round 4)_
