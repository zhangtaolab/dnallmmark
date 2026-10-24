---
phase: quick-261014-mlc
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - tui/services/registries.py
  - tui/services/download_queue.py
  - tui/screens/selection.py
  - tui/screens/data_manager.py
  - tui/app.py
  - tui/strings.py
  - tests/tui/test_services_registries.py
  - tests/tui/test_services_download_queue.py
  - tests/tui/test_pilot_selection.py
  - tests/tui/test_pilot_selection_custom.py
  - tests/tui/test_pilot_data_manager.py
  - tests/tui/test_pilot_nav_shell.py
  - tests/tui/test_snapshots.py
  - docs/TUI-GUIDE.md
autonomous: true
requirements: [MLC-01, MLC-02, MLC-03]
user_setup: []

estimate:
  tokens: 120000
  raw_tokens: 60000
  tasks: 3
  confidence: low

must_haves:
  truths:
    - "MLC-01: the shared download queue executes MODEL downloads end-to-end: enqueue_model gates (idempotent per key; official-registry authority; dnllm_compat.json verdict; defensive already-present disk check), run_task's KIND_MODEL branch composes a python -I -c subprocess (LIST argv, start_new_session, PIPEs, env exactly dict(os.environ)) that calls dnallm.models.model.download_model with a functools.partial-bound modelscope snapshot_download whose cache_dir is the effective model root joined with the registry Model_path — the L6H-04 proven invocation shape — then normalizes the modelscope 1.40.2 nesting (hoist the single snapshot dir's children to the landing root, remove the models/ scaffolding and .lock/) and gates done on config.json existing directly in the landing dir; the landing base resolves through the SAME chain the selection presence uses (run-config resolve_dirs(load_state()).model_root_abs, else the repo pipeline dir) so a landed model always flips its presence cell"
    - "MLC-02: slot 2 is a models-only screen per the maintainer's 2026-10-14 slot split — the m view toggle and the datasets table are gone; every row carries the 选取 mark column and a 下载 column with the honest four-state vocabulary (已下载 / 未下载 d-able / 手动放置 for missing unadapted-or-custom / ◌ 未知); the DEFAULT list shows dnllm-adapted official models plus custom entries, the t toggle reveals official unadapted rows clearly marked 未适配 (never hidden data, honest marking); d on a missing adapted row enqueues the model download through the shared queue and kicks the app driver; d on manual-placement rows toasts the manual state naming the landing directory and NEVER offers huggingface guidance; a done model download flips the row to 已下载 live via the existing apply_queue_event refresh"
    - "MLC-03: slot 3 is the datasets-only screen — the full official dataset list (下载 state + 状态 columns) is the PRIMARY pane with the missing-only view demoted to the v toggle, per-dataset ModelScope download stays the default d/a action, the Zenodo probe line is demoted out of the missing-list title row into the queue title row with 备选 wording (z remains the available alternate, never the default), and the dataset custom-entry wizard stays reachable (w on slot 3); nav slot labels read 2 模型 and 3 数据集; make lint + make typecheck green and the pytest suites green modulo the documented l6h baseline (6 documented + 1 machine-state pipeline/logs failure) plus the four explicitly xfailed stale goldens"
  artifacts:
    - tui/services/registries.py
    - tui/services/download_queue.py
    - tui/screens/selection.py
    - tui/screens/data_manager.py
    - tui/app.py
    - tui/strings.py
    - tests/tui/test_services_download_queue.py
    - tests/tui/test_pilot_selection.py
    - tests/tui/test_pilot_data_manager.py
    - docs/TUI-GUIDE.md
  key_links:
    - "SelectionQueueBackend.enqueue_model (app bridge) -> DownloadQueueService.enqueue_model -> claim/run_task KIND_MODEL branch -> normalized landing under the effective model root -> app QueueEventMessage(done) -> SelectionScreen.apply_queue_event -> _load_data -> model_presence flip to 已下载"
    - "registries.load_dnallm_compat (the ONE tolerant loader over pipeline/dnallm_compat.json, schema 1, 59 keys / 36 adapted, the 261014-l6h artifact) feeds BOTH the slot-2 default filter (SelectionBackend.load_selection_data) and the queue's model channel resolution — one authority, two consumers"
    - "_models_base() in download_queue resolves the identical chain SelectionBackend already uses for model_presence (resolve_dirs(load_state()).model_root_abs or DEFAULT_REGISTRY_DIR) — download landing and presence checking can never disagree about the root"
---

<objective>
Slot 2/3 UI rework per the maintainer's locked 2026-10-14 rulings: slot 2 becomes a pure
MODELS screen (per-model download state + selection state; d-key model download through
the dnallm-authoritative ModelScope channel proven in 261014-l6h; default list filtered to
dnllm_adapted verdicts from pipeline/dnallm_compat.json; honest manual-placement state for
private/no-source models), and slot 3 becomes the pure DATASETS screen (full dataset list
with download state + status as the primary pane; ModelScope the default channel with the
Zenodo bundle demoted to a non-default alternate; landing already routed through the
effective() chain by l6h).

Purpose: the maintainer's console navigation now matches their mental model — one screen
per resource kind, every download ModelScope-first under dnallm authority, no HF guidance
anywhere, private/unadapted models honestly marked instead of hidden.
Output: reworked tui/screens/selection.py (models-only), reworked
tui/screens/data_manager.py (datasets-primary, Zenodo demoted), KIND_MODEL support in
tui/services/download_queue.py, compat loader in tui/services/registries.py, new
tui/strings.py constants, updated pins/tests, updated docs/TUI-GUIDE.md, four stale
snapshot goldens xfailed pending the maintainer's D-03 refresh ruling.
</objective>

<execution_context>
@~/.claude/gsd-core/workflows/execute-plan.md
@~/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/.continue-here.md
@.planning/quick/261014-l6h-dnallm-dnallmmark-dnallm-dev-cd4be43-rep/261014-l6h-SUMMARY.md
@.planning/quick/261014-l6h-dnallm-dnallmmark-dnallm-dev-cd4be43-rep/deferred-items.md
@pipeline/dnallm_compat.json
@tui/services/download_queue.py
@tui/services/selection.py
@tui/services/registries.py
@tui/services/run_config.py
@tui/screens/selection.py
@tui/screens/data_manager.py
@tui/screens/nav.py
@tui/app.py
@tui/strings.py
@tests/tui/test_snapshots.py
@docs/TUI-GUIDE.md
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Model download channel in the shared queue (compat loader + KIND_MODEL + dnallm invocation + landing normalization)</name>
  <files>tui/services/registries.py, tui/services/download_queue.py, tests/tui/test_services_registries.py, tests/tui/test_services_download_queue.py</files>
  <precondition>.venv carries dnallm 1.2.1 (editable from the read-only sibling clone ../DNALLM @ dev/cd4be43) and modelscope 1.40.2 per 261014-l6h Task 1 — import both before starting; if either import fails, halt and report (the machine env is a prerequisite, not something to rebuild here). CI lanes never import either (the service module keeps its no-modelscope-import invariant).</precondition>
  <behavior>
    - registries.load_dnallm_compat(): the committed pipeline/dnallm_compat.json loads with schema_version 1, dnallm_commit cd4be439..., exactly 59 model keys, 36 with dnllm_adapted true (11 channel modelscope-slot + 25 modelscope-mirror); a missing or corrupt file (monkeypatch the module path constant at a tmp_path) degrades to the empty mapping — never an exception
    - enqueue_model(key) outcome order: an existing entry of ANY state yields already_queued; a key absent from the official models registry yields unknown_key; a key whose compat verdict is not dnllm_adapted (or whose compat entry is absent while the map is loadable) yields action unknown with reason_code not_dnallm_adapted; an unreadable compat map yields unknown with reason_code compat_unavailable; an entry with no usable Model_path string yields unknown with reason_code no_model_path; a landing dir that already exists on disk yields unknown with reason_code already_present; a modelscope-CLI-absent machine (the existing _resolve_cli gate as the modelscope-package presence proxy) yields cli_unavailable; an unwritable state rail yields persist_failed with the ghost row rolled back; otherwise a pending kind=KIND_MODEL entry appends and persists — enqueued
    - resolve_model_channel(key): an adapted key resolves to a pure-data spec carrying the compat map's modelscope repo id, the landing dir = _models_base() joined with the registry entry's verbatim Model_path (the model_presence join semantics: base keeps its trailing separator discipline, Model_path keeps its own models/ prefix), and source_url data for drill-down
    - _models_base(): constructor model_root param > the run-config chain resolve_dirs(load_state()).model_root_abs > the repo pipeline dir — with no param and no configured root it is byte-identical to the presence chain SelectionBackend already uses (write a pin test that calls both and asserts equality under a pinned tmp config env)
    - run_task KIND_MODEL branch (dispatch beside the KIND_ZENODO_BUNDLE check, driven by the entry's persisted kind): composes argv = [sys.executable, "-I", "-c", the module-level program constant, str(landing_dir), repo_id]; the program constant is a short python script that reads landing dir and repo id from sys.argv, imports functools.partial, from modelscope.hub.snapshot_download import snapshot_download (the exact hub path dnallm's own modelscope branch uses, DNALLM model.py:462), and from dnallm.models.model import download_model, then calls download_model(repo_id, downloader=partial(snapshot_download, cache_dir=landing_dir)) — the L6H-04 proven invocation, cache_dir riding the partial because the wrapper does not thread it
    - run_task model lifecycle: spawn through the injectable self._spawner with start_new_session=True, PIPEs, and env exactly dict(os.environ); pump stdout/stderr into the log (percent stays None — dnallm logs carry no parseable percents, the row renders indeterminate); nonzero exit -> failed exit_<code>; exit 0 -> _normalize_model_landing(landing) hoists the single models/<org>--<name>/snapshots/<rev>/ directory's children to the landing root and removes the scaffolding (the models/ subtree and the .lock dir), then the done gate requires config.json to exist DIRECTLY in the landing dir — a missing/ambiguous nesting (zero or multiple snapshot dirs) or an empty landing fails honestly with the problem strings recorded in the entry
    - cancel/reap/persist/boot-resume ride the existing machinery unchanged: _reap chunks, _active bookkeeping, os.killpg escalation, downloading->pending downgrade on load — write one test proving a persisted pending KIND_MODEL entry survives load() and re-claims
    - every new test is CI-safe: fake spawner (the existing test file's seam) writing fixture files under tmp_path for the normalization cases; NO test imports dnallm or modelscope or touches the network
  </behavior>
  <action>
    RED first: add the failing service + registries tests to tests/tui/test_services_download_queue.py and tests/tui/test_services_registries.py (behavior list above), run them, confirm failures on the missing API only, commit test(quick-261014-mlc). GREEN: implement per the maintainer's 2026-10-14 dnallm-authority ruling (.continue-here.md: ALL model downloads/load go through dnallm, ModelScope primary — never raw hf guidance; the dataset CLI contract of Phase 10 stays untouched beside it):
    1. tui/services/registries.py: add load_dnallm_compat() — tolerant read of the module-resolved pipeline/dnallm_compat.json (path as a module constant so tests can monkeypatch it), returning the models mapping verbatim ({} on absent/corrupt/wrong-shape). This is the ONE loader; download_queue and the slot-2 backend both consume it — do not duplicate the read.
    2. tui/services/download_queue.py: add KIND_MODEL beside KIND_DATASET/KIND_ZENODO_BUNDLE; a frozen ModelChannelSpec dataclass (key, repo_id, landing, source data, reason_code) mirroring ChannelSpec's role; resolve_model_channel(key); _models_base() (constructor model_root param > run-config resolve_dirs(load_state()).model_root_abs > the repo pipeline default — import the run_config service as a sibling, no cycle: run_config imports only settings); enqueue_model(key) with the documented outcome order; and the run_task dispatch branch _run_model_download(key, run_id) implementing the behavior contract above (the program string as a module-level constant; keep the module's no-textual/no-modelscope-import invariant — the subprocess is the only place dnallm code runs, and argv stays a LIST with no shell). Reuse _finish/_write_log/_reap/claim machinery untouched; KIND_MODEL entries need NO reconcile leg (models are not n_audit subjects — the done gate is the normalized config.json check only).
    3. Machine-local bounded live proof (the l6h evidence discipline, NOT a committed test): sandboxed under /tmp via DNALLMMARK_TUI_STATE_DIR + the constructor model_root param pointed at a tmp dir, run one real enqueue_model + run_task cycle for DNABERT-2-117M (the smallest adapted slot model, ZhejiangLab-LifeScience/DNABERT-2-117M) and verify the normalized landing holds config.json directly; paste the assertion output into the SUMMARY (real-run artifacts stay outside the repo). If the network leg fails, document it and rely on the fake-spawner proof — do not silently skip.
    Follow the existing module docstring contract style: extend the download_queue module docstring with the model-kind contract (dnallm authority per the 2026-10-14 ruling; -I isolation; the normalization rule; no reconcile leg). Strings: the service tier carries zero operator copy (machine vocabularies only) — no strings.py changes in this task.
  </action>
  <verify>
    <automated>uv run --group dev --group tui pytest tests/tui/test_services_download_queue.py tests/tui/test_services_registries.py tests/tui/test_import_lock.py -q</automated>
  </verify>
  <done>Compat loader + KIND_MODEL queue integration landed with CI-safe tests green; the machine-local live DNABERT-2-117M download proof (or its documented network failure) recorded in the SUMMARY; no test imports dnallm/modelscope; make lint and make typecheck green over the touched modules.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Slot 2 becomes the models-only screen (compat default filter, 下载/选取 columns, d-key model download, manual-placement honesty)</name>
  <files>tui/screens/selection.py, tui/app.py, tui/strings.py, tests/tui/test_pilot_selection.py, tests/tui/test_pilot_selection_custom.py, tests/tui/test_snapshots.py</files>
  <behavior>
    - models-only surface: the screen renders the model table exclusively — the m binding, _DATASETS_VIEW branches, the datasets title, and action_switch_list are gone; marks on datasets remain settable through presets (p) and template import (x) and still display in the matrix (v) and the status line (已标记: 模型 n/N · 数据集 m/M stays)
    - default filter: with no text filter, the table lists dnllm-adapted official models PLUS custom entries (customs are operator-added, outside the official registry the ruling constrains — always visible, per the private-models-visible ruling); official unadapted rows are hidden; the t binding toggles the pool to ALL official entries with unadapted rows present and clearly marked (适配 column cell 未适配, dim); adapted rows show 已适配, customs show 自定义
    - columns: 标 (选取 mark, unchanged semantics) · 模型 key (custom badge unchanged) · 类型 · 物种 · 规模(M) · 适配 (new) · 下载 (the old 数据 presence column reworked): 已下载 for present; 未下载 for missing+adapted (the d-able state, error style); 手动放置 for missing+unadapted or missing+custom (muted style — the honest private/no-source state per the ruling, NEVER huggingface guidance); ◌ 未知 for no-Model_path/drift
    - d on the cursor row: a state row stays silent; present -> the honest already-downloaded toast; missing+adapted -> queue.enqueue_model(key) through the injected seam with the SAME outcome-toast mapping the dataset flow uses (enqueued -> toast + app.kick_download_queue; already_queued -> its toast; cli_unavailable -> error toast; persist_failed -> error toast; unknown -> the reason-carrying toast: not_dnallm_adapted/compat_unavailable/no_model_path/already_present); missing manual-placement rows -> the manual toast naming the landing dir (the effective model root joined with the row's Model_path) instructing manual weight placement there
    - a done KIND_MODEL event forwarded by the app re-runs the snapshot worker and the row's 下载 cell flips to 已下载 in place (the existing apply_queue_event -> _load_data path; model_presence re-decides from disk)
    - the filter count readout carries the pool mode (已适配 vs 全部 segment) so the default-filter state is always legible; the text filter composes AND over the active pool
    - help modal + bottom bar reflect the new binding set: m row gone, t row present (declaration order: space, t, p, x, s, /, w, e, d, v); w opens the MODEL wizard only (kind is now constant); e toggles model customs only
  </behavior>
  <action>
    Load the tui-design skill (maintainer directive 2026-10-12: all screen-building work runs through it) and follow it for the column layout, state-glyph, and toast wording decisions before editing. Then, per the maintainer's locked slot-split ruling (2026-10-14, .continue-here.md: slot 2 = models ONLY — download status + selection status columns, no dataset columns):
    1. tui/strings.py: add the new constants (适配/下载 column headers, 已适配/未适配/自定义 compat cells, the manual-placement download cell 手动放置, the pool-mode filter-count segments, the t binding label, the model d label, the manual-placement toast naming {path}, the already-downloaded toast) in the SEL block, following the existing comment style; retire SEL_SWITCH_LABEL/SEL_SCREEN_TITLE_DATASETS and the dataset-only enqueue toasts from this screen's imports only if nothing else consumes them (data_manager owns the dataset vocabulary — check before deleting any constant; a constant still consumed elsewhere stays).
    2. tui/screens/selection.py: extend SelectionData with an additive compat field (dict key -> verdict mapping; default {} keeps every Phase 8/9 fake conforming); SelectionBackend.load_selection_data populates it from registries.load_dnallm_compat(); rework the screen to a models-only surface per the behavior contract — remove the view-toggle machinery, add the pool-mode state + t action, extend _MODEL_COLUMNS with the 适配 and 下载 columns, derive the download cell from model_presence + compat + custom_status (render only — the service decided presence, the compat map decided adaptation), and replace action_enqueue_dataset with the model-download action implementing the guard chain. Keep the existing worker/filter/preset/template/wizard/matrix machinery byte-adjacent — this is a surgical rework of the view layer, not a rewrite; the i18n grep lock (zero Chinese literals in the module) must stay green.
    3. tui/app.py: SelectionQueueServiceProtocol + SelectionQueueBackend gain enqueue_model (the same two-Protocol bridge shape — the app-level shared queue is the ONE instance; the declared QueueDriverProtocol is untouched).
    4. Tests: update the pinning tests (the m-toggle boot test, test_d_on_the_models_view_is_a_silent_noop — inverted into the model-download contract, the help-row pin, the w-routes-by-active-table test — models-only now, the dataset-wizard full-loop test — moves its dataset leg expectation out of this screen) and ADD the new Pilot tests for: default pool hides unadapted officials but shows customs; t reveals unadapted rows marked 未适配; the four 下载 cell states; each d guard path through the injected fake queue seam (enqueued + kick called, manual toast names the landing dir, present noop); the done-event live flip. Follow the tui-design skill's guidance for the visual assertions; all Pilot tests keep using fakes (no real queue, no fs).
    5. tests/tui/test_snapshots.py: mark the selection_models and selection_datasets goldens pytest.mark.xfail(strict=True) with a reason naming this task and "golden refresh pending maintainer make snapshot-update + D-03 review" — do NOT regenerate, do NOT delete, do NOT touch tests/tui/__snapshots__/.
  </action>
  <verify>
    <automated>uv run --group dev --group tui pytest tests/tui/test_pilot_selection.py tests/tui/test_pilot_selection_custom.py tests/tui/test_pilot_matrix.py tests/tui/test_snapshots.py tests/tui/test_import_lock.py -q</automated>
  </verify>
  <done>Slot 2 renders models only with the 适配/下载/标 columns; the default pool is adapted+customs with unadapted honestly revealed by t; d downloads models through the shared queue with every guard path toast-pinned; the done flip is Pilot-proven; the two selection goldens are strict-xfail with the maintainer-ruling reason; lint + typecheck green.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: Slot 3 datasets-primary rework (full list default, Zenodo demoted, ModelScope default affirmed, dataset wizard preserved) + nav labels + docs + full gates</name>
  <files>tui/screens/data_manager.py, tui/strings.py, tests/tui/test_pilot_data_manager.py, tests/tui/test_pilot_nav_shell.py, tests/tui/test_snapshots.py, docs/TUI-GUIDE.md</files>
  <behavior>
    - the FULL official dataset list (every registry key) is the primary top pane with 下载 state (the merged presence status: ✓ 在场 / ✗ 缺失 / ◌ 未知) + 状态 (declared rows) columns; a row with a live queue entry renders its queue state word in the 下载 cell (pending/downloading/failed/mismatch — a screen-side join of presence_rows with the entries() snapshot already delivered in the same SnapshotLoaded message; no service change); the missing-only table is the v-toggled alternate (the toggle direction flips from today)
    - d acts on the cursor row of whichever pane is active: a missing row in the full list enqueues the SAME per-dataset ModelScope channel as before (the default channel per the ruling — unchanged enqueue path, unchanged outcome toasts); present rows keep the honest noop toast; a/enqueue-all, r, x, g, enter drill-down all keep working over the new primary pane
    - the Zenodo probe line moves out of the missing-list title row into the QUEUE title row with 备选-prefixed wording (the alternate-channel framing per the ruling: Zenodo available, never the default); z stays the hidden alternate entry with its 备选 label; the per-dataset ModelScope channel needs no copy change — it IS the default
    - w opens the dataset custom-entry wizard (the kind is constant datasets now): lazy WizardModal import inside the action (the 09-06 cycle-break pattern), on_changed wired to the existing snapshot reload; e stays OFF this screen (custom dataset enable/disable remains a slot-2-era surface — flagged in the SUMMARY, not built here)
    - nav labels: NAV_LABEL_SELECTION renders 模型 and NAV_LABEL_DATA renders 数据集 (constant values only — names, bindings, and routing untouched; the env-check 前往数据管理 routing hint and its pins stay byte-identical)
    - the data_manager + data_manager_presence goldens are strict-xfail with the same maintainer-ruling reason as Task 2; tests/tui/__snapshots__/ untouched
    - docs/TUI-GUIDE.md: Screen 2 and Screen 3 sections rewritten to the new surfaces (key maps, columns, the default-filter + manual-placement semantics, the Zenodo demotion note, the model d-key flow through the shared queue); the slot table row names updated; no other sections touched
  </behavior>
  <action>
    Load the tui-design skill first (maintainer directive) and apply it to the pane promotion, the queue-state overlay wording, and the demoted Zenodo placement. Then, per the locked ruling (slot 3 = datasets ONLY: download + status; ModelScope DEFAULT, Zenodo demoted to non-default):
    1. tui/screens/data_manager.py: flip the pane default (the _presence_view flag inverts — full list primary, missing-only the v toggle); generalize the cursor/action plumbing so d/r/x/enter target the active pane (the _missing_cursor_key pattern extended, state rows still silent); add the screen-side queue-state join for the 下载 cells; move the Zenodo line widget from the missing-title row to the queue-title row; add the w binding (lazy wizard import, on_changed -> _reload_snapshot). All copy through tui/strings.py (new DL_ constants: the 备选-prefixed zenodo line forms, the full-list title, the queue-state overlay words where they are operator copy rather than machine vocabulary — follow the existing data/table-symbol distinction documented in the module header).
    2. tui/strings.py: the DL additions/rewrites above + NAV_LABEL_SELECTION 模型·数据集 -> 模型 and NAV_LABEL_DATA 数据管理 -> 数据集 (value-only; every consumer imports the constant).
    3. Tests: update test_pilot_data_manager pins (pane order/default, zenodo line placement/wording, the d-on-full-list paths, the w wizard injection) and test_pilot_nav_shell slot pins (模型/数据集); add the queue-state overlay Pilot test over fakes; xfail the two data_manager goldens in tests/tui/test_snapshots.py exactly as Task 2 did for the selection pair.
    4. docs/TUI-GUIDE.md per the behavior contract (surgical section rewrites; the Quick-start slot table + Screen 2/3 sections + the state-persistence note if the queue now persists KIND_MODEL entries — one honest sentence there).
    5. Full gates: make lint, make typecheck, make test. Baseline accounting per the l6h deferred-items (authoritative, re-based 2026-10-14): 6 documented baseline failures (5 test_schemas + 1 test_determinism) + 1 proven pre-existing machine-state failure (test_storage_overview_defaults_mirror_real_consumers vs the gitignored pipeline/logs leftovers) + the 4 new strict-xfail goldens; the 4 root-user chmod sims run green on this non-root box; the known snapshot flake did not strike at l6h close — anything beyond this set is a NEW failure and must be fixed or proven pre-existing before handoff. Also run make test-fast as the quick lane.
  </action>
  <verify>
    <automated>make lint && make typecheck && uv run --group dev --group tui pytest tests/tui/test_pilot_data_manager.py tests/tui/test_pilot_nav_shell.py tests/tui/test_snapshots.py -q && make test-fast</automated>
  </verify>
  <done>Slot 3 lists every dataset with download state + status as the primary pane; ModelScope per-dataset download remains the default action with Zenodo visibly demoted to the 备用 alternate; the dataset wizard is reachable via w; nav reads 2 模型 3 数据集; TUI-GUIDE matches the shipped surfaces; full-suite gates green modulo the documented l6h baseline + the 4 xfailed goldens; the SUMMARY flags every maintainer-facing item (golden refresh ruling, task-marking surface reduction, dataset-customs e-toggle absence, the live model-download proof from Task 1).</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| queue subprocess -> OS | The model-download program runs as a child python process executing third-party library code (dnallm + modelscope) against the network |
| network -> model_root | Downloaded model cards are untrusted data landing under the effective model root |
| XDG state/config files -> service | download_queue.json + directories.json + run-config state are user-owned files read by the landing-resolution chain |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-qt-01 | Elevation/Tampering | _run_model_download subprocess | high | mitigate | LIST argv only (no shell), python -I isolation (no cwd/user-site imports), a FIXED module-level program constant (no operator-controlled code — only landing dir + repo id cross as argv data), start_new_session + the existing killpg cancel discipline |
| T-qt-02 | Tampering | _normalize_model_landing | medium | mitigate | Normalization only moves/collapses directories under the resolved landing dir it created this run; it never follows symlinks out of the landing root (skip/hoist real entries only, fail honestly on ambiguity) and never executes anything inside the card |
| T-qt-03 | Repudiation | KIND_MODEL queue entries | low | mitigate | The existing per-key verbatim log files + persisted attempts/state ride unchanged — every model download leaves the same audit trail dataset downloads already do |
| T-qt-04 | Tampering | user-owned directories.json / run-config state -> _models_base() | medium | mitigate | The chain is read-tolerant through the existing seams (load_state whole-spec tolerance + load_directories_tolerant); a malformed root degrades to the repo default exactly as the dataset chain (l6h) already proven, never to an exception-driven wrong write |
| T-qt-SC | Tampering | package installs | high | mitigate | No new packages: dnallm/modelscope are already machine-local per 261014-l6h (never added to any uv group; CI never installs them) — no package-legitimacy gate applies; the DNALLM sibling clone stays read-only |
</threat_model>

<verification>
- Task-level automated commands above all green (uv-run targeted suites, make lint, make typecheck, make test-fast).
- Full make test at Task 3 close with explicit baseline accounting: exactly the 6 documented + 1 machine-state pre-existing failures + 4 strict-xfail goldens; anything beyond is a NEW failure.
- Machine-local (not CI): the Task 1 sandboxed live DNABERT-2-117M download proof through enqueue_model + run_task with the normalized config.json assertion, evidence pasted into the SUMMARY.
- Manual sanity (maintainer UAT surface, listed in the SUMMARY): slot 2 d on a missing adapted model flips the row live; slot 3 full list renders with ModelScope default and the demoted Zenodo line.
</verification>

<success_criteria>
- MLC-01/02/03 must_haves truths hold and are test-pinned (service fakes + Pilot fakes; no CI lane imports dnallm/modelscope or touches the network).
- Every operator-facing string lives in tui/strings.py; styles only in styles.tcss; zero new dependencies; zero changes to slot 4/5 screens, pipeline/, registries, or the DNALLM sibling.
- tests/tui/__snapshots__/ is byte-untouched; the four stale goldens are strict-xfail with the maintainer-ruling reason; the SUMMARY carries the golden-refresh flag (D-03 review pending) and the surface-relocation notes (task-marking surface now presets/templates + slot-4 picker; dataset-customs e-toggle has no surface; dataset wizard now on slot 3 w).
- docs/TUI-GUIDE.md Screen 2/3 sections match the shipped behavior.
- Commits: TDD RED test commit, GREEN implementation commit(s), docs/gates commit — plain messages, no attribution trailers (maintainer config).
</success_criteria>

<output>
Create .planning/quick/261014-mlc-tui-slot-2-3-ui-slot-2-d-dnallm-download/261014-mlc-SUMMARY.md when done
</output>
