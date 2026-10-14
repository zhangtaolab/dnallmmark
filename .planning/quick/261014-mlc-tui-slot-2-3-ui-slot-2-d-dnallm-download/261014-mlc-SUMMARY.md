---
phase: quick-261014-mlc
plan: 01
subsystem: TUI slot 2/3 UI rework (models-only + datasets-primary) + the KIND_MODEL dnallm download lane
tags: [tui, slot-split, dnallm, modelscope, download-queue, selection, data-manager, nav]
requires:
  - "261014-l6h (pipeline/dnallm_compat.json + the L6H-04 download invocation + the dataset-root reroute seam)"
  - "261014-dcl (model_presence service + the full presence view)"
  - "the maintainer's locked 2026-10-14 slot-split rulings (.continue-here.md)"
provides:
  - "tui/services/registries.load_dnallm_compat — the ONE tolerant loader over the committed compat map (slot-2 pool filter + queue model channel share it)"
  - "DownloadQueueService KIND_MODEL lane — enqueue_model + resolve_model_channel + _models_base + the -I dnallm subprocess + landing normalization + the config.json done gate"
  - "Slot 2 as the models-only screen (适配/下载 columns, t pool toggle, d model download, manual-placement honesty)"
  - "Slot 3 as the datasets-primary screen (full list primary, queue-state overlay, demoted Zenodo 备选 line, w dataset wizard)"
  - "Nav labels 2 模型 / 3 数据集 (value-only; routing byte-identical)"
affects:
  - "every TUI screen's top bar (the label rename renders on all screens)"
  - "tests/tui/test_snapshots.py — all NINE goldens strict-xfail pending the maintainer's make snapshot-update + D-03 review"
  - "tui/strings.py inventory (DL_/QUEUE_ additions; SEL_ENQUEUE_LABEL retired, SEL_SWITCH_LABEL now slot-4-owned)"
tech-stack:
  added: []
  patterns:
    - "python -I -c FIXED_PROGRAM child calling dnallm download_model with a functools.partial-bound modelscope snapshot_download (cache_dir rides the partial) — the subprocess is the only place dnallm code runs"
    - "AST-based import guard (the program constant carries the child's own import lines as string data)"
    - "screen-side queue-state join: presence_rows x entries() in the same SnapshotLoaded message (no service change)"
key-files:
  created: []
  modified:
    - tui/services/registries.py
    - tui/services/download_queue.py
    - tui/screens/selection.py
    - tui/screens/data_manager.py
    - tui/app.py
    - tui/strings.py
    - tui/styles.tcss
    - tests/tui/test_services_registries.py
    - tests/tui/test_services_download_queue.py
    - tests/tui/test_pilot_selection.py
    - tests/tui/test_pilot_selection_custom.py
    - tests/tui/test_pilot_matrix.py
    - tests/tui/test_pilot_data_manager.py
    - tests/tui/test_snapshots.py
    - docs/TUI-GUIDE.md
decisions:
  - "Empty compat mapping == the degraded read (compat_unavailable): the committed map carries all 59 keys, so emptiness is the unreadable signal — never a verdict"
  - "An adapted verdict without a usable modelscope repo id reads not_dnllm_adapted — the verdict alone can never authorize a download"
  - "The model flip toast is its own constant (QUEUE_FLIP_TOAST_MODEL): a done model has no reconcile leg, so the dataset lane's 对账一致 wording must never render for it"
  - "SEL_FILTER_COUNT stays verbatim (slot 4's own readout); slot 2 gained SEL_FILTER_COUNT_POOLED — slot-4/5 surfaces untouched"
  - "SEL_SWITCH_LABEL retained (slot 4's picker m-flip owns it now); SEL_SCREEN_TITLE_DATASETS and SEL_ENQUEUE_LABEL retired (zero consumers)"
  - "d on a ◌ 未知 model row (no Model_path) is silent — no path to name, no channel to call (the state-row rule)"
  - "The full-list d present-toast check applies to the FULL view only; missing-view rows are missing by construction"
metrics:
  duration: 105 min
  completed: 2026-10-14
status: complete
actuals:
  tokens: 64827    # chars/4 over the realized 991f481..HEAD diff (259,308 chars)
  tasks: 3
  commits: 4       # MEASURED: git rev-list --count 991f481..HEAD
plan_head_before: 991f481fc48a9ff86cd9f658aef3528b7b319c4e
plan_head_after: a0fab7a4bbd98998a71602390ee1b16187ad6a8e
---

# Quick Task 261014-mlc: TUI Slot 2/3 UI Split — Slot 2 Models (dnallm download) + Slot 3 Datasets (primary) Summary

**One-liner:** the maintainer's 2026-10-14 slot split landed end-to-end — a KIND_MODEL queue lane that downloads models through `dnallm.models.model.download_model` with a partial-bound ModelScope snapshot downloader (live-proven on DNABERT-2-117M, nesting normalized so config.json lands directly in the model dir), slot 2 reworked to a models-only screen with 适配/下载 columns and honest manual-placement states, slot 3 promoted to the datasets-primary full list with the Zenodo line demoted to 备选, and the nav labels renamed 2 模型 / 3 数据集.

## Task 1 — Model download channel in the shared queue (MLC-01): TDD, 2 commits

### TDD record

**RED (f1e961e):** the new service/registries tests failed on the missing API only (AttributeError on `load_dnallm_compat` / `KIND_MODEL` / `enqueue_model` / `resolve_model_channel` / `_models_base`; the registries module failed at import); the 169 pre-existing queue tests stayed green.

**GREEN (7200011):** implementation below; `tests/tui/test_services_download_queue.py tests/tui/test_services_registries.py tests/tui/test_import_lock.py` → 216 passed. `make lint` + `make typecheck` green.

### What landed

- **tui/services/registries.py — `load_dnallm_compat()`**: the ONE tolerant loader over the committed `pipeline/dnallm_compat.json` (module path constant `DNALLM_COMPAT_PATH` so tests monkeypatch one seam; `{}` on absent/corrupt/wrong-shape via the artifact_loader None sentinel). Pinned: exactly 59 keys == the official models registry key set, 36 adapted (11 modelscope-slot + 25 modelscope-mirror), every adapted entry carrying an allowlist-valid modelscope repo id.
- **tui/services/download_queue.py — the KIND_MODEL lane**:
  - `KIND_MODEL` + `ModelChannelSpec` (key/repo_id/landing/source_url/reason_code) + `resolve_model_channel` (registry `Model_path` joined onto `_models_base()` with the exact `model_presence` semantics — base trailing separator, Model_path keeping its `models/` prefix; verdict + repo id from the compat map).
  - `_models_base()`: constructor `model_root` param > `resolve_dirs(load_state()).model_root_abs` > the repo pipeline dir — **byte-identical to the selection presence chain** (pin test calls both expressions under a pinned state root; download landing and presence checking can never disagree about the root).
  - `enqueue_model` outcome order: already_queued (any state) > unknown_key > unknown/not_dnllm_adapted (incl. absent-while-loadable) > unknown/compat_unavailable > unknown/no_model_path > unknown/already_present (the defensive disk gate) > cli_unavailable (the CLI probe as the modelscope-package proxy) > persist_failed (rolled back) > enqueued.
  - `_run_model_download`: `[sys.executable, "-I", "-c", MODEL_DOWNLOAD_PROGRAM, landing, repo_id]` — the FIXED module-level program (the L6H-04 shape verbatim: `from functools import partial`, `from modelscope.hub.snapshot_download import snapshot_download`, `from dnallm.models.model import download_model`, `download_model(repo_id, downloader=partial(snapshot_download, cache_dir=landing))`); LIST argv, `start_new_session=True`, PIPEs, env exactly `dict(os.environ)`; percent stays None (dnallm logs carry no parseable percents); nonzero exit → `exit_<code>`; exit 0 → `_normalize_model_landing` (the single `models/<org>--<name>/snapshots/<rev>/` snapshot's children hoisted to the landing root, symlink entries skipped per T-qt-02, the `models/` subtree + `.lock/` removed; zero/multiple/empty snapshots or hoist collisions fail `model_nesting_ambiguous` honestly) then the done gate requires `config.json` DIRECTLY in the landing dir. NO reconcile leg (models are not n_audit subjects — the entry's reconcile stays None).
  - Boot resume rides the existing machinery (pin: a persisted pending KIND_MODEL entry survives `load()` and re-claims with its kind).
  - The module keeps the no-textual/no-dnallm/no-modelscope-import invariant: the raw-text modelscope scan moved to an AST scan (the program constant legitimately carries the child's own import lines as STRING data; dnallm joined the refused set).

### The machine-local live proof (L6H evidence discipline — never committed)

Sandboxed under /tmp (`DNALLMMARK_TUI_STATE_DIR` + `DNALLMMARK_TUI_CONFIG_DIR` + constructor `model_root=/tmp/mlc-proof/model-store`), one real `enqueue_model + run_task` cycle for **DNABERT-2-117M** (the smallest adapted slot model, `ZhejiangLab-LifeScience/DNABERT-2-117M`). Verbatim assertion output:

```
enqueue_model: enqueued
claimed: DNABERT-2-117M model
run_task: done problems: ()
details: ('exit_code=0', 'hoisted=.gitattributes', 'hoisted=LICENSE', 'hoisted=README.md', 'hoisted=bert_layers.py', 'hoisted=bert_padding.py', 'hoisted=config.json', 'hoisted=configuration.json', 'hoisted=configuration_bert.py', 'hoisted=flash_attn_triton.py', 'hoisted=generation_config.json', 'hoisted=pytorch_model.bin', 'hoisted=tokenizer.json', 'hoisted=tokenizer_config.json', 'removed=models', 'removed=.lock', 'landing=ok')
normalized landing children: ['.gitattributes', 'LICENSE', 'README.md', 'bert_layers.py', 'bert_padding.py', 'config.json', 'configuration.json', 'configuration_bert.py', 'flash_attn_triton.py', 'generation_config.json', 'pytorch_model.bin', 'tokenizer.json', 'tokenizer_config.json']
config.json bytes: 904
entry state: done reconcile: None
MLC LIVE PROOF OK: normalized landing holds config.json directly
```

12 files hoisted, scaffolding removed, config.json (904 B) direct in the landing dir, entry done with reconcile None. First-try pass; real-run artifacts stayed outside the repo (gitignored-class /tmp only).

## Task 2 — Slot 2 becomes the models-only screen (MLC-02): commit 1aaab93

- **SelectionData.compat** (additive, default `{}` keeps every Phase 8/9/10 fake conforming) populated by the real backend through the ONE loader; **the m toggle, the datasets table, `_DATASETS_VIEW`, `action_switch_list`, and the dataset d are gone** — the table is models-only with the column set 标 · 模型 · 类型 · 物种 · 规模(M) · **适配** · **下载** (budget 101 = widths 85 + 14 padding + 2 scrollbar; h-scroll below, 80x24 minimum intact; the backstop tests re-pinned to the 46-char longest model key `caduceus-ph_seqlen-131k_d_model-256_n_layer-16`).
- **The default pool**: dnllm-adapted officials + customs (customs always visible per the private-models-visible ruling); the **t** binding reveals ALL officials with unadapted rows marked 未适配 (dim) — never hidden data. The filter-count readout carries the pool segment (已适配/全部) via the new `SEL_FILTER_COUNT_POOLED`; the text filter composes AND over the active pool.
- **The 下载 vocabulary**: ✓ 已下载 / ✗ 未下载 (missing+adapted, the d-able state) / 手动放置 (missing unadapted-or-custom, muted — the honest private/no-source state) / ◌ 未知 (no Model_path/drift).
- **d = the model download** through `SelectionQueueBackend.enqueue_model` (the two-Protocol bridge gained the method): state rows silent; present → the honest already-downloaded toast; missing+adapted → enqueue with the full outcome-toast chain (enqueued+kick / already_queued / unknown-reason / cli_unavailable / persist_failed); manual-placement rows → `SEL_MODEL_MANUAL_TOAST` **naming the landing dir** (the effective model root joined with the row's Model_path — NEVER hf guidance, pinned by an explicit no-hf assertion); unknown-presence rows silent. A done KIND_MODEL event flips the row to 已下载 live through the existing `apply_queue_event` → reload path (Pilot-proven over the real backend with a staged model dir; the app's flip toast branches per kind — `QUEUE_FLIP_TOAST_MODEL`, honest no-reconcile wording).
- w/e act on the constant models kind; marks on datasets remain settable through presets (p) and template import (x) and still display in the matrix (v) and the status line — pinned unchanged.
- i18n: zero Chinese literals in the module (grep lock green); the dataset-wizard full loop moved out of this screen (successor surfaces: slot 3 w + the wizard suite); the dataset D-11 overlay proofs re-pinned as backend-snapshot assertions (the rendering surfaces are slot 3 / the matrix, pinned in their own suites).

## Task 3 — Slot 3 datasets-primary + nav labels + docs (MLC-03): commit a0fab7a

- **The pane promotion**: the FULL official dataset list is the primary top pane — key · 下载 · n_audit 基线行数 columns; the missing-only list is the v-toggled alternate (direction flipped from DCL-03; per-view column sets re-compose on render).
- **The queue-state overlay** (screen-side join over the entries snapshot in the same SnapshotLoaded message; no service change): a row with a live non-done entry renders the queue's own state word (待下载/下载中/失败/对账不一致) in its 下载 cell; a done entry reads ✓ 在场 through the merged presence (pinned per-state, incl. the done-exclusion).
- **d on the active pane**: a missing row enqueues the SAME per-dataset ModelScope channel (the default per the ruling — unchanged path/toasts); a present row gets the honest already-present toast (`SEL_ENQUEUE_PRESENT_TOAST`, now slot-3-owned); a/enqueue-all, r, x, g, enter all keep working over the new primary pane.
- **The Zenodo demotion**: the probe line moved from the missing-title row into the QUEUE title row (new `#dl-queue-title-row`), every line 备选-prefixed; z keeps its 备选 label.
- **w** opens the DATASET custom-entry wizard (lazy `CustomOnboardingBackend` composition inside the action; the snapshot reload wired as the land-completion callback; the injection seam Pilot-pinned).
- **Nav labels**: `NAV_LABEL_SELECTION` 模型·数据集 → **模型**, `NAV_LABEL_DATA` 数据管理 → **数据集** — value-only; the `ENV_ROUTE_MISSING_DATASETS` 前往数据管理 routing hint and its pins stay byte-identical per the locked ruling.
- **docs/TUI-GUIDE.md**: Quick-start, the slot table, Screen 2/3 sections, and the state-persistence note (model entries persist in download_queue.json, no reconcile leg) rewritten to the shipped surfaces.

### Full-suite gates (baseline accounting)

- `make lint` + `make typecheck` green; `make test-fast` green modulo the set below; `make test` → **1717 passed / 7 failed / 9 strict-xfail**, node lane **26/26**.
- The 7 failures are EXACTLY the documented l6h baseline: 5 test_schemas + 1 test_determinism (the documented pre-existing stale pins) + 1 `test_storage_overview_defaults_mirror_real_consumers` (the proven pre-existing machine-state failure vs the gitignored pipeline/logs leftovers). Nothing beyond — no new failures, no baseline "fixes".

## MAINTAINER-FACING ITEMS (the plan's mandatory SUMMARY flags)

1. **The stale SVG goldens — `make snapshot-update` + D-03 review pending.** ALL NINE committed goldens are strict-xfail in tests/tui/test_snapshots.py with the maintainer-ruling reason; `tests/tui/__snapshots__/` is byte-untouched. The plan named FOUR (selection_models, selection_datasets, data_manager, data_manager_presence — staled by the screen reworks); the LOCKED nav label rename additionally stales every top-bar-carrying golden (env_check, run_config, monitor_running, monitor_empty, wizard — verified: every committed SVG carries the `2模型`/`3数据` slot text). One `make snapshot-update` regenerates all nine; D-03 human-UAT review stays the gate. Recorded in the WINDOWS ledger.
2. **The reduced interactive task-marking surface.** Dataset marks can no longer be toggled interactively on slot 2 (no dataset table): they arrive via presets (p), template import (x), and the slot-4 picker; the mark sets, the status line (已标记: 模型 n/N · 数据集 m/M), and the matrix view are unchanged.
3. **The dataset-customs e-toggle surface gap.** `e` now toggles MODEL customs only (slot 2 is models-only); dataset custom entries have NO enable/disable surface anywhere in the console (the wizard's undo covers the just-landed case only). Flagged, not built — the plan scopes it out.
4. **The Task-1 live download proof: PASS** (output pasted above — normalized landing holds config.json directly, first try, no network failures).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] The plan's four-golden accounting undercounted the nav-rename blast radius**
- **Found during:** Task 2/3 gates (test_snapshots).
- **Issue:** the plan xfails exactly four goldens, but the LOCKED nav label rename (value-only, routing untouched) renders in EVERY screen's top bar — all nine committed SVGs carry the slot text, so five more goldens (env_check, run_config, monitor_running, monitor_empty, wizard) went stale beyond the documented baseline, breaking the "anything beyond is a NEW failure" gate.
- **Fix:** strict-xfail extended to all nine affected goldens with one maintainer-ruling reason (make snapshot-update + D-03 review); `__snapshots__/` untouched; recorded in the WINDOWS ledger. The alternative (leaving five red tests) would violate the task's own gates.

**2. [Rule 2 - Missing functionality] The model done-flip toast wording**
- **Found during:** Task 2 (app forward).
- **Issue:** the app-level QUEUE_FLIP_TOAST claims 下载完成且对账一致 for every done event — a lie for the model lane, which has no reconcile leg.
- **Fix:** `QUEUE_FLIP_TOAST_MODEL` ("✓ {key} 模型下载完成 — 下载列已更新") branched by entry kind; registered in the string inventory tripwire.

**3. [Rule 1 - Bug] The raw-text modelscope import guard false-positived on the program constant**
- **Found during:** Task 1 GREEN.
- **Issue:** the program string legitimately contains `from modelscope...` as subprocess data; the source-text scan flagged it.
- **Fix:** the guard moved to an AST Import/ImportFrom scan (stronger — catches aliased imports; dnallm added to the refused set).

**4. [Rule 3 - Blocking] SEL_FILTER_COUNT is shared with the untouched slot 4**
- **Found during:** Task 2 gates (the run_config golden KeyError).
- **Issue:** adding {pool} to SEL_FILTER_COUNT broke slot 4's picker readout (slot 4/5 must stay untouched).
- **Fix:** SEL_FILTER_COUNT reverted verbatim; slot 2 gained its own SEL_FILTER_COUNT_POOLED.

**5. [Rule 1 - Bug] i18n grep-lock leaks in new docstrings/comments**
- **Found during:** Task 2/3 gates (the zero-Chinese locks on selection.py/app.py).
- **Issue:** my new docstrings/comments used the Chinese UI words; the locks scan the whole file.
- **Fix:** all copy moved to strings.py constants / English comment wording; locks green.

## Auth Gates

None.

## Known Stubs

None — no stub patterns introduced: the compat map, the KIND_MODEL lane, both screen reworks, and the docs are fully wired (live-proofen end-to-end for the model lane).

## Threat Flags

None beyond the plan's register — T-qt-01 (LIST argv, -I, FIXED program, start_new_session + killpg), T-qt-02 (normalization never follows symlinks out of the landing root, never executes card content), T-qt-03 (per-key verbatim logs + persisted state ride unchanged), T-qt-04 (the _models_base chain degrades tolerantly), T-qt-SC (no new packages; dnallm/modelscope stay machine-local; the DNALLM sibling untouched — `git -C ../DNALLM status --porcelain` clean at handoff) are all implemented and test-pinned.

## Self-Check: PASSED

- Files: tui/services/registries.py, tui/services/download_queue.py, tui/screens/selection.py, tui/screens/data_manager.py, tui/app.py, tui/strings.py, tui/styles.tcss, tests/tui/test_snapshots.py, docs/TUI-GUIDE.md — all FOUND (modified, committed)
- Commits: f1e961e, 7200011, 1aaab93, a0fab7a are ancestors of HEAD (git merge-base --is-ancestor verified via rev-list 991f481..HEAD == 4)
- docs artifacts (SUMMARY.md/STATE.md) intentionally uncommitted — the orchestrator owns the docs commit per the dispatch constraints
