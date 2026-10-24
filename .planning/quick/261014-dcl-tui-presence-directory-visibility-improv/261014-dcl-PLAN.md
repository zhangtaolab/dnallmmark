---
phase: quick-261014-dcl
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - pipeline/env_smoke.py
  - tui/services/env_check.py
  - tui/services/quick_check.py
  - tui/services/env_gate.py
  - tui/services/selection.py
  - tui/services/download_queue.py
  - tui/screens/env_check.py
  - tui/screens/selection.py
  - tui/screens/data_manager.py
  - tui/strings.py
  - tests/test_env_smoke_bytes.py
  - tests/tui/test_services_env_check.py
  - tests/tui/test_services_quick_check.py
  - tests/tui/test_services_env_gate.py
  - tests/tui/test_pilot_env_check.py
  - tests/tui/test_pilot_boot.py
  - tests/tui/test_services_selection.py
  - tests/tui/test_pilot_selection.py
  - tests/tui/test_services_download_queue.py
  - tests/tui/test_pilot_data_manager.py
  - tests/tui/test_snapshots.py
  - tests/tui/__snapshots__/env_check.svg
  - tests/tui/__snapshots__/selection_models.svg
  - tests/tui/__snapshots__/data_manager.svg
  - tests/tui/__snapshots__/data_manager_presence.svg
autonomous: true
requirements: [DCL-01, DCL-02, DCL-03]
user_setup: []

estimate:
  tokens: 145000
  raw_tokens: 80000
  tasks: 3
  confidence: med

must_haves:
  truths:
    - "DCL-01: the env-check screen renders an eighth row (kernel id model_dirs, label 模型目录) whose PASS/FAIL reflects live filesystem existence of every registry Model_path under the effective model root; both directory kernels annotate the effective root they actually checked; model_dirs failures are ROUTING (route signal only, never blocking can_launch)"
    - "DCL-01: both directory kernels resolve against the persisted run-config roots (settings.state_dir()/run_config.json read through run_config.load_state + resolve_dirs, absolute forms) when set and against the pipeline/ defaults byte-identically when unset; a missing/corrupt state file reads as defaults, never a crash"
    - "DCL-02: the selection screen's models table shows a live presence cell per model (✓ 已下载 / ✗ 未下载 / ◌ 未知) decided in tui/services/selection.py over each registry Model_path resolved against the effective model root; the DATASETS presence column (SEL-04) renders byte-identically to before"
    - "DCL-03: the data-manager screen toggles (key v) between the missing table and a full presence view listing every official dataset registry key with downloaded/missing status decided in tui/services/download_queue.py over the existing merged n_audit/reconcile view; the screen renders, never decides"
    - "make lint + make typecheck green; the full suite shows ONLY the 10 documented pre-existing failures (.planning/quick/261014-c2l-add-custom-model-dataset-storage-directo/deferred-items.md); affected SVG goldens regenerated via make snapshot-update and committed with the change"
  artifacts:
    - pipeline/env_smoke.py
    - tui/services/env_check.py
    - tui/services/quick_check.py
    - tui/services/env_gate.py
    - tui/services/selection.py
    - tui/services/download_queue.py
    - tui/screens/env_check.py
    - tui/screens/selection.py
    - tui/screens/data_manager.py
    - tui/strings.py
    - tests/tui/__snapshots__/env_check.svg
    - tests/tui/__snapshots__/selection_models.svg
    - tests/tui/__snapshots__/data_manager.svg
    - tests/tui/__snapshots__/data_manager_presence.svg
  key_links:
    - "run_config.load_state -> resolve_dirs(.model_root_abs/.dataset_root_abs) -> env_check.default_kernels root kwargs -> env_smoke.check_model_dirs/check_dataset_dirs(root=...) (the 261014-c2l verbatim-join semantics)"
    - "ENV_KERNEL_LABELS['model_dirs'] <-> env_check.default_kernels()['model_dirs'] <-> env_smoke.main() kernel order <-> quick_check.QUICK_CHECK_KERNEL_IDS <-> env_gate CRITICAL/ROUTING union (the one-sequence discipline, now eight ids)"
    - "SelectionBackend.load_selection_data -> selection_service.model_presence(entries, base) -> SelectionData.model_presence -> the models-table presence cell"
    - "DownloadQueueService.presence_rows -> merged_audit_tasks + registries.presence_for -> MissingSnapshot.presence_rows -> the #dl-missing toggle render"
    - "sweep_launcher env_preflight -> quick_check subset (now seven ids incl. model_dirs) -> env_gate ROUTING (model_dirs never blocks a launch)"
---

<objective>
Three operator-console presence/visibility improvements from the maintainer's manual verification session: (1) a model_dirs env-check kernel beside dataset_dirs with BOTH kernels aware of the persisted run-config storage roots; (2) a live download-state presence column in the selection screen's models table; (3) a toggleable full-dataset presence view in the data manager beside the missing table.

Purpose: after 261014-c2l, models/datasets can live under custom storage roots, but the console still shows presence against the pipeline/ defaults only — the env screen cannot see model directories at all, the models table renders a permanently-unknown presence cell (models are not n_audit subjects), and the data manager shows only the missing set, never the full picture.

Output: one new env_smoke kernel + root-aware service wiring (ROUTING, non-fatal), a service-decided live models presence column, a service-decided full presence view with a v toggle, strings inventory sync, tier-1/tier-2 tests in the same change, and the affected SVG goldens regenerated and committed.

External API declaration: No external API integration — local filesystem stat reads + the existing XDG state file only; no network, no subprocess, no new packages anywhere.
</objective>

<execution_context>
@~/.claude/gsd-core/workflows/execute-plan.md
@~/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/quick/261014-c2l-add-custom-model-dataset-storage-directo/261014-c2l-SUMMARY.md
@.planning/quick/261014-c2l-add-custom-model-dataset-storage-directo/deferred-items.md

@pipeline/env_smoke.py
@tui/services/env_check.py
@tui/services/env_gate.py
@tui/services/run_config.py
@tui/services/selection.py
@tui/services/registries.py
@tui/screens/env_check.py
@tui/screens/selection.py
@tui/screens/data_manager.py
@tui/strings.py
@tests/test_env_smoke_bytes.py
@tests/tui/test_snapshots.py
</context>

<assumption_delta_decision>
Transition detected (singular-hardcoded -> default-with-override): check_dataset_dirs currently resolves every registry Dataset_path against the import-time DATASETS_ROOT constant; this plan re-bases it onto an override-aware effective base. Decision: ADD-ALONGSIDE (the 261014-c2l precedent, not promote): the None branch joins the pipeline dir base with the registry value VERBATIM (value keeps its own datasets/ prefix), which resolves the exact same directories as today's removeprefix + DATASETS_ROOT form; the override branch activates only when the persisted run-config state file carries a root. The DATASETS_ROOT constant is retired; the default path it computed is preserved by the join expression. The golden scenarios S1/S3 prove path-equivalence on the default branch (only the annotation and the new model line differ). The new check_model_dirs kernel ships the same two-branch shape from day one.
</assumption_delta_decision>

<tasks>

<task type="tracer">
  <name>Task 1: model_dirs env kernel + run-config-aware roots end-to-end (slot 1)</name>
  <files>pipeline/env_smoke.py, tui/services/env_check.py, tui/services/quick_check.py, tui/services/env_gate.py, tui/screens/env_check.py, tui/strings.py, tests/test_env_smoke_bytes.py, tests/tui/test_services_env_check.py, tests/tui/test_services_quick_check.py, tests/tui/test_services_env_gate.py, tests/tui/test_pilot_env_check.py, tests/tui/test_pilot_boot.py, tests/tui/__snapshots__/env_check.svg</files>
  <behavior>
    - Kernel: check_model_dirs(root=None) over a synthetic registry reports all-present PASS with the root annotation; a missing Model_path dir yields the missing-count FAIL line plus one "  - {name}" listing line per missing key, in sorted-key order.
    - Kernel: check_dataset_dirs(root=None) on the default branch resolves the SAME directories as before the change (S1/S3 scenario shapes unchanged apart from the annotation); on the override branch it resolves base + verbatim Dataset_path (the models/--dataset_root semantics of 261014-c2l, prefix preserved).
    - Service: with a persisted run_config.json carrying model_root/dataset_root (DNALLMMARK_TUI_STATE_DIR pointed at tmp), default_kernels() binds the RESOLVED ABSOLUTE roots into both kernels; with no state file both kernels receive root=None.
    - Gate: a model_dirs failure sets route_to_data without touching can_launch; CRITICAL stays the six non-directory ids; CRITICAL and ROUTING union == the eight main()-order ids.
    - Screen: a model_dirs FAIL + dataset_dirs PASS run renders ENV_ROUTE_MISSING_MODELS with the listing-line count and NO ENV_ROUTE_MISSING_DATASETS line; a same-day cache hit whose persisted items cover only seven kernel ids reads as a cache MISS (full re-run).
  </behavior>
  <action>
    pipeline/env_smoke.py (the kernel home, D-02 single implementation):
    - Add module attr MODELS_INFO_PATH = PIPELINE_DIR / "models_info.json" beside DATASETS_INFO_PATH, and import os (needed for the join).
    - Add the shared helper _effective_base(root): returns str(PIPELINE_DIR) + os.sep when root is None, else str(root).rstrip(os.sep) + os.sep — the 261014-c2l run_finetune override-aware expression verbatim (pipeline/run_finetune.py:966-973 is the reference).
    - New kernel check_model_dirs(model_root=None) -> CheckResult: read MODELS_INFO_PATH; for each key in sorted order, expected path = _effective_base(model_root) + the entry's Model_path string (VERBATIM join — the registry value keeps its own models/ prefix, so the root is a pipeline/-equivalent base, exactly what run_finetune consumes); is_dir decides. Output shape mirrors check_dataset_dirs exactly: all-present headline PASS, or missing-count FAIL line plus one indented "  - {name}" line per missing key. Headline ALWAYS annotates the effective root: the stable literal " (root: pipeline/)" on the default branch (a fixed token, never the host-absolute path, so the byte goldens stay checkout-independent) and " (root: {the root string as given})" on the override branch. Google-style docstring; the kernel never prints (D-02).
    - Re-base check_dataset_dirs(dataset_root=None) onto the same helper: expected = _effective_base(dataset_root) + the entry's Dataset_path VERBATIM (replacing the removeprefix("datasets/") + DATASETS_ROOT / rel form); re-derive the double-nested sibling detection over the joined path (the fresh-unzip {suite}/{suite}/{task} note, same output wording); same always-annotate rule. Default-branch resolved directories are IDENTICAL to today — state this equivalence in the docstring and prove it via the S1/S3 goldens. Retire the DATASETS_ROOT module attr after grepping consumers (expect only env_smoke itself and its test; update all).
    - main(): render model_dirs immediately BEFORE dataset_dirs (models-before-datasets, the pinned argv-tail order of 261014-c2l), same append + _emit pattern; model/dataset dirs are not torch-gated. Update the module checkable-surface docstring (add the model-dirs item) and every "seven kernels/ids" wording in the file to eight, including the CheckResult.name attribute list.
    tui/services/env_check.py:
    - default_kernels(): read the persisted run-config roots through the 261014-c2l seams — dirs = run_config.resolve_dirs(run_config.load_state()) (import the sibling run_config service; no cycle: run_config imports only run_sweep + settings). Bind "model_dirs": env_smoke.check_model_dirs(root=dirs.model_root_abs) and rebind "dataset_dirs": env_smoke.check_dataset_dirs(root=dirs.dataset_root_abs), insertion order ..., "numpy", "model_dirs", "dataset_dirs". load_state is tolerant-by-contract (defaults on missing/corrupt -> both roots None -> kernel defaults); the *_abs forms are already absolute-or-None. Update the docstring kernel list and the run_full_check docstring.
    tui/services/quick_check.py: QUICK_CHECK_KERNEL_IDS gains "model_dirs" before "dataset_dirs" (now seven ids — all eight kernel ids except matmul); docstring "ALL seven kernel ids" -> all eight.
    tui/services/env_gate.py: ROUTING = frozenset({"model_dirs", "dataset_dirs"}); docstring: union == the EIGHT main()-order ids, ROUTING paragraph names both directory kernels; route_to_data attribute doc gains the model-dirs wording. CRITICAL unchanged (six ids).
    tui/strings.py: ENV_KERNEL_LABELS gains "model_dirs": "模型目录" immediately before "dataset_dirs" (comment "the seven env-check rows" -> eight). New ENV_ROUTE_MISSING_MODELS = "⚠ {n} 个模型目录缺失 — 模型需手动放置（[4] 运行配置可查看存储根）" (glyph-first ⚠; models have no CLI download command, so the wording must not promise one — it points at the run-config screen where the storage root is visible).
    tui/screens/env_check.py:
    - _render_check_outcome: mount ENV_ROUTE_MISSING_DATASETS only when the dataset_dirs result itself failed; mount ENV_ROUTE_MISSING_MODELS when the model_dirs result itself failed (per-kernel checks, not the route_to_data bool — model_dirs failures must not fabricate a zero-count datasets line). Generalize _missing_dataset_count to _missing_count(result) (the "  - " prefix-count idiom) used for both.
    - EnvCheckBackend.cached_results: coverage guard — after rebuilding the CheckResult list, a kernel-id set that differs from set(ENV_KERNEL_LABELS) returns None (cache miss): a pre-change same-day seven-item state file re-runs once and persists eight, instead of stranding the model_dirs row pending forever.
    - Module docstring "seven-row"/"seven rows" wording -> eight.
    Tests (same change):
    - tests/test_env_smoke_bytes.py: rework _run_scenario to pin env_smoke.PIPELINE_DIR at a synthetic tmp pipeline dir and place BOTH info files (pin MODELS_INFO_PATH + DATASETS_INFO_PATH module attrs into that layout) with materialized models/{a,b,c} dirs alongside the existing datasets fixtures; update EXPECTED_S1/S2/S3 (dataset line gains the " (root: pipeline/)" annotation; a model_dirs PASS line precedes it; S2 trailer count unchanged — model_dirs passes there). Add S4 as a KERNEL-level (not main()) test: check_model_dirs/check_dataset_dirs with an explicit override root over tmp dirs pin the override annotation, the verbatim join (root without trailing sep + "models/x" -> exactly one separator), and the missing listing. Update the module docstring scenario notes.
    - tests/tui/test_services_env_check.py: _patch_env_smoke_kernels fakes accept the root kwarg (def fake_dataset_dirs(root=None), plus fake_model_dirs(root=None)); the sequence and torch-gate order assertions gain model_dirs; NEW root-threading test: DNALLMMARK_TUI_STATE_DIR -> tmp, save_state a RunSpec with model_root/dataset_root set, recording fakes capture the kwargs and assert they equal run_config.resolve_dirs outputs (absolute); a no-state-file variant asserts both kwargs are None.
    - tests/tui/test_services_quick_check.py: the ids literal gains "model_dirs" (seven ids, matmul still excluded); rename/retire the "six non-matmul" naming.
    - tests/tui/test_services_env_gate.py: MAIN ids tuple gains model_dirs; ROUTING == {"model_dirs", "dataset_dirs"}; the disjoint-cover test moves to eight; NEW twin test: model_dirs failure routes without blocking.
    - tests/tui/test_pilot_env_check.py: _mixed_results gains a passing model_dirs entry (contract-shaped line) before the dataset FAIL; every seven-count assertion moves to eight (row_count sites, range(1, 7), the 6 downs to reach the last row -> 7, kernel_calls 7 -> 8 and 14 -> 16, state items 7 -> 8); NEW scenario: model_dirs FAIL + dataset_dirs PASS renders ENV_ROUTE_MISSING_MODELS with the count and no datasets routing line; add ENV_ROUTE_MISSING_MODELS to the glyph-first tuple; NEW backend test: a same-day persisted seven-item list reads as a cache miss.
    - tests/tui/test_pilot_boot.py: row_count == 7 -> 8 with the comment updated (the other ENV_KERNEL_LABELS-iterating Pilot fakes across test_pilot_nav_shell/wizard/monitor/selection adapt automatically — verify none hard-code seven).
    - Regenerate tests/tui/__snapshots__/env_check.svg via make snapshot-update (the eighth row); confirm git status over __snapshots__ shows ONLY env_check.svg.
  <verify>
    <automated>make lint && make typecheck && make snapshot-update && git status --porcelain tests/tui/__snapshots__/ && uv run --group dev --group tui pytest tests/test_env_smoke_bytes.py tests/tui/test_services_env_check.py tests/tui/test_services_quick_check.py tests/tui/test_services_env_gate.py tests/tui/test_pilot_env_check.py tests/tui/test_pilot_boot.py tests/tui/test_snapshots.py -q</automated>
  </verify>
  <done>Kernel-level and Pilot tests above green; make lint + make typecheck green; env_check.svg the only regenerated golden; the env screen carries an eighth 模型目录 row; both directory kernels annotate the effective root; model_dirs joins ROUTING and never blocks can_launch; quick check subset and env_gate union updated consistently (DCL-01).</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: live models presence column in the selection screen (slot 2)</name>
  <files>tui/services/selection.py, tui/screens/selection.py, tui/strings.py, tests/tui/test_services_selection.py, tests/tui/test_pilot_selection.py, tests/tui/test_services_download_queue.py, tests/tui/test_snapshots.py, tests/tui/__snapshots__/selection_models.svg</files>
  <behavior>
    - Pure function model_presence(entries, base_dir, is_dir=None): a Model_path whose dir exists under the join -> "present"; absent -> "missing"; an entry whose card carries no usable Model_path string -> "unknown"; join is verbatim (base rstrip os.sep + os.sep + value, the value's own models/ prefix preserved) so base_dir is a pipeline/-equivalent root.
    - Real backend: SelectionData.model_presence covers every model key in the merged+management view (official + custom, both enabled states); statuses stay within the three-value vocabulary on any machine (structure-only asserts — CI has no models/).
    - Run-config threading: with DNALLMMARK_TUI_STATE_DIR -> tmp holding a run_config.json with model_root set to an EMPTY tmp dir, every model reads "missing" deterministically on any machine.
    - Screen: the models-table presence cell renders ✓ 已下载 / ✗ 未下载 / ◌ 未知 from data.model_presence; the datasets-table presence cell (SEL-04 four-status vocabulary) renders byte-identically to before.
  </behavior>
  <action>
    tui/services/selection.py (the presence decision lives HERE, tier-1 tested; module stays registries-blind AND config-blind — entries and base arrive as parameters):
    - Add module constants MODEL_PRESENCE_PRESENT = "present", MODEL_PRESENCE_MISSING = "missing", MODEL_PRESENCE_UNKNOWN = "unknown" — the models-column machine vocabulary, deliberately distinct from the n_audit four-status vocabulary in registries.py (importing registries here would violate the module's decoupling contract).
    - Add pure function model_presence(entries, base_dir, is_dir=None) -> dict[str, str]: for each canonical entry, read entry["card"].get("Model_path"); a non-str/empty value maps to UNKNOWN; else full = str(base_dir).rstrip(os.sep) + os.sep + value (the 261014-c2l verbatim join) and status = PRESENT when is_dir(full) else MISSING. Default is_dir = the real filesystem check; the parameter is the test/injection seam. import os. Google-style docstring naming the join precedent (pipeline/run_finetune.py model_base + Model_path) and the PRESENTATION ONLY split (this service decides; the screen maps to words).
    tui/screens/selection.py:
    - SelectionData gains model_presence: dict[str, str] = field(default_factory=dict) (default keeps every Phase-8/9/10 fake conforming unchanged; update the dataclass docstring).
    - SelectionBackend.load_selection_data: AFTER the customs union completes (so custom models get statuses too), resolve the effective base — dirs = run_config_service.resolve_dirs(run_config_service.load_state()); base = dirs.model_root_abs or str(run_config_service.DEFAULT_REGISTRY_DIR) (the committed pipeline dir; the same path the launch would resolve against when no root is configured) — then model_presence = selection_service.model_presence(model_entries, base). Import the run_config service (no cycle; the backend is the wiring tier, mirroring where the registry read already lives).
    - Add render helper _model_presence_cell(data, key): PRESENT -> Text(SEL_MODEL_PRESENCE_PRESENT, _STYLE_PRESENCE_PASS); MISSING -> Text(SEL_MODEL_PRESENCE_MISSING, _STYLE_PRESENCE_FAIL); absent/other -> Text(SEL_PRESENCE_UNKNOWN, _STYLE_PRESENCE_UNKNOWN).
    - _row_cells: the models branch uses _model_presence_cell; the datasets branch keeps _presence_cell untouched (SEL-04 unchanged per the finding). The _MODEL_COLUMNS presence column (header 数据, width 20) stays as-is.
    tui/strings.py: SEL_MODEL_PRESENCE_PRESENT = "✓ 已下载", SEL_MODEL_PRESENCE_MISSING = "✗ 未下载"; update the SEL_PRESENCE_UNKNOWN comment (the "every real model key lands here" note is retired — for models, unknown is now the no-Model_path/drift state; datasets keep the n_audit drift meaning).
    Tests (same change):
    - tests/tui/test_services_selection.py: new tier-1 block over real tmp dirs — present (mkdir base/models/x), missing (absent dir), unknown (card without Model_path), the verbatim-join pin (base given without a trailing separator still yields exactly one separator), a second custom base pinning that the root is honored, and an is_dir-injection test (recording fake) proving the default seam is replaceable.
    - tests/tui/test_pilot_selection.py: _default_data fills model_presence mixed (one present, one missing, one unknown); the models-table presence assertions (currently pinning the unknown copy "the real backend fills presence per DATASET key only") flip to the new words; the datasets presence-cell tests stay byte-identical. Extend the real-backend test (test_backend_loads_the_committed_registries_and_presence) with structure-only asserts: set(model_presence) == the model keys, statuses within the vocabulary. NEW deterministic backend test: DNALLMMARK_TUI_STATE_DIR -> tmp + run_config save_state(RunSpec(models=(), tasks=(), model_root=str(empty_tmp))) -> load_selection_data().model_presence is all-"missing" on any machine.
    - tests/tui/test_services_download_queue.py: EXPECTED_SEL_CONSTANTS gains the two new SEL_ names (this file is the established SEL_ registration site; update its comment) — the one-directional defined-check covers them.
    - tests/tui/test_snapshots.py: _SelectionGoldenService._standard_data fills model_presence with fixed mixed values (deterministic regardless of machine).
    - Regenerate tests/tui/__snapshots__/selection_models.svg via make snapshot-update; selection_datasets.svg must stay byte-identical (the datasets view never renders model cells) — verify via git status over __snapshots__ showing ONLY selection_models.svg.
  <verify>
    <automated>make lint && make typecheck && make snapshot-update && git status --porcelain tests/tui/__snapshots__/ && uv run --group dev --group tui pytest tests/tui/test_services_selection.py tests/tui/test_pilot_selection.py tests/tui/test_services_download_queue.py tests/tui/test_snapshots.py -q</automated>
  </verify>
  <done>Tier-1 pure-function and Pilot tests green; the models table renders live per-model download state; the datasets presence column unchanged; the two new SEL_ constants registered in the IN-09 inventory tuple; only selection_models.svg regenerated (DCL-02).</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: data-manager full-dataset presence view with v toggle (slot 3)</name>
  <files>tui/services/download_queue.py, tui/screens/data_manager.py, tui/strings.py, tests/tui/test_services_download_queue.py, tests/tui/test_pilot_data_manager.py, tests/tui/test_snapshots.py, tests/tui/__snapshots__/data_manager.svg, tests/tui/__snapshots__/data_manager_presence.svg</files>
  <behavior>
    - Service: DownloadQueueService.presence_rows() returns one row per OFFICIAL dataset registry key (all 50 against the committed registry, registry file order), each status decided by registries.presence_for over merged_audit_tasks() (the same D-11 substrate as missing_datasets) and declared_total from the registry; the set of "missing" rows equals the missing_datasets() key set exactly; a done-reconciled key flips in both views together (CR-01); with the committed n_audit absent, keys still list with degraded statuses (overlay-present or unknown), never an exception.
    - Snapshot: MissingSnapshot carries presence_rows (default () so existing fakes conform); the real backend fills it from the queue service.
    - Screen: key v toggles the missing pane between the missing table (unchanged render) and the full view (title DL_PRESENCE_TITLE, one row per key with a ✓/✗/◌ status glyph prefix on the key cell and declared_total right-aligned in the rows column); toggling back restores the missing table; the toggle re-renders from the cached snapshot without re-running the dl-snapshot worker.
  </behavior>
  <action>
    tui/services/download_queue.py (the presence decision lives HERE, reusing the existing semantics):
    - New frozen dataclass PresenceRow(key, status, declared_total) — status in the registries PRESENCE_* vocabulary (present/missing/unknown; the four-status mapping already degrades honestly); pure data, the screen renders.
    - New method DownloadQueueService.presence_rows() -> list[PresenceRow]: iterate the OFFICIAL registry (the same direct _official_registry() read missing_datasets uses — custom overlay keys are not download targets and stay out of this view, matching the all-50-official acceptance); merged = self.merged_audit_tasks(); for each key, presence = registries.presence_for(key, merged), declared_total = _declared_total(entry); registry unreadable -> [] (the missing_datasets tolerance twin); absent committed n_audit still lists keys with presence_for's degenerate statuses. Google-style docstring: the full presence view rides the same merged n_audit/reconcile substrate as the missing view and the selection screen (CR-01 — rows AND the missing set move together).
    tui/screens/data_manager.py (PRESENTATION ONLY intact — the docstring's registries-own-the-presence-view line extends to the queue service's presence_rows):
    - MissingSnapshot gains presence_rows: "tuple[PresenceRow, ...]" = () (fakes conform unchanged; docstring updated).
    - DataManagerBackend.missing_snapshot: fill rows = tuple(self._queue.presence_rows()) alongside the existing legs (the queue's own state path stays authoritative — an explicitly constructed service reads its own overlay).
    - New visible binding after a in the D-15 declaration order: Binding("v", "toggle_presence_view", DL_PRESENCE_TOGGLE_LABEL) (the bottom bar and the ? help modal auto-reflect; the clip policy governs at 80 cols).
    - Screen state self._presence_view = False; action_toggle_presence_view flips it and re-renders the missing pane from self._snapshot (no worker kick — the rows ride the snapshot; guard the pre-snapshot emptiness the way _render_missing already does).
    - _render_missing branches: missing mode unchanged (title, rows, happy-zero line); full mode -> title DL_PRESENCE_TITLE.format(n=len(rows)), one row per PresenceRow: key cell = the glyph prefix + key (PRESENT -> "✓ " with _STYLE_DONE, MISSING -> "✗ " with _STYLE_FAIL, UNKNOWN -> "◌ " with _STYLE_MUTED — the same table-symbol glyph-prefix idiom the missing view's "✗ " already uses), truncated at the existing _TASK_W budget; rows column = declared_total right-aligned exactly as the missing view. Column headers and geometry unchanged (no column surgery — the stable two-column shape is why the status rides the key cell).
    tui/strings.py: DL_PRESENCE_TITLE = "全部数据集 ({n})", DL_PRESENCE_TOGGLE_LABEL = "切换缺失/全部".
    Tests (same change):
    - tests/tui/test_services_download_queue.py: new tier-1 block for presence_rows — every committed official key covered (50), statuses within the vocabulary, the missing-status key set equals missing_datasets() keys, the done-reconciled flip consistency (the CR-01 pattern over a seeded done entry, mirroring the existing missing_datasets flip test), and the absent-n_audit degraded listing; register BOTH new DL_ names in EXPECTED_DL_CONSTANTS (the bidirectional IN-09 lock goes red otherwise).
    - tests/tui/test_pilot_data_manager.py: the fakes' missing_snapshot fills presence_rows (a small mixed fixture — some present, some missing, one unknown); NEW Pilot tests: v toggles to the full view (row count == the fixture length, glyph-prefixed keys render), v again restores the missing view, the title swaps between the two constants, and the toggle does not re-run the snapshot worker (kernel/service call count unchanged). Extend the real-seeded backend test (test_backend_missing_snapshot_flips_over_real_seeded_state_cr01) to assert presence_rows rides the same flip.
    - tests/tui/test_snapshots.py: corpus gains "data_manager_presence" (corpus-table docstring row + GOLDENS entry; the drive settles the data-manager screen then presses v), extending the frozen 8 to 9 — the new canonical state earns its golden per the TEST-01 discipline.
    - Regenerate via make snapshot-update: data_manager.svg (the bottom bar gains the v label) and the NEW data_manager_presence.svg; git status over __snapshots__ shows exactly those two.
  <verify>
    <automated>make lint && make typecheck && make snapshot-update && git status --porcelain tests/tui/__snapshots__/ && uv run --group dev --group tui pytest tests/tui/test_services_download_queue.py tests/tui/test_pilot_data_manager.py tests/tui/test_snapshots.py -q</automated>
  </verify>
  <done>Tier-1 and Pilot tests green; the v toggle flips between the missing table and the full 50-key presence view with service-decided statuses; both new DL_ constants registered in the bidirectional inventory; data_manager.svg regenerated and data_manager_presence.svg added and committed (DCL-03).</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| operator-local state file -> services | run_config.json (XDG state root) is read by the env/selection service wiring to derive storage roots; trusted operator-local input, read tolerantly (load_state never raises) |
| local filesystem -> presence decisions | registry-derived paths are stat-checked (is_dir only); no path from this change is ever executed, opened for write, or sent to a subprocess |

## STRIDE Threat Register

ASVS level 1; blocking threshold high — no high/critical threats below, nothing blocks execution.

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-dcl-01 | Tampering | env_smoke directory kernels + selection model_presence over run-config roots | low | accept | Roots come from the operator's own XDG state file — the same trust domain as the launch path that already threads these roots (261014-c2l); presence output is display-only (model_dirs/dataset_dirs are ROUTING, never blocking) and no checked path is executed |
| T-dcl-02 | Information disclosure | kernel CheckResult lines + env_check.json state | low | accept | The root annotation surfaces local filesystem paths into local logs/state only — the same exposure the slot-4 run-config screen already renders; no remote sink exists (static local console) |
| T-dcl-03 | Denial of Service | model_presence / presence_rows filesystem scans | low | mitigate | Bounded stat loops (62/50 is_dir calls) inside the existing exclusive @work(thread=True) workers (the env run worker, the dl-snapshot worker) — the same cost class as the existing registry/n_audit reads; no network, no subprocess |
| T-dcl-SC | Tampering | package installs | high | mitigate | Zero package installs in this plan — stdlib + already-locked deps only; no [ASSUMED]/[SUS] packages exist to gate (the 08-02 legitimacy verdicts stand unchanged) |
</threat_model>

<verification>
Per-task automated lanes are in each task's verify block. After Task 3, run the full gates from the checkout root:

1. make lint — ruff green (PHASE8_TUI wildcard covers the touched tui/ files automatically).
2. make typecheck — ty green (--group tui lane already carries textual/platformdirs).
3. make test — the full suite plus the node lane. EXPECTED baseline: exactly the 10 pre-existing failures documented in .planning/quick/261014-c2l-add-custom-model-dataset-storage-directo/deferred-items.md (stale schema/determinism pins after data commit 9e803ca; root-user chmod persist-failure sims — four of them live in tests/tui/test_services_download_queue.py and tests/tui/test_pilot_data_manager.py, files this task touches: they are environmental, out of scope, and must fail identically before and after). Any failure outside that list is a regression this task introduced and must be fixed before commit.
4. git status --porcelain tests/tui/__snapshots__/ — across the whole plan exactly four SVG diffs: env_check.svg, selection_models.svg, data_manager.svg (regenerated) and data_manager_presence.svg (new). make snapshot-update is the only regeneration path; every SVG is committed with the change that drifted it (D-03).
5. Import-purity spot check: importing tui.services.env_check / tui.services.selection / tui.services.download_queue leaves torch/dnallm absent from sys.modules (the existing tier-1 lane pins; the new run_config import chain must not regress it — run_config itself is already pinned torch-free).
</verification>

<success_criteria>
- The env screen shows eight rows including 模型目录, with both directory kernels annotating the effective root actually checked; a configured run-config root redirects both kernels and the annotation names it.
- model_dirs failures route (advisory) and never block a launch; the launch pre-flight (quick check) now validates model dirs under the same configured root the launch itself will thread.
- The models table shows live per-model download state (✓ 已下载 / ✗ 未下载 / ◌ 未知) decided in the service layer; the datasets presence column is byte-identical to before.
- The data manager toggles with v between the missing table and the full 50-key official presence view; presence comes from the queue service's merged n_audit/reconcile view.
- All strings additions registered in their IN-09 inventory tuples; tier-1 + tier-2 tests landed in the same change; the four SVG golden diffs committed; make lint + make typecheck + full make test green modulo the ten documented pre-existing failures.
</success_criteria>

<output>
Create .planning/quick/261014-dcl-tui-presence-directory-visibility-improv/261014-dcl-SUMMARY.md when done
</output>
