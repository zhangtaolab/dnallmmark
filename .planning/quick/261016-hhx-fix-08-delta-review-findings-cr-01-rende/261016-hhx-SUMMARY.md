---
phase: quick-261016-hhx
plan: 01
subsystem: tui
tags: [i18n, code-review-fix, demo-assets, render-time-derivation]
requires:
  - "08-REVIEW.md findings (the c4j+ehc TUI delta review, d800613)"
provides:
  - "Render-time i18n: the L toggle and a persisted-zh boot render ONE language everywhere (every DataTable header, state vocabulary, keycap, wizard label, dir-picker field re-derives at call time)"
  - "The CR-01 structural pin (tests/tui/test_language_rederivation.py AST checker + positive control) + the L-toggle Pilot pin + the _kind_spec language pin"
  - "Registry injectivity in BOTH directions (the en->zh mirror tripwire beside the zh->en one)"
  - "Pure-zh demo casts/GIFs (10 scenes + language-toggle-en) with honest RECORDED.md rows"
affects:
  - "The parked 08→12 verification refresh chain (all five TUI phases were waiting on this landing)"
tech-stack:
  added: []
  patterns:
    - "module-frozen copy table -> render-time re-derivation function (the env_check/matrix pattern, now enforced by the AST pin)"
    - "dedicated keycap registry constants byte-equal to old split() projections (translatable by remap_binding_descriptions)"
key-files:
  created:
    - tests/tui/test_language_rederivation.py
  modified:
    - tui/strings.py
    - tui/screens/data_manager.py
    - tui/screens/selection.py
    - tui/screens/monitor.py
    - tui/screens/wizard.py
    - tui/screens/run_config.py
    - tui/screens/env_check.py
    - tui/app.py
    - tui/__main__.py
    - tui/services/settings.py
    - tui/services/download_queue.py
    - scripts/demo/record_tui_demo.py
    - docs/demo/RECORDED.md
    - docs/demo/casts/*.zh.cast + language-toggle-en.cast
    - docs/demo/gifs/*-zh.gif + language-toggle-en.gif
decisions:
  - "QUEUE_STATE_PENDING en is '◌ waiting' (NOT the reviewer's '◌ queued' — MON_STATE_QUEUED owns that en value with a different zh; the collision would just move)"
  - "WizardModal keeps ctor-frozen copy (the modal is pushed in the active language); the removed freeze was the module-level one"
  - "The demo driver derives matrix counts and download-state anchors live from the registry (never-hardcode is its own contract); zh recordings end in zh (no on-camera restore — the restore frames rendered the EN tables and violated the zero-en-header requirement; per-recording state dirs make the restore functionally unnecessary)"
metrics:
  duration: 172 min
  completed: 2026-10-16
actuals:
  tokens: 28399   # chars/4 over the py+md diff (the cast/gif re-record churn is asset replacement, not authored text)
  tasks: 4
  commits: 5       # measured: git rev-list --count e4422fc..HEAD at SUMMARY time
plan_head_before: e4422fc18cda80f7598fcb915a1a62a0cf387ef0
plan_head_after: 723e046   # the last code commit; the bookkeeping commit rides on top (5 total, measured)
status: complete
---

# Quick Task 261016-hhx: Fix 08 delta review findings (CR-01 + WR/IN cluster) + zh GIF re-record Summary

**One-liner:** Render-time i18n re-derivation closes CR-01 (one language everywhere after L or a persisted-zh boot), the WR/IN cluster lands with regression coverage in both registry directions, and all ten zh demo GIFs re-recorded as pure zh.

## What Changed (per finding, with evidence)

### CR-01 (critical) — commit f9528e3

Every module-frozen copy site converted to a call-time re-derivation
function; call-site shapes unchanged:

- `tui/screens/data_manager.py`: `_QUEUE_COLUMNS`/`_MISSING_COLUMNS`/
  `_FULL_COLUMNS`/`_STATE_CELLS` -> `_queue_columns()`/
  `_missing_columns()`/`_full_columns()`/`_state_cells()` (call sites:
  on_mount, `_render_missing`, `_render_presence_view` ×2,
  `_state_cell`)
- `tui/screens/selection.py`: `_MODEL_COLUMNS` -> `_model_columns()`
  (`_rebuild_rows`), `_QUEUE_STATE_CELLS` -> `_queue_state_cells()`
  (`_model_download_cell`)
- `tui/screens/monitor.py`: `_SWEEP_STATE_CELLS`/`_CELL_STATE_CELLS` ->
  `_sweep_state_cells()`/`_cell_state_cells()` (the CellDetailModal,
  discovered-row, and entries-row renders); the `[f]`/`[t]` keycaps now
  read the NEW `S.MON_FAILURES_KEYCAP`/`S.MON_LOG_KEYCAP` registry
  constants (byte-equal to the old `split()` projections in both
  languages — zh goldens byte-identical, and being registry values is
  what finally lets `remap_binding_descriptions` translate them)
- `tui/screens/wizard.py`: `QUIRK_FIELDS`/`MODEL_STEPS`/`DATASET_STEPS`
  -> `_quirk_fields()`/`_model_steps()`/`_dataset_steps()`;
  `KINDS` -> language-neutral `_KIND_NAMES` (ctor validation) +
  `_kind_spec(kind)` builder; `WizardModal.__init__` captures
  `self._kind_spec` once (ctor-frozen copy is the accepted modal
  semantics — the freeze removed was the module-level one)
- `tui/screens/run_config.py`: `_DIR_INPUT_FIELDS` ClassVar ->
  `_dir_input_fields()` (the ctrl+o picker title re-derives)
- `tests/tui/test_language_rederivation.py` (NEW): the AST pin (module/
  class-level registry captures banned outside the four sanctioned
  sites — nav `NAV_SLOTS`/`_NAV_SLOTS_LANGUAGE`, class-body `BINDINGS`,
  app `TITLE` — with a positive control), the L-toggle Pilot pin
  (headers/state cells equal FRESH module-attribute reads, never
  literals), and the `_kind_spec` language pin
- `EXPECTED_MON_CONSTANTS` gains both keycap names (the bidirectional
  MON_ inventory lock)

### WR-01 / WR-02 / WR-03 / IN-01 / IN-02 / IN-03 — commit 190d1c4 (+ 723e046 lint follow-up)

- **WR-01**: `WIZ_BACK_LABEL` en -> "Back a step" (APP_MODAL_BACK_LABEL
  owns "Back") and `QUEUE_STATE_PENDING` en -> "◌ waiting"
  (ENV_STATE_PENDING owns "◌ pending"). The new
  `test_registry_consistency_same_en_implies_same_zh` mirrors the zh->en
  tripwire (structured entries excluded) — injective in BOTH
  directions now. Value-choice note: the reviewer's example "◌ queued"
  was NOT used — `MON_STATE_QUEUED` (zh ◌ 排队) already owns that en
  value; adopting it would have moved the collision rather than fixed
  it. The wizard `b` binding description now translates to 上一步 on
  en->zh.
- **WR-02**: `enqueue_zenodo` (tui/services/download_queue.py:1579
  area) carries the sibling-lane WR-04 discipline — persist error ->
  `self._entries.pop()` + `ACTION_PERSIST_FAILED`; the z action's
  persist_failed branch toasts `QUEUE_PERSIST_FAILED_TOAST` with the
  bundle label at error severity and kicks nothing (the
  `_toast_enqueue_outcome` arm mirrored, not restructured — the label
  is not the raw outcome.key). Service test over a chmod-0o500 state
  rail (persist_failed + rollback + fresh-load-empty) + a screen-side
  toast Pilot test.
- **WR-03**: env_check `__init__` gains `_check_in_flight` +
  `_last_outcome`; `run_full_check` sets the flag at entry, the
  ACCEPTED `CheckRunComplete` stores the outcome triple and clears the
  flag; the on_mount tail is population-only by guard (landed results
  re-apply + cached outcome re-renders; in-flight leaves the rebuilt
  pending rows; only a first mount consults the cache/runs kernels).
  app.py's `_rerender_screen` docstring states the now-true contract.
  The gated-fake Pilot test proves the remount restarts zero kernels
  (kernel_queries stays 1), rows 0-2 keep their final glyphs, and the
  run completes + renders the verdict.
- **IN-01**: the `_live_percents`/`_live_speeds` stores moved BELOW the
  ignore guard in `apply_queue_progress`; the pops moved ABOVE the
  KIND_MODEL return in `apply_queue_event` — model keys cannot
  accumulate (tick stores nothing; a completion cleans pre-seeded
  residue; both unit-pinned).
- **IN-02**: `settings.LANGUAGE_FILE_NAME` is the one definition;
  `__main__` imports/re-exports it (the boot read +
  `tui_main.LANGUAGE_FILE_NAME` test reference unchanged); the toggle
  writes `settings.state_dir() / settings.LANGUAGE_FILE_NAME`. Grep
  pin: exactly one "language.json" literal in tui/ (docstring mentions
  reworded so the pin counts the literal alone).
- **IN-03**: `DL_ENQUEUE_PRESENT_TOAST` registered in the DL_ block
  (same values as the retired SEL_ twin); consumed at the slot-3
  present-row guard; the SEL_-prefixed name retired from strings.py
  and both inventory locks (EXPECTED_DL_CONSTANTS gains it,
  EXPECTED_SEL_CONSTANTS drops it, comment amended).

### Task 3 — zh GIF re-record — commit c76c315 (+ driver fixes)

All ten zh scenes + `language-toggle-en` re-recorded 2026-10-16, every
meta exit 0, real ModelScope downloads + the bounded GPU scenes
(plant-dnabert-6mer × iDNA_ABF__5mC, single-GPU serialized one at a
time; the EHC-3 guard never tripped — no live sweep). Verification:
zero "Row reconcile"/"n_audit baseline rows" occurrences across
`*-zh.cast`; the queue tables render 任务/状态/进度/行数对账; the
monitor scenes render 训练项 状态/失败清单/日志尾随; RECORDED.md rows
refreshed (11 rows dated 2026-10-16, real targets, no new degradation
hunks); docs/TUI-DEMO.md byte-untouched (it quotes none of the changed
words — verified by grep).

Rule-3 driver fixes the re-record exposed (scripts/demo/
record_tui_demo.py — the recording tool, not tui/ code):

1. The matrix-title anchor derived its counts from a hardcoded 59x50
   while the live config root carries the demo custom entry (merged
   view = 60) — the scan now reports `merged_models`/`merged_datasets`
   (official + landed customs) and the scene uses them.
2. The model-download claim anchor hardcoded the EN clipped prefix
   "downloadin" — the 10-15 zh cast matched it only because the live
   overlay word was frozen ENGLISH (the CR-01 bug on film). The anchor
   now derives BOTH languages' `QUEUE_STATE_DOWNLOADING` words.
3. The custom-entries toast anchors carried a trailing space before
   the key; the zh toast wraps exactly between the word and the key,
   so the pattern never appeared contiguously on the wire — the
   deterministic 20.5s failures (three attempts; also the 10-15 zh
   failure). The anchors now use the wrap-proof styled-span word.
4. zh recordings no longer restore the boot language on camera — the
   restore frames rendered the EN tables and put en-only header
   strings into the zh casts (all occurrences sat at 90-99% of the
   cast, interleaved with "Switched to English"). Per-recording state
   dirs (destroyed at teardown) make the restore functionally
   unnecessary.

The dataset reset lever for the download/rerun pair: with iPro-WAEL's
directory removed, the audit re-run marks it n_audit-missing, the
dataset-download recording downloads it back (reconcile 10581 rows),
and the four committed audit artifacts (`dnallm-mark/data/n_audit.json`,
`n_audit.csv`, `pipeline/eval_subsets.json`, `DATA.md`) are restored
via `git checkout` (left clean). The rerun scene then genuinely
retrains the failed seed to completion — the first rerun attempt (with
the dataset still missing) was DISCARDED and re-recorded because its
"1/1" anchor had matched a re-failed cell folded as terminal; the
committed recording retrains for real.

### Task 4 — gates, disposition, STATE row

- `make lint` green (two gate-caught fixes follow-up-committed as
  723e046: the DL_ import's alphabetical position, an unquoted
  annotation UP037)
- `make typecheck` green
- `make test`: **7 failed / 1808 passed** — EXACTLY the pinned
  baseline membership (test_determinism 1 + test_schemas 5 +
  test_services_run_config 1; all machine/environment-dependent,
  pre-existing — the run_config failure re-verified at HEAD before any
  edit) with the 10 new tests passing (4 rederivation + 1 injectivity
  mirror + 1 zenodo persist + 1 remount + 2 live-dict + 1 z-toast;
  1798P -> 1808P)
- `node --test tests/js/*.test.js`: **26/26**
- The 9 golden SVG tests green UNMODIFIED (test_snapshots in the Task-1
  verify run; no snapshot file touched)
- Disposition: the SEVEN rows CR-01/WR-01..03/IN-01..03 -> fixed with
  their fix-commit short hashes (f9528e3 for CR-01; 190d1c4 for the six
  WR/IN rows); IN-04 stays open (not in this review)
- STATE.md quick row appended (c76c315 cited)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Demo driver anchors drifted against the live box state**
- **Found during:** Task 3 (the re-record)
- **Issue:** the matrix-title anchor hardcoded 59x50 (merged view is
  60 with the live custom entry); the model-download claim anchor
  hardcoded the EN word (a frozen-en CR-01 artifact); the
  custom-entries toast anchor's trailing space never matched the zh
  wrap; the generic on-camera language restore put EN tables into the
  zh casts.
- **Fix:** the four surgical driver edits listed above (the driver's
  own contract: targets/anchors derive live, never hardcoded; the
  driver never edits tui/ source).
- **Files:** scripts/demo/record_tui_demo.py
- **Commit:** c76c315

**2. [Rule 3 - Blocking] dataset-download/rerun needed the audit reset lever**
- **Found during:** Task 3
- **Issue:** the committed n_audit marks nothing missing on this box
  today, so the console's missing list was empty (d enqueued nothing)
  and the fail sweep had no dataset to fail; the plan's "delete the
  dir" preparation alone no longer suffices (presence is n_audit-based,
  not dir-scan-based).
- **Fix:** audit re-run over the deleted dir (disk-accurate missing),
  record, `git checkout` the four committed audit artifacts; the rerun
  re-recorded only after the dataset was truly back.
- **Files:** (no repo files changed by the lever itself — restored
  byte-clean)

**3. [Rule 1 - Bug] Gate-caught lint nits**
- **Found during:** Task 4 (make lint)
- **Issue:** the DL_ import appended out of alphabetical order; a
  quoted annotation UP037 in env_check.
- **Fix:** commit 723e046.

### Plan-text slips (noted, not blocking)

- The Task-3 verify expected `grep -q "行数对账" rerun-from-failures-zh.cast`,
  but that scene lives on slot 5 (the monitor) and never carried the
  queue header — not at 10-15 either (0 occurrences in the committed
  cast). Its zh MONITOR headers verify instead (训练项 状态 28×,
  失败清单 40×, 日志尾随 29×). The substantive truth (zero en-only
  headers, pure zh) holds across all casts.
- The plan's Task-4 step 5 says "git push the branch" — NOT done: the
  orchestrator's instruction explicitly reserves the push ("Do NOT
  push — the orchestrator pushes").

## Evidence Index

- CR-01 RED->GREEN: the AST pin failed listing all twelve frozen sites
  pre-fix; green post-fix with only the four sanctioned allowlist
  entries. The Pilot toggle test failed on the frozen zh header
  pre-fix; passes reading fresh en values post-fix.
- WR-01 RED->GREEN: `test_registry_consistency_same_en_implies_same_zh`
  failed on both "Back" and "◌ pending" collisions pre-edit; green
  after.
- The zh cast purity greps (Task-3 verify block) all pass; the
  eleven `.meta-*.json` sidecars all carry exit_code 0.
- Gate baseline proof: the run_config failure reproduced at HEAD
  (e4422fc) via stash before any edit — machine-dependent
  (pipeline/logs exists on the dev box).

## Self-Check: PASSED

- tests/tui/test_language_rederivation.py exists (created)
- docs/demo/RECORDED.md rows dated 2026-10-16 (11)
- Commits f9528e3, 190d1c4, c76c315, 723e046 are ancestors of HEAD
  (verified via git log at write time)
