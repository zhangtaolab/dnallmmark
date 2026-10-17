---
phase: quick-261017-uwr
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - tui/services/run_config.py
  - tui/services/sweep_launcher.py
  - tui/services/sweep_monitor.py
  - tui/screens/monitor.py
  - tui/strings.py
  - tests/tui/test_services_run_config.py
  - tests/tui/test_services_sweep_launcher.py
  - tests/tui/test_services_sweep_monitor.py
  - tests/tui/test_strings_phase11.py
  - tests/tui/test_pilot_monitor.py
  - tests/tui/test_snapshots.py
  - tests/tui/__snapshots__/monitor_running.svg
  - tests/tui/__snapshots__/monitor_empty.svg
  - .planning/WINDOWS.md
  - .planning/quick/261017-uwr-slot-5-monitor-ux-overhaul-context-heade/261017-uwr-SUMMARY.md
autonomous: true
requirements: [UWR-1, UWR-2, UWR-3, UWR-4]

user_setup: []

estimate:
  tokens: 62000
  raw_tokens: 49000
  tasks: 4
  confidence: low

must_haves:
  truths:
    - "UWR-1 (three-state cell derivation, closes WINDOWS #34): a discovered cell's state is derived as — readable record status (verbatim, terminal family) / RESUME_MARKER -> skipped / pair LIVE with activity (runs/ or checkpoint-* child, or seed-dir mtime within STALE_GRACE_SECONDS, or the root's frontier-newest dir) -> running / pair LIVE without activity -> queued / pair NOT live and non-terminal (kill-left checkpoint residue, stale dirs, empty dirs) -> INTERRUPTED (the new machine state 'interrupted', glyph ⏸). Live-pair evidence is per-(model, task): the pair is a member of a live sweep's PLANNED matrix (UWR-2). live_pairs=None (unknown evidence — every pre-existing call site and fake) keeps today's byte-identical semantics: existing suite members pass unmodified. entry_fold and _fold_frac_states gain the interrupted leg with precedence running > failed > interrupted > completed(all completed|skipped) > queued."
    - "UWR-2 (live-process evidence sources): (a) TUI-launched sweeps — the launcher registry's live handles (SweepLauncher.live_sweeps, whose entries carry meta.argv verbatim); (b) attached/discovered CLI sweeps — a bounded /proc cmdline probe for run_sweep.py processes (probe per scan in the existing D-09 workers, NEVER per row — the maintainer's no-ps-per-row ruling). Both feed run_config.argv_matrix, the compose_argv inverse: --models/--tasks/--seeds/--registry-dir/--peft/--config-variant/--curve recovered through run_sweep.enumerate_matrix SAME-SOURCE (never a naive cross product — alias cell names +lora/+variant must match the cell-dir identity), --from-failures through run_sweep.load_failure_pairs; unparseable argv -> None (live-but-unknown -> legacy rendering for that root, never a false interrupt). SweepLauncher.live_sweep_matrices() merges registry + probe with a per-argv matrix cache. The kill face (live_sweeps/kill_sweep/[k] gate) stays REGISTRY-ONLY — a probed CLI sweep is display-live but not handle-killable; probe roots DO join the root-level running classification (live_roots threading at the MonitorBackend seam)."
    - "UWR-3 (context header): a new one-row Label (id mon-context-header) directly under the monitor title bar renders, for the ATTACHED root only (unattached -> empty string, the stats-line precedent — the multi-root ruling resolves to attached-root-first), the bilingual MON_CONTEXT_HEADER: zh 结果目录 {root} · {n} 训练项：⏵{running} 运行 / ✓{done} 完成 / ⏸{interrupted} 中断 (terminology table: 结果目录/训练项 — the ruling's 「输出根/对」 wording is direction, the approved table is binding) / en 'Output root {root} · {n} cells: ⏵{running} running / ✓{done} done / ⏸{interrupted} interrupted'. n = total entry rows; the three counts = fold-state families (running / completed / interrupted — failed and queued rows stay visible in the table with their own glyphs but are not in the three-segment header). Single row, no_wrap; counts derive from the SAME entry_fold outputs _render_cells computes (render-side composition only — the screen derives nothing from the artifact tree)."
    - "UWR-4 (live-on-top ordering): the entries table sorts by fold group — group 0 running rows (newest activity time DESC, CellRow.newest_mtime desc, None last), group 1 unfinished non-running rows (failed / interrupted / queued / unrecognized, key ASC stable), group 2 completed rows sink (key ASC). _set_table_rows reorders when the desired key order differs from the table's current order (remove+re-add moved rows) with the WR-05 cursor re-pin by key (scroll=False); steady ticks with unchanged order take the existing in-place update path — zero added churn. MON_STATE_RUNNING's glyph changes ⠋ -> ⏵ and MON_STATE_INTERRUPTED (⏸ 中断 / ⏸ interrupted) joins the call-time _cell_state_cells vocabulary ($text-muted style), so header and table show the same glyph for the same state."
    - "GATES: make lint and make typecheck green; make test at the pre-task baseline MEMBERSHIP (read counts at execution time; 2026-10-17 baseline 1F/1869P, the 1F being the machine-local storage-overview member) with every NEW test green and zero new failures; node lane 26/26 (inside make test); golden discipline — monitor_running.svg regenerated via make snapshot-update and deliberately UNCOMMITTED pending maintainer D-03 review (the vxr #29 precedent: the committed tree fails test_snapshots on exactly the monitor goldens until they land); monitor_empty.svg regenerated alongside (may come out byte-identical — the unattached header is empty by design; report either way); EVERY non-monitor SVG byte-identical (sha256 before/after comparison); tests/tui/test_snapshots.py fixture change limited to adding one interrupted pair row to _running_monitor_service (fixture data, no behavioral pin weakened); i18n single-home + identical placeholder sets + inventory updated (EXPECTED_MON_CONSTANTS, MON_CELL_STATE_CONSTANTS, MON_STATE_GLYPHS); EHC/c4j/vxr semantics preserved byte-for-byte (ETA on parsed-progress rows, [k] kill confirm, [f] failures, [t] log tail, [a] attach, [r] rescan); commits PLAIN (zero attribution trailers), executor does NOT push; the LIVE hyenadna sweep running on this box right now is NEVER signalled, killed, or disturbed — read-only probing only, Pilot/unit tests use fakes per D-03 discipline."
  artifacts:
    - tui/services/run_config.py
    - tui/services/sweep_launcher.py
    - tui/services/sweep_monitor.py
    - tui/screens/monitor.py
    - tui/strings.py
    - tests/tui/test_services_run_config.py
    - tests/tui/test_services_sweep_launcher.py
    - tests/tui/test_services_sweep_monitor.py
    - tests/tui/test_strings_phase11.py
    - tests/tui/test_pilot_monitor.py
    - tests/tui/test_snapshots.py
    - .planning/WINDOWS.md
    - .planning/quick/261017-uwr-slot-5-monitor-ux-overhaul-context-heade/261017-uwr-SUMMARY.md
  key_links:
    - "SweepLauncher.live_sweep_matrices() = registry live handles (meta.argv) ∪ probe_cli_sweeps(/proc) -> run_config.argv_matrix (enumerate_matrix / load_failure_pairs same-source) -> {resolved root: frozenset[(model, task)] | None} (UWR-2)"
    - "MonitorBackend scans (full_scan / frontier_scan / cells_view / entries_progress) thread live_roots (registry ∪ probed) + live_pairs=matrices.get(root, frozenset()) -> sweep_monitor three-state derivation (UWR-1); tolerant getattr for fakes without the new launcher method (the entries_progress precedent)"
    - "_seed_state_from_dir / _cell_state_from_dir pair_live gate -> CELL_INTERRUPTED | CELL_RUNNING | CELL_QUEUED -> entry_fold interrupted leg -> screen _cell_state_cells (⏵/✓/⏸) -> header counts + group ordering + goldens (UWR-1/3/4)"
    - "CellRow.newest_mtime (cells_view fills max seed-dir mtime) -> group-0 sort key (mtime DESC) -> _set_table_rows reorder path -> WR-05 cursor identity (UWR-4)"
    - "kill face UNCHANGED: [k] -> MonitorLauncherProtocol.live_sweeps() (registry-only) -> kill_sweep handle -> y-only confirm (a probed CLI sweep refuses with MON_KILL_UNAVAILABLE — pre-existing semantics)"
---

<objective>
The slot-5 monitor UX overhaul the maintainer ruled 需要 at 2026-10-17 22:15 (their words: slot5 的逻辑完全搞不懂 — the entries list does not explain where its rows come from, dead cells wear the running glyph, and discovery-order mixing hides the live row). WINDOWS #34 (the interrupted-cell state conflation: PlantHelixSeek killed 10-16 and dnamamba interrupted 10-15 both render ⠋ 运行 at tui/screens/monitor.py) is the explicit symptom this task closes.

Three deliverables (maintainer ruling, verbatim intent):
1. Context header — one line at the top of the monitor screen: current output root + count summary, making "where do these rows come from" self-explanatory. Multi-root wording decided at planning time: attached-root-first single line (every other context line on this screen — cells title, stats line, [f]/[t] bindings — already binds to the attached root; one basis, no per-root wall of text).
2. Three-state derivation — cell state goes from two effective states (done = trainer_state/record marker, everything else = running) to three: ✓ done (marker/record) / ⏵ running (LIVE-PROCESS evidence: the cell's model×task hits a live sweep handle's planned matrix — TUI launcher handles for TUI launches, /proc process probing for attached CLI sweeps) / ⏸ interrupted (no marker, no live process — historical residue shown honestly). This closes #34.
3. Live-on-top ordering — running rows first (newest activity first), then unfinished non-running rows, completed rows sink to the bottom. The current alphabetical interleave is the confusion's other main source.

Purpose: the maintainer reads the finetuned-smoke root and sees, in one glance, 「结果目录 finetuned-smoke · 5 训练项：⏵1 运行 / ✓2 完成 / ⏸2 中断」with the hyenadna live row on top — instead of five rows all claiming to run.

Output: three-state scanner derivation + live-evidence sources (argv matrix recovery + CLI probe), the screen header/ordering/glyphs, bilingual strings + inventory, regenerated monitor goldens (uncommitted, D-03), WINDOWS #34 closed + the golden-deviation row recorded.
</objective>

<execution_context>
@~/.claude/gsd-core/workflows/execute-plan.md
@~/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/WINDOWS.md

The five source files this task modifies — read them before editing:
@tui/screens/monitor.py
@tui/services/sweep_monitor.py
@tui/services/sweep_launcher.py
@tui/services/run_config.py
@tui/strings.py

Test-surface conventions (fakes, tmp trees, inventory tripwires):
@tests/tui/test_pilot_monitor.py
@tests/tui/test_snapshots.py
@tests/tui/test_strings_phase11.py
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Live-evidence sources — run_config.argv_matrix + SweepLauncher.live_sweep_matrices + the /proc CLI probe</name>
  <files>tui/services/run_config.py, tui/services/sweep_launcher.py, tests/tui/test_services_run_config.py, tests/tui/test_services_sweep_launcher.py</files>
  <behavior>
    - Test: argv_matrix(compose_argv(spec)) over the committed registries returns exactly the spec's (model, task) pairs (a 2x2 spec; a single-model spec with absent-flag legs).
    - Test: a peft lora spec round-trips to ALIAS pairs ("model+lora" cell names) — the enumeration output, never the bare filter names.
    - Test: argv with --models/--tasks ABSENT parses as the full-registry legs (None filters — the driver's own default semantics); argv without --seeds, or without a run_sweep.py element, returns None.
    - Test: a --from-failures argv parses through load_failure_pairs over a tmp failures file (the pairs verbatim); an unreadable failures file returns None (SystemExit/OSError/ValueError caught, never raised).
    - Test: probe_cli_sweeps over a FAKE proc root (tmp tree: numeric pid dirs with NUL-separated cmdline files) maps {resolved --output-root: argv} — one run_sweep.py process, one unrelated python process (ignored), one unreadable pid dir (skipped); an absent proc root returns {}.
    - Test: SweepLauncher.live_sweep_matrices() with a fake spawner handle (poll() None) merges the registry argv's matrix with probed roots; a parse-failure argv maps the root to None (live-but-unknown); repeated calls with the same argv hit the matrix cache (enumerate counted once via a monkeypatched spy).
    - Test: live_sweeps() and kill_sweep() behavior is byte-unchanged (the registry-only kill face — existing members already pin this; assert no probe root ever enters live_sweeps()).
  </behavior>
  <action>
    Add to tui/services/run_config.py (beside compose_argv, ~line 1094 — this module owns argv composition, so it owns the inverse):
    1. argv_matrix(argv, registry_dir=None) -> "frozenset[tuple[str, str]] | None". Pair-scan the argv list (walk elements; a recognized flag consumes the next element). Flags: --models and --tasks (comma-split; flag ABSENT -> None filter = the driver's full-registry default, run_sweep.py:336-349), --seeds (comma-split ints; ABSENT -> return None — run_sweep marks it required), --registry-dir (the enumeration dir override), --peft, --config-variant, --curve (comma floats). Guard: no element ending run_sweep.py -> None.
    2. --from-failures present: pairs = run_sweep.load_failure_pairs(path, registry_dir or DEFAULT_REGISTRY_DIR) inside try/except (SystemExit, OSError, ValueError) -> None on failure — the exact idiom sweep_launcher._from_failures_refusal already uses at tui/services/sweep_launcher.py:778-786. Never re-implement the pair loading.
    3. Otherwise: pairs = {(str(cell[0]), str(cell[1])) for cell in run_sweep.enumerate_matrix(models, tasks, seeds, registry_dir or DEFAULT_REGISTRY_DIR, peft=..., fractions=..., config_variant=...)} — the SAME same-source enumeration preview() threads at tui/services/run_config.py:907-913. enumerate_matrix emits the ALIAS cell names and the fraction expansion; projecting (cell[0], cell[1]) matches the cell-dir identity CellRow documents (verbatim alias, never translated). Documented edge (accept, do not fix): --subset_file is not re-filtered — an excluded pair over-claims live (renders queued, not interrupted) while its sweep runs; over-claim is the safe direction, never a false interrupt.
    Add to tui/services/sweep_launcher.py:
    4. Module function probe_cli_sweeps(proc_root="/proc") -> dict[str, tuple[str, ...]]. Iterate the numeric entries of proc_root (sorted, skip non-numeric); read <pid>/cmdline as bytes, split on NUL, decode utf-8 replace (any OSError/ValueError -> skip the pid). A process whose argv contains an element whose Path name is run_sweep.py: extract --output-root (pair-scan, reuse-tolerant); resolve the value absolute — a RELATIVE root resolves against os.readlink(<pid>/cwd) best-effort, falling back to plain resolve (compose_argv threads absolute roots by contract; the relative leg is the CLI hand-run edge). Map {resolved root str: argv tuple}. proc_root absent/unlistable -> {} (non-Linux degrades to no CLI evidence — honest). Bounded and read-only: filesystem reads only, no subprocess, no signal, EVER (a LIVE sweep may be running on this box while tests execute — the probe never touches it beyond reading its cmdline).
    5. SweepLauncher.live_sweep_matrices() -> dict[str, "frozenset[tuple[str, str]] | None"]. For each root in live_sweeps() (the pruned registry read, tui/services/sweep_launcher.py:931-959): entry meta.argv -> run_config.argv_matrix; unparseable -> None (live-but-unknown-matrix — that root's cells keep legacy activity semantics, never a false interrupt). Merge probe_cli_sweeps() results the same way (probe argv -> argv_matrix; unparseable -> None). Keep an instance matrix cache keyed by the argv tuple (a full-matrix argv enumerates 8850 cells once per session, not once per 2s tick); dead entries' cache rows may persist (keyed by argv, harmless). live_sweeps()/kill_sweep()/detach() stay byte-untouched — the kill face is registry-only by design (a probed CLI sweep has no Popen handle in this process; [k] keeps refusing it with MON_KILL_UNAVAILABLE).
    6. Zero Chinese literals, zero textual imports (the services-tier locks, enforced by existing grep tests); ruff + ty clean (the lint wildcard covers tui/ automatically).
  </action>
  <verify>uv run --group dev --group tui pytest tests/tui/test_services_run_config.py tests/tui/test_services_sweep_launcher.py -q && make lint && make typecheck</verify>
  <done>argv_matrix round-trips compose_argv (alias shapes included), degrades to None on unparseable argv, and parses --from-failures through load_failure_pairs; the /proc probe maps live run_sweep processes to their resolved roots from a fake proc tree; live_sweep_matrices merges registry + probe behind a matrix cache with None for live-but-unknown; the kill face is untouched; both test files green with the new members and zero edits to existing members.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Three-state cell derivation in sweep_monitor — CELL_INTERRUPTED + live_pairs threading + CellRow.newest_mtime</name>
  <files>tui/services/sweep_monitor.py, tests/tui/test_services_sweep_monitor.py</files>
  <behavior>
    - Test (#34 pin): a seed dir with kill-left checkpoint-*/ residue and live_pairs MISSING its pair derives interrupted (today it derives running forever — the conflation); with live_pairs CONTAINING the pair it derives running; with live_pairs None it derives running (legacy, byte-identical).
    - Test: pair live + bare empty dir -> queued; pair MISSING + bare empty dir -> interrupted; pair MISSING + the root's frontier-newest dir -> interrupted (the newest-dir running leg is gated too).
    - Test: record status and RESUME_MARKER legs are unaffected by live_pairs in every combination (records win first, always).
    - Test: entry_fold precedence running > failed > interrupted > completed > queued over mixed seed states ((interrupted, completed) -> interrupted; (running, interrupted) -> running; (failed, interrupted) -> failed; (completed, completed) -> completed; (queued, queued) -> queued).
    - Test: the maintainer scenario shape over one tmp root — two pairs with completed records, one live pair (fresh checkpoint dir + mtime), two dead pairs (stale checkpoint residue), live_pairs = the one live pair -> cells_view folds to 2 completed / 1 running / 2 interrupted.
    - Test: CellRow.newest_mtime = max seed-dir mtime (cells_view fills it); entries_progress parses progress ONLY for live-running seeds (a dead interrupted pair with checkpoints parses NOTHING — the 2s cadence stays light).
  </behavior>
  <action>
    All edits in tui/services/sweep_monitor.py (the pure scanner owns derivation; the screen derives nothing — its tier contract):
    1. CELL_INTERRUPTED = "interrupted" beside the CELL_* vocabulary (~line 138-142). Interrupted is NOT a terminal record status — leave TERMINAL_RECORD_STATUSES untouched (progress/ETA math and stats done-counts unchanged).
    2. _cell_state_from_dir(cell_dir, now, pair_live=None): after the record and RESUME_MARKER legs, pair_live is False -> CELL_INTERRUPTED (BEFORE the activity legs — residue signals are moot when no live sweep plans the pair); pair_live True or None -> the existing _dir_shows_activity -> CELL_RUNNING / CELL_QUEUED legs byte-identical. None = no evidence data = legacy semantics for every pre-existing caller and fake.
    3. _seed_state_from_dir(seed_dir, now, frontier_newest=False, pair_live=None): thread pair_live into _cell_state_from_dir calls (seed + fraction level — _fold_frac_states needs the interrupted leg too) and gate the frontier_newest early-running leg (~line 791-797): frontier_newest + no record + no marker -> running only when pair_live is True or None; False -> interrupted.
    4. entry_fold (~line 1028) and _fold_frac_states (~line 760): insert the interrupted leg with precedence running > failed > interrupted > completed (all completed|skipped, non-empty) > queued. Update both docstrings' fold orders.
    5. Signature threading (all additive, None defaults): cells_view(root, expected_seeds=None, live_pairs=None), frontier_scan(root, live_roots=(), now=None, live_pairs=None), entries_progress(root, live_pairs=None). Per seed: pair_live = None when live_pairs is None else ((model, task) in live_pairs). Thread into every _seed_state_from_dir call site in those three functions.
    6. CellRow gains newest_mtime: "float | None = None" (additive defaulted field — every existing fake and test constructor at tests/tui/test_pilot_monitor.py:141 and tests/tui/test_snapshots.py:448 constructs unchanged). cells_view fills it with the max _seed_dir_mtime over the row's discovered seed dirs (the walk already stats these).
    7. Root-level classification (full_scan/frontier_scan state fields) is UNCHANGED — the discovered table's three D-03 states stay exactly as they are; only per-cell/entry states gain the third state.
  </action>
  <verify>uv run --group dev --group tui pytest tests/tui/test_services_sweep_monitor.py -q && make lint && make typecheck</verify>
  <done>The interrupted state exists with its fold legs; every live_pairs=None call path is byte-identical to today (existing members green unmodified); the #34 residue case derives interrupted while the live-pair and legacy cases keep running/queued; the maintainer scenario (2 done / 1 running / 2 interrupted) derives over one tmp root; CellRow.newest_mtime is filled and defaulted-safe.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: Screen — context header + ⏵/⏸ glyphs + live-on-top ordering + MonitorBackend evidence threading + strings/inventory</name>
  <files>tui/strings.py, tui/screens/monitor.py, tests/tui/test_strings_phase11.py, tests/tui/test_pilot_monitor.py</files>
  <behavior>
    - Test: the header renders for an attached root — root name, n = row count, and the running/done/interrupted fold counts in the MON_CONTEXT_HEADER shape (fake service rows: 2 completed + 1 running + 2 interrupted -> the maintainer's exact 5/1/2/2 line); nothing attached -> the header Label is empty.
    - Test: entry ordering — the running row renders ABOVE interrupted/queued rows, completed rows sink below; within the running group a fresher newest_mtime row renders first.
    - Test: a fold flip mid-session (fake state: a completed pair becomes running) reorders the LIVE table with the cursor row identity preserved (WR-05: move_cursor by key, scroll=False — assert the focused row key survives the reorder).
    - Test: an interrupted fold row renders the MON_STATE_INTERRUPTED glyph-word + done/total counts; the narrow grid keeps the glyph + counts form (the _entry_state_cell degradation).
    - Test: strings — MON_STATE_RUNNING opens with ⏵, MON_STATE_INTERRUPTED opens with ⏸, MON_CONTEXT_HEADER carries the identical placeholder set {root, n, running, done, interrupted} in both languages, zh uses 结果目录/训练项 (terminology table), all three names present in EXPECTED_MON_CONSTANTS, MON_STATE_GLYPHS matches the actual glyph vocabulary.
  </behavior>
  <action>
    tui/strings.py (beside the MON_STATE_* block ~line 1676):
    1. MON_STATE_RUNNING glyph edit: "⠋ 运行"/"⠋ running" -> "⏵ 运行"/"⏵ running" (both languages, name and key unchanged — the ruling's icon triple is ⏵/✓/⏸ and the header/table must show the same glyph for the same state).
    2. MON_STATE_INTERRUPTED = _t("MON_STATE_INTERRUPTED", "⏸ 中断", "⏸ interrupted").
    3. MON_CONTEXT_HEADER = _t("MON_CONTEXT_HEADER", "结果目录 {root} · {n} 训练项：⏵{running} 运行 / ✓{done} 完成 / ⏸{interrupted} 中断", "Output root {root} · {n} cells: ⏵{running} running / ✓{done} done / ⏸{interrupted} interrupted"). zh wording note: the maintainer's ruling sketch says 「输出根 {path} · {n} 对」 but the 2026-10-15 approved terminology table (binding, strings.py:24-26) fixes zh output root = 结果目录 and cell = 训练项 — the ruling's wording is direction, the table governs the committed copy.
    4. tests/tui/test_strings_phase11.py inventory (sanctioned by the i18n+inventory gate): EXPECTED_MON_CONSTANTS += MON_STATE_INTERRUPTED, MON_CONTEXT_HEADER; MON_CELL_STATE_CONSTANTS += MON_STATE_INTERRUPTED; MON_STATE_GLYPHS becomes {"◌", "⏵", "✓", "✗", "⊘", "●", "○", "⏸"} (⠋ dropped — no constant carries it anymore; every stateful constant still opens with its glyph).
    tui/screens/monitor.py:
    5. compose (~line 989-1009): yield Label("", id="mon-context-header") immediately after the #mon-title-bar Horizontal, before #mon-discovered-region. _render_context_header(): not running or no attached root -> update(""); else a single-row Text (no_wrap=True so it never pushes the layout) of S.MON_CONTEXT_HEADER.format(root=self._attached_root.name, n=len(self._cell_rows), running=..., done=..., interrupted=...) where the three counts are computed over the same entry_fold outputs _render_cells derives (fold each row once per render pass — reuse the fold results across the header and the row cells in the same method chain, no double derivation). Call it wherever _render_cells is called (both scan handlers, on_resize, the mount/recompose path). Empty-rows edge: attached with zero rows renders the line with n=0 and zero counts (honest, never blank-when-attached).
    6. _cell_state_cells() (~line 130-139): add CELL_INTERRUPTED: (S.MON_STATE_INTERRUPTED, "$text-muted") — the call-time dict keeps the CR-01 live-language re-derivation; the CellDetailModal seed/fraction lines inherit the new state word automatically.
    7. _render_cells ordering (~line 1657-1672): replace the plain sorted(rows_map) with a group sort — group 0 = fold running (key: (-newest_mtime or 0, row key) so freshest first, mtime-None last), group 1 = failed/interrupted/queued/unrecognized folds (row key ASC), group 2 = completed folds (row key ASC). Extend the _set_table_rows diff pass (~line 728-778): when the desired row-key ORDER differs from the table's current order, remove+re-add rows in the desired order (Textual DataTable has no move-row API); the existing cursor-key re-pin (move_cursor scroll=False) already preserves the operator's row identity across the reorder. Unchanged order -> the existing in-place update path, zero added churn on steady ticks.
    8. MonitorBackend evidence threading (~line 304-396): one private _live_evidence() helper -> (live_roots tuple, matrices dict): live_roots = launcher.live_sweeps() UNION probe roots (the keys of live_sweep_matrices(), tolerant getattr — a fake launcher without the new method degrades to live_sweeps() alone, the entries_progress precedent); full_scan/frontier_scan thread live_roots from the union (a probed CLI sweep's root classifies running at root level too); cells_view/frontier_scan/entries_progress thread live_pairs = matrices.get(resolved_root, frozenset()) — root absent from the evidence dict = strict miss (interrupted), which is exactly the dead-root case. MonitorLauncherProtocol.live_sweeps() and the [k] kill gate are byte-unchanged (registry-only kill face, Task 1's pin).
    9. Pilot tests in tests/tui/test_pilot_monitor.py (fakes only — D-03 discipline, never real GPU/handles): drive the tick callbacks directly per the file's existing conventions; assert the header Label content, the DataTable row-key order, the reorder-on-flip with cursor identity, and the interrupted glyph-word render. The existing fake service constructs CellRow positionally — unchanged members stay green.
    10. NO changes to the discovered table's rendering/order, ETA cells, [k]/[f]/[t]/[a]/[r] semantics, or the stats line — the ruling pins their behavior (ETA/k/attach/f/log 尾随语义不变).
  </action>
  <verify>uv run --group dev --group tui pytest tests/tui/test_strings_phase11.py tests/tui/test_pilot_monitor.py -q && make lint && make typecheck</verify>
  <done>The header line renders attached-only with the three counts; running rows sort to the top (freshest first) with completed sunk and reordering preserves cursor identity; ⏵/⏸ render consistently in table, detail modal, and header; the strings inventory tripwire passes with the two new constants and the updated glyph vocabulary; the backend threads union live roots + per-root live pairs behind tolerant getattr seams; existing Pilot members green unmodified.</done>
</task>

<task type="auto">
  <name>Task 4: Goldens (D-03 regen, uncommitted) + WINDOWS #34 closure + full-suite gate</name>
  <files>tests/tui/test_snapshots.py, tests/tui/__snapshots__/monitor_running.svg, tests/tui/__snapshots__/monitor_empty.svg, .planning/WINDOWS.md</files>
  <precondition>The Task 1-3 commits are on the working branch and the live hyenadna sweep (started ~22:10, output finetuned-smoke) may still be running on this box — it is never signalled or disturbed; this task only regenerates SVGs and edits planning docs.</precondition>
  <action>
    1. BEFORE regenerating: sha256sum every tests/tui/__snapshots__/*.svg and record the hashes (the comparison baseline).
    2. tests/tui/test_snapshots.py: extend _running_monitor_service (~line 511) with ONE interrupted pair row (a PlantHelixSeek-style dead pair — fixture DATA so the monitor golden demonstrates ⏸ and the live-on-top ordering alongside ⏵ and the header). This is the only edit to the module: no factory, drive function, or assertion weakens (document the fixture addition in the commit body).
    3. Regen: make snapshot-update (the ONLY regeneration path, maintainer-gated D-03; plain pytest --snapshot-update does nothing in this fallback lane).
    4. sha256sum again and compare: every NON-monitor SVG must be byte-identical; monitor_running.svg is expected to differ (header line + ⏵/⏸ glyphs + ordering); monitor_empty.svg differs only if the empty screen's render actually changed — by design the unattached header is empty, so it may come out byte-identical; report whichever outcome holds, never force a diff.
    5. uv run --group dev --group tui pytest tests/tui/test_snapshots.py -q green against the WORKING TREE.
    6. DO NOT commit the regenerated SVGs (git add must skip both monitor_*.svg). The committed tree fails test_snapshots on exactly those two until the maintainer's D-03 review lands them — the accepted 261016-vxr #29 pattern. Leave them as working-tree changes and name them in the SUMMARY for the D-03 review.
    7. .planning/WINDOWS.md: row 34 (line ~51 + its JSON entry) -> resolved: status fixed, reason naming this quick task (three-state derivation + live-matrix evidence + ⏸ glyph; the PlantHelixSeek/dnamamba residue now derives interrupted), resolved_at now. Append row 35 (deviation, tests/tui/__snapshots__/monitor_running.svg): monitor_running.svg (and monitor_empty.svg if it differed) regenerated via make snapshot-update, deliberately UNCOMMITTED pending maintainer D-03 review — the #29 verbatim shape — status open. Mirror both in the JSON block; bump front-matter total_count 34 -> 35. One obligation one row; do not touch any other row.
    8. Full gate: make lint && make typecheck && make test. Read the actual counts at execution time; the invariant is the baseline MEMBERSHIP (2026-10-17: 1F/1869P where the 1F is the machine-local storage-overview member) — zero existing-member regressions, every new test green, node lane 26/26, test_snapshots green in the working tree. On any unexpected golden or member red: STOP and report (the mad discipline), never widen the change to chase green.
    9. Write .planning/quick/261017-uwr-slot-5-monitor-ux-overhaul-context-heade/261017-uwr-SUMMARY.md per the summary template: what landed per ruling item (1)/(2)/(3), the derivation table (state x evidence -> glyph), the argv-matrix + probe design notes, the golden regen outcome + sha evidence for the D-03 review, WINDOWS #34/#35, and the optional read-only live-probe observation if performed (below).
    10. OPTIONAL read-only probe (never committed, the 12-05 throwaway-probe precedent): a one-off python -c calling probe_cli_sweeps() + run_config.argv_matrix to confirm the LIVE hyenadna sweep (output finetuned-smoke) is found with its 3-pair matrix — evidence the real path sees the real sweep. Strictly read-only; if the sweep has finished by then, skip silently.
    Commits: PLAIN messages, zero attribution trailers, no push. The two SVGs stay out of every commit.
  </action>
  <verify>make lint && make typecheck && make test && test -n "$(git status --porcelain tests/tui/__snapshots__)"</verify>
  <done>monitor goldens regenerated via make snapshot-update and left UNCOMMITTED (both named in the SUMMARY for D-03); every non-monitor SVG sha-identical; tests/tui/test_snapshots.py green in the working tree with the one-row fixture addition; WINDOWS #34 resolved in place and the #35 golden-deviation row recorded (markdown + JSON + total_count); full suite at the baseline membership with all new tests green and node 26/26; SUMMARY written.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| other processes -> TUI | probe_cli_sweeps reads /proc/<pid>/cmdline of processes this TUI does not own (CLI-launched run_sweep and, on a shared box, anything else) — untrusted argv data crosses into the monitor's liveness evidence |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-uwr-01 | Spoofing / Info disclosure | probe_cli_sweeps + live_sweep_matrices | low | mitigate | Probe output is DISPLAY-ONLY evidence (cell/entry glyphs, header counts); it never gates launches, kills, or exits — the kill face stays registry-handle-only (Task 1 pin). Parsing is total (any malformed cmdline skips the pid, never crashes the cadence); roots resolve absolute; raw argv is never rendered to the operator. |
| T-uwr-02 | DoS | probe_cli_sweeps /proc iteration | low | mitigate | Bounded numeric-entry iteration, per-pid skip-on-error, cheap filesystem reads only (no subprocess per probe), called from the existing D-09 workers at most a few times per 2s/60s tick — never per row (the maintainer's no-ps-per-row ruling). |
| T-uwr-SC | Tampering | package installs | high | mitigate | No package-manager installs anywhere in this task (zero new dependencies, uv groups untouched) — the legitimacy gate is vacuous here; kept as the reserved row confirming no install task exists. |
</threat_model>

<verification>
- make lint && make typecheck green after every task.
- make test at the baseline membership (read live counts; 1F machine-local member tolerated exactly as-is) with every new test green and node 26/26.
- tests/tui/test_snapshots.py green in the working tree; exactly the monitor goldens may differ; every other SVG sha256-identical.
- Working tree carries the regenerated monitor_*.svg UNCOMMITTED; git log shows plain commits with zero attribution trailers; nothing pushed.
- WINDOWS.md: #34 resolved, #35 open (D-03 pending), total_count 35.
</verification>

<success_criteria>
- The maintainer scenario renders: attaching to a root like finetuned-smoke shows 「结果目录 finetuned-smoke · 5 训练项：⏵1 运行 / ✓2 完成 / ⏸2 中断」(zh) with the live row on top — dead residue pairs show ⏸ 中断 instead of masquerading as running (WINDOWS #34 closed).
- Kill-left checkpoint residue derives interrupted; live-matrix pairs derive running/queued; live_pairs=None call paths are byte-identical to today (existing suite members unmodified).
- The live sweep running on this box was never disturbed; Pilot/unit tests used fakes throughout.
</success_criteria>

<output>
Create `.planning/quick/261017-uwr-slot-5-monitor-ux-overhaul-context-heade/261017-uwr-SUMMARY.md` when done
</output>
