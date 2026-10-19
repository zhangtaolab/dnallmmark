# Phase 12: Multi-GPU Orchestration & Console Hardening - Pattern Map

**Mapped:** 2026-10-13
**Files analyzed:** 14 (new/modified, from 12-RESEARCH.md Recommended Structure)
**Analogs found:** 12 with codebase analogs / 14 total (2 no-analog, research substitutes)

> **Dispatch correction:** `script/get_task_performance.py` no longer exists (deleted at 04-05; see `tests/conftest.py:25-27`). Its role as the script/ conventions analog is taken by `script/export_runs.py` (+ `script/summarize_comparison.py`). All analog paths below are git-TRACKED (verified via `git ls-files`, 7/7 non-mirror).
>
> **Research substitute principle:** the genuinely new algorithms — LPT sharding, merge SHA256-verify, the fallback snapshot harness, the dismiss() override — have probe-verified code shapes in `12-RESEARCH.md` §Code Examples and §Areas 2/5/8/9. Those excerpts are the substitute source where no codebase analog exists.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `pipeline/run_sweep_shard.py` (NEW) | CLI orchestrator (entry script) | batch / process spawn | `pipeline/run_sweep.py` + `tui/services/sweep_launcher.py:_spawn` | exact (composition of two live seams) |
| `script/gen_progress.py` (NEW) | offline generator script | batch / file-I/O | `script/export_runs.py` (docstring/main/argparse) + `tui/services/sweep_monitor.py` (data source) | exact |
| `dnallm-mark/progress.html` (NEW) | page shell (HTML) | request-response (static fetch) | `dnallm-mark/finetuning.html` | exact (copy shell verbatim, minus CDN script) |
| `dnallm-mark/js/progress.js` (NEW) | page controller (component) | request-response | `dnallm-mark/js/finetuning.js` | exact |
| `dnallm-mark/css/progress.css` (NEW) | page-specific stylesheet | — | `dnallm-mark/css/task.css` (page-specific-file precedent) + `css/components.css:183-204` progress classes | exact |
| `tui/screens/run_config.py` (EDIT) | TUI screen (focus fix) | event-driven | its own `run_config.py:1389` focus pattern | exact (in-file pattern) |
| `tests/test_sweep_shard.py` (NEW) | test | batch (dry-run manifests) | `tests/test_sweep.py` | exact |
| `tests/tui/test_snapshots.py` (NEW) | test (golden corpus) | transform (SVG export) | `tests/tui/test_pilot_monitor.py` (run_test/fixture idioms) | role-match (export_screenshot is new) |
| `tests/tui/test_pilot_run_config.py` (EDIT) | test (Pilot) | event-driven | itself (existing B-recipe scaffolding) | exact |
| `tests/tui/test_gen_progress.py` (NEW) | test | file-I/O (golden JSON) | `tests/test_sweep.py` (dry-run manifest assertions) + `tests/tui/test_import_lock.py` env pinning | role-match |
| `dnallm-mark/js/config.js` (EDIT) | config | — | its own `NAV_LINKS` block :63-70 | exact |
| `dnallm-mark/js/data.js` (EDIT) | data-access layer | request-response | its own `loadDataManifest()` :85-102 | exact |
| `dnallm-mark/css/styles.css` (EDIT) | CSS entry | — | its own `@import` list (task.css precedent) | exact |
| `README.md` (EDIT) | docs | — | existing README link patterns | exact |
| `docs/multi-gpu.md` (NEW) | docs | — | phase-11 runbook/UAT prose (no code analog; RESEARCH Area 10 draft is the substitute) | no-analog |
| `Makefile` (EDIT) | build targets | — | existing `snapshot:` target (SHA256 manifest discipline, Makefile ~:75-95) | exact |

## Pattern Assignments

### `pipeline/run_sweep_shard.py` (CLI orchestrator, batch/process-spawn)

**Analog 1 (module shape):** `pipeline/run_sweep.py`
**Analog 2 (spawn discipline, copy VERBATIM):** `tui/services/sweep_launcher.py:473-484`

**Module-docstring + argparse pattern** (`run_sweep.py:1-130`, `:295-461`): large docstring stating output layout, invocation/cwd contract, failure boundary; then `parse_args()` with `parser.add_argument("--flag", type=str, default=None, help="...")` — every flag carries a long help string explaining WHY (English, D-10). Copy this docstring depth for the orchestrator: frozen `{root}-mgpu-w{i}` naming, disjointness proof summary, killpg recipe, merge semantics, and the D-05 other-machine boundary all belong in the module docstring.

**Argparse shape to copy** (`run_sweep.py:295-328`):
```python
def parse_args():
    parser = argparse.ArgumentParser(
        description="Drive the model x task x seed fine-tuning sweep matrix "
                    "(run_finetune.py per cell)")
    parser.add_argument(
        "--output-root", type=str, default="./finetuned",
        help="Sweep output root (default: ./finetuned, resolved absolute; "
             "cells land under {root}/{model}/{task}/seed_{seed}/)")
```
Differences: `--workers`, `--gpus "0,1"`, `--merge` (mode flag), `--dry-run`, `--include-checkpoints`; validation is collect-all fail-fast like `_validate_filters` (`run_sweep.py:594`) — `sys.exit(f"[Error] {'; '.join(problems)}")` (`:1016`).

**Import-of-sibling-module precedent** (the orchestrator imports `enumerate_matrix`/validators from `run_sweep`, never re-implements):
```python
import run_sweep  # conftest/tests put pipeline/ on sys.path
# house precedent: tui/services/sweep_launcher.py:88 does exactly this
```

**Worker spawn pattern — copy VERBATIM from** `tui/services/sweep_launcher.py:473-484`, adding ONE env key:
```python
proc = seam(                              # seam = injectable spawner (testability)
    list(argv),
    start_new_session=True,               # each worker = its own process group
    cwd=str(PIPELINE_DIR),
    env={**os.environ,
         "PYTHONUNBUFFERED": "1",
         "CUDA_VISIBLE_DEVICES": str(gpu_i)},   # the ONLY delta from the launcher
    stdout=tee_handle,                    # per-worker sibling log {root}-mgpu-w{i}.log
    stderr=subprocess.STDOUT,
)
```
Note the `seam = self._spawner if spawner is None else spawner` injectable-executor idiom at `:475` — the orchestrator copies it so `tests/test_sweep_shard.py` can inject a fake spawner (CPU-testable, the D-05 discipline).

**Worker argv composition**: worker = ordinary `run_sweep.py --models <shard_i> --output-root {root}-mgpu-w{i} ...` — `--models` filter semantics reused verbatim (`run_sweep.py:300-305`). argv always a LIST, never a shell string (T-03-10, `run_sweep.py:1067-1090` `build_argv`).

**Deterministic JSON writes** (`run_sweep.py:1210-1213`) — merge mode reuses this exact helper shape:
```python
def _write_json(path, payload):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4, ensure_ascii=False, sort_keys=True)
```

**Manifest structure** (`run_sweep.py:1519-1532`): matrix dict `{models, tasks, seeds, output_root}` + `_manifest_payload(matrix, records, sweep_flags)`; failures always written even when empty. Merge mode: cells union, `output_dir` rewritten to merged root, `matrix.models/tasks/seeds` unioned; lane flags (`sweep_flags`) must be EQUAL across workers or refuse collect-all (Pitfall 6).

**No-analog pieces (research substitutes):**
- LPT greedy bin-pack by `size (M)` (registry read precedent: `pipeline/models_info.json`, key in `CARD_KEYS` at `script/export_runs.py:330-341`) — RESEARCH Area 2, ~10 lines.
- `--merge` copy + SHA256 (hashlib/shutil) with the data-artifact allowlist (`run_record.json`, `final_metrics.json`, `trainer_state.json`, `seed_result.json`, `flops_report.json`, `frac_*/` recursion; NOT `checkpoint-*/` or `runs/`) — RESEARCH Area 5 + `export_runs.py` walk (`:340`, `:500-562`) proves the JSON-only consumer scope.
- Aggregated exit table (per-worker exit code + root + log + failed-cell count).

---

### `script/gen_progress.py` (offline generator, batch/file-I/O)

**Analog:** `script/export_runs.py` (script conventions) + `tui/services/sweep_monitor.py` (data source — import, never re-walk)

**Module docstring pattern** (`export_runs.py:1-80`): Purpose / Direction of truth / Behavior / numbered map-join-aggregate-emit sections; states CWD sensitivity. gen_progress's docstring: input roots → output JSON, the run-from-repo-root note, `--group tui` env requirement (platformdirs), never both worker-roots-and-merged-root warning.

**Argparse main() pattern** (`export_runs.py:897-930`):
```python
def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(...)
    parser.add_argument("--input-root", type=Path, default=REPO_ROOT / "finetuned", ...)
```
Differences: positional `ROOT` (nargs="*") defaulting to `sweep_monitor.DEFAULT_OUTPUT_ROOTS` (`sweep_monitor.py:78-81`), `--output` default `dnallm-mark/data/progress/sweep.json`. `# ===== Configuration =====` block + `if __name__ == "__main__": sys.exit(main())` per house style.

**The sys.path bootstrap — inline the conftest contract** (RESEARCH §Code Examples, sourced from `tests/conftest.py:40-44` + `tests/tui/conftest.py:24`):
```python
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))              # tui (package-qualified)
sys.path.insert(0, str(REPO_ROOT / "pipeline")) # run_sweep, artifact_loader (top-level)
from tui.services import sweep_monitor          # textual-free by tests/tui/test_import_lock.py
```

**Emission — serialize the scanner's dataclasses verbatim** (`sweep_monitor.py:143-235`, frozen field names ARE the web data contract):
- `full_scan(roots, now=...)` `:468` → per-root `SweepSummary(root, state, done, total, newest_mtime)`
- `stats(root, expected_total=None, ..., now=)` `:961` → `SweepStats(done, total, current, elapsed_seconds, eta)`
- `cells_view(root, expected_seeds=None)` `:739` → `tuple[CellRow(model, task, seeds)]`, `CellSeed(seed, state, fraction_states)`
- Machine vocabularies `:111-138`: `finished/running/artifacts_only`, `completed/failed/skipped/running/queued`, `pending/point/range/none`.
- `newest_mtime` deliberately DROPPED from JSON (churn signal); `generated_at` = generator clock ISO-8601 UTC (`run_sweep._utc_now_iso()` `:1190-1192` precedent); `_write_json` semantics (sort_keys, indent 4, ensure_ascii False) for byte-stable regeneration.
- Per-root tolerance: no artifacts → `print(f"  [Skip] ...")` line, root absent from JSON (the house per-file skip idiom).

---

### `dnallm-mark/progress.html` (page shell)

**Analog:** `dnallm-mark/finetuning.html` — copy verbatim, then: title `DNALLM Mark | Progress`, description, **delete the SheetJS CDN `<script>` line** (UI-SPEC: no CDN scripts on this page), swap module src to `./js/progress.js`. Keep `.navbar-container`, `.hero-container`, `main.content` with `.model-selector-wrapper`, `.leaderboard-container`, footer, end-of-body module script.

### `dnallm-mark/js/progress.js` (page controller)

**Analog:** `dnallm-mark/js/finetuning.js` (253 lines, whole-file pattern)

**Imports + class skeleton** (`finetuning.js:6-26`):
```javascript
import DataAPI from './data.js';
import { renderNavbar } from './navbar.js';

class FineTuningPage {
  constructor() {
    this.state = { selectedModel: null, ... };  // single this.state object
    this.init();
  }
  async init() {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.setup());
    } else { this.setup(); }
  }
```

**Setup order — navbar FIRST, try/catch** (`finetuning.js:28-46`): `renderNavbar()` before any I/O (WR-03: failed fetch still leaves navigation); then `loadData → renderHero → render* → bindEvents`; catch logs `console.error('Failed to setup ...')`. ProgressPage's catch additionally renders the fetch-error `.empty-state` per UI-SPEC.

**Render pattern** (`finetuning.js:64-110`): null-guarded container, template-literal innerHTML, `.leaderboard > .table-wrapper > table.arena-table` markup verbatim for the cell table; the `-- All Models --` select option at `:71`.

**Event binding / delegation on persistent containers** (`finetuning.js:227-249`): `document.getElementById('model-select')?.addEventListener('change', ...)`; delegation via `e.target.closest('.clickable-row')` on the container that survives re-render. ProgressPage adds `.tag[data-status]` delegation (the `main.js:477-486` `data-filter` grammar).

**Copy constants**: a `PROGRESS` object literal at module top (UI-SPEC copy table — `TITLE`, `SUBTITLE`, `LEGEND`, `FILTER_ALL_MODELS` verbatim `-- All Models --`, empty-state titles/hints, `FOOTER_STAMP`). `formatValue`-style defensive N/A rendering (`finetuning.js:141-145`) is the `N/A` precedent; `generated_at` rendered verbatim from JSON, never a client clock (`data.js:78-83` comment).

### `dnallm-mark/css/progress.css` (page-specific stylesheet)

**Analog:** `css/task.css` (page-specific-file precedent) + the reused classes at `css/components.css:183-204` (`.progress-bar/.progress-fill/.progress-text`) and `:53` (`.tag/.tag.active`). New rules ONLY: 5 state-glyph classes (`.cell-state--done/-running/-failed/-skipped/-queued`) + stat-card grid refinement — every value from `css/variables.css` tokens, no hardcoded hex (CLAUDE.md rule). `@import './progress.css';` appended LAST in `css/styles.css`.

### `dnallm-mark/js/config.js` / `js/data.js` (EDITS)

- `config.js:63-70`: append `{ name: 'Progress', url: './progress.html' }` after Submit — one line.
- `data.js`: add `loadProgress()` copying `loadDataManifest()` (`data.js:85-102`) exactly — `cache.progress` slot, `fetch('./data/progress/sweep.json')`, `if (!response.ok) throw new Error(...)`, catch → `console.error` → re-throw.

### `tui/screens/run_config.py` (EDIT — delta B focus fix, the ONE TUI change)

**Analog:** in-file pattern `run_config.py:1384-1391` (the filter-Enter refocus precedent):
```python
if event.input.id == "cfg-filter":
    self.query_one("#cfg-picker", PickerList).focus()
    return
```

**Targets:** the 6 modal classes at `:580` PreviewModal, `:605` ProblemsModal, `:631` EnvBlockModal, `:662` E2PhraseModal (explicit `self.dismiss()` at `:717`, `:726`), `:730` ChoiceModal (dismiss at `:762`); `ConfirmModal` lives in `selection.py:1109` — DO NOT edit; local one-line subclass `_GateConfirmModal(ConfirmModal)` for the `:1621` push site.

**No-analog (research substitute — RESEARCH §Code Examples):** one shared base `_PickerReturnModal(ModalScreen)` overriding `dismiss()` → `super().dismiss(result)` + `below.query_one("#cfg-picker", PickerList).call_after_refresh(picker.focus)` via `self.app.screen_stack[-2]`. Probe-verified: all 6 escape bindings route through `Screen.action_dismiss → self.dismiss()`, so this covers all 10 dismiss paths. Zero selection.py edits, zero new strings, zero styles.tcss changes.

### `tests/test_sweep_shard.py` (NEW — tier-1)

**Analog:** `tests/test_sweep.py`

- **Docstring-as-behavior-spec** (`test_sweep.py:1-113`): bullet list of pinned behaviors.
- **`run_cli` helper** (`:183-186`): `monkeypatch.setattr(sys, "argv", full_argv); run_sweep_shard.main()` — copy for the shard module.
- **Machine-independence env pin** (`:131-152` `_pin_custom_registry_overlay`): pin `DNALLMMARK_CUSTOM_REGISTRY_DIR` + `XDG_CONFIG_HOME` to a fresh tmp dir — REQUIRED here too (worker argv derives from registries).
- **Dry-run disjointness test** (`:214-246` precedent): per worker run `--dry-run --models <shard_i> --output-root {tmp}/w{i}`, parse the manifest, assert pairwise-disjoint `output_dir` sets, union == full enumeration, `matrix.models == shard` (RESEARCH Area 4 test shape).
- **argv LIST capture** (`:531-542`): `monkeypatch.setattr(module.subprocess, "run", fake_run)` — the orchestrator's fake SPAWNER asserts `start_new_session=True`, `env["CUDA_VISIBLE_DEVICES"] == str(i)`, cwd == pipeline/, argv is a list.
- Merge tests: two tiny fixture worker trees → `--merge` → assert copied set == union, SHA256 verified, manifest `output_dir` rewritten, unequal lane flags refuse collect-all.

### `tests/tui/test_snapshots.py` (NEW — fallback goldens)

**Analog:** `tests/tui/test_pilot_monitor.py` — `app.run_test(size=(120, 40))` idiom (`:442`, `:461`...) and the `_three_state_scan()` deterministic fixture factory (`:424`) + `FakeMonitorService(scans=[...])` injection (`:440`). Copy the fake-injection style for all 8 golden apps; monitor golden #6 adds one `finetuned-mgpu-w0` `SweepSummary` (delta A proof).

**No-analog (research substitute — RESEARCH §Code Examples, probe-proven 0.44s/3 tests):**
```python
async def _export(app_factory):
    app = app_factory()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        return app.export_screenshot()   # byte-deterministic SVG string
golden = (SNAP_DIR / f"{golden_id}.svg").read_text(encoding="utf-8")
assert svg == golden
```
No plugin, no syrupy, no pyproject change. Regeneration = `make snapshot-update` (module docstring documents it as the ONLY path — Pitfall 4).

### `tests/tui/test_pilot_run_config.py` (EDIT — B1-B5)

**Analog:** itself — the existing fake-services boot (`:46-80` imports, `_model_entry` fixture builders) is the scaffolding. Add per UI-SPEC delta B: `p`+`esc` → assert `app.focused` is `PickerList#cfg-picker`; choice modal + `esc`; gate `[enter]` → confirm/`esc`; E2' modal `esc`; then press `3` and assert the data-manager screen is active. Deterministic fakes, no sleeps (inherited discipline).

### `tests/tui/test_gen_progress.py` (NEW)

**Analog:** `tests/test_sweep.py` dry-run manifest assertions (fixture tree → run main() → compare parsed JSON) — here: build a fixture sweep root (records + manifest), run `gen_progress.main([...])`, assert the golden JSON (frozen dataclass field names, state_counts, dropped `newest_mtime`). Follow the `_three_state_scan`-style deterministic fixtures and the conftest env-pinning idiom.

### `Makefile` (EDIT)

**Analog:** the existing `snapshot:` target (SHA256-manifest + freeze discipline, Makefile ~:75-95) and the `PHASE6/7/8` existence-guard lists. Add `snapshot-update:` maintainer target invoking the regeneration script explicitly (`--group dev --group tui` env, matching `test:`'s group pattern). Optionally add `pipeline/run_sweep_shard.py` to the lint list's explicit files.

### `docs/multi-gpu.md` (NEW) — no codebase analog

Substitute source: RESEARCH Area 10's 9-step other-machine smoke procedure (verbatim draft provided) + Area 1/3/5/6 CLI examples + the DDP-vs-sharding matrix (`run_finetune.py:1357, 1542` WORLD_SIZE/LOCAL_RANK scaffolding). Plus README one-line link (D-04).

## Shared Patterns

### Deterministic JSON I/O
**Source:** `pipeline/run_sweep.py:1210-1213` (`_write_json`: sort_keys=True, indent=4, ensure_ascii=False)
**Apply to:** `run_sweep_shard.py` (merged manifest/failures), `gen_progress.py` (sweep.json — byte-stable regeneration).

### Collect-all fail-fast validation
**Source:** `run_sweep.py:594` `_validate_filters` + `sys.exit(f"[Error] {'; '.join(problems)}")` (`:1016`)
**Apply to:** shard orchestrator (--workers > #models, gpu arity, registry names via imported run_sweep validators, merge lane-flag equality), gen_progress (bad roots), merge mode (missing worker roots).

### Injectable executor/spawner seam
**Source:** `run_sweep.py` executor param; `sweep_launcher.py:475` (`seam = self._spawner if spawner is None else spawner`)
**Apply to:** `run_sweep_shard.py` worker spawner — tests inject a fake; real path = Popen with `start_new_session=True` + `CUDA_VISIBLE_DEVICES`.

### Fetch-wrapper + navbar-first page controller (web)
**Source:** `js/data.js:85-102`, `js/finetuning.js:28-46`, `js/navbar.js:18-21`
**Apply to:** `progress.js` + `DataAPI.loadProgress()`.

### Argv LISTs, never shell strings (T-03-10)
**Source:** `run_sweep.py:1067-1090`, `sweep_launcher.py:477-484`
**Apply to:** every worker argv the orchestrator builds.

## No Analog Found

| File | Role | Data Flow | Substitute |
|------|------|-----------|------------|
| `docs/multi-gpu.md` | docs | — | RESEARCH Area 10 verbatim procedure draft + Area 1/5/6 command examples |
| LPT sharding / SHA256 merge / dismiss() override / export_screenshot goldens (logic inside otherwise-analoged files) | algorithm/test-harness | batch / event | RESEARCH §Code Examples — all four probe-verified live (Areas 2, 5, 8, 9) |

## Metadata

**Analog search scope:** `pipeline/`, `tui/services/`, `tui/screens/`, `script/`, `tests/`, `tests/tui/`, `dnallm-mark/js/`, `dnallm-mark/css/`, `dnallm-mark/*.html`, `Makefile`
**Files scanned:** ~20 (targeted reads)
**Tracked-source gate:** all named analogs verified via `git ls-files` (no capability-mirror paths involved)
**Pattern extraction date:** 2026-10-13
