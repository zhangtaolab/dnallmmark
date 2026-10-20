# Phase 14: 编排运行视图与失败恢复 - Pattern Map

**Mapped:** 2026-10-20
**Files analyzed:** 8 (3 modify, 1 new artifact, 3 test extensions, 1 conditional)
**Analogs found:** 8 / 8 (every file composes over Phase 12/13 seams verified in-tree)

All analog paths below are git-TRACKED (verified via `git ls-files`).

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `pipeline/dispatch_core.py` (MODIFY: state v2 + renderer + re-run branch + lane cache_dir + rerun_of) | service / orchestrator | event-driven (state transitions) | itself — Phase 13 engine (`_write_state`, `_claim_payload`, `claim_cell`) | exact |
| `pipeline/run_sweep_shard.py` (MODIFY: `--cleanup` mode + combo refusals + re-run flag routing) | CLI entry / mode router | request-response (CLI → verify → gate → act) | `run_merge` + A6 refusal block in its own `main()` | exact |
| `script/export_runs.py` (MODIFY: `--dry-run` walk+count, no writes) | utility / batch | batch (file-tree walk) | its own `load_run_records` walk + `main()` | exact |
| `schemas/dispatch_state.json` (NEW) | config / contract | — | existing 14 schemas in `schemas/` (e.g. `schemas/flops_report.json`) + Phase 8/9 jsonschema tests | role-match |
| `tests/test_dispatch_core.py` (EXTEND) | test | — | its own harness (`make_child_spawner`, `run_cli`, spy/ENOSPC idioms) | exact |
| `tests/test_sweep_shard.py` (EXTEND) | test | — | its own merge fixtures (`make_worker_pair`, `run_merge_cli`) | exact |
| `tests/test_export_runs.py` (EXTEND) | test | — | existing dry-run-less unit tests in same file | role-match |
| `Makefile` (ONLY if a new pipeline sibling module exists) | config | — | `PHASE13_MODULES` wildcard-existence guard (Makefile:181,191) | exact idiom |

## Pattern Assignments

### `pipeline/dispatch_core.py` — state extension + renderer + re-run (service, event-driven)

**Analog:** itself (Phase 13 engine); the seams below are the exact insertion points.

**State shape + single write choke point** (`dispatch_core.py:634-641`, state build at `:1184-1192`):

```python
def _write_state(state_path, state):
    """Atomically write ``dispatch_state.json`` (single writer, P10)."""
    _atomic_write_json(state_path, state)

# :1184-1192 — the payload Phase 14 EXTENDS (schema_version 1 → 2, additive
# queue_depth / workers[] / failures per D14-01; frozen in schemas/dispatch_state.json
# in the SAME commit, D14-04):
    state = {
        "schema_version": DISPATCH_STATE_SCHEMA_VERSION,
        "mode": "dispatch",
        "run_id": run_id,
        "status": "running",
        "started_at": started_at,
        "updated_at": started_at,
        "counts": dict(counts),
    }
    _write_state(state_path, state)  # BEFORE any claim (mode evidence)
```

Renderer (D14-02/03) hooks here — render the FROZEN state payload itself under `state_lock`, `print(..., flush=True)` (block-buffering pitfall; cover with pty lane). A NEW state write must be added at claim time (today first per-cell write is finalize, `:781`).

**Claim mechanics for re-run (D14-07 genealogy)** — `claim_cell` O_EXCL create-or-refuse (`dispatch_core.py:288-314`):

```python
    path = Path(ledger_dir) / claim_filename(cell)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    except FileExistsError:
        return None   # SC3 structural refusal — today silently SKIPS
```

`claim_filename` (`:242-270`) is keyed by cell identity only → a fresh O_EXCL on a re-run cell EEXISTs against the failed claim. Planner must pick a genealogy scheme (research recommends archive-copy + atomic replace of the canonical slot; `rerun_of` links to the archive). Adjacent mechanics to copy: `overwrite_claim` (`:346-367`, tmp+`os.replace`), tolerant `read_claim` (`:317-343`, corrupt → `{}` → requeue, never trust), `_atomic_write_json` (`:370-385`).

**Claim payload / lane flags (D14-06)** — `_claim_payload` (`dispatch_core.py:400-435`) with the live lane dict (`:1237-1243`) — **GAP: `cache_dir` absent** though it sits in `context` at `:1233`:

```python
        "lane": {
            "peft": sweep_args.peft,
            "config_variant": config_variant,
            "subset_file": subset_file_abs,
            "effective_batch_size": sweep_args.effective_batch_size,
            "num_train_epochs": sweep_args.num_train_epochs,
        },
```

The `_claim_payload` docstring already names Phase 14 MGPU-04 as the lane consumer. Replay must be tolerant of pre-Phase-14 claims lacking `cache_dir` (`lane.get(...)` absent-parity). Re-run branch must sit BEFORE the `--models` refusal (`:888-896`) and the `--seeds` argparse-code-2 death; reuse the CR-01 filter discipline at `:1061-1085` (`run_sweep.load_failure_pairs` + `base_model_name` join — discipline, not the manifest reader).

**Worker loop / locks** (`dispatch_core.py:644-699`): `queue_lock` guards pending pops, `state_lock` guards counts+state writes — the queue_depth snapshot semantics decision (Pitfall 3) plays out here.

---

### `pipeline/run_sweep_shard.py` — `--cleanup` mode + refusals (CLI router)

**Analog:** its own `main()` A6 block + `run_merge` (`run_sweep_shard.py:1161-1184`):

```python
    args, passthrough = parse_args()
    if args.merge and args.mode == "dispatch":
        sys.exit(
            "[Error] --mode dispatch cannot combine with --merge: ...")
    if args.merge:
        return run_merge(args, passthrough)
    if args.mode == "dispatch":
        import dispatch_core   # lazy import (cycle-breaking precedent)
        return dispatch_core.run_dispatch(args, passthrough, spawner=spawner, clock=clock)
```

`--cleanup` becomes a fourth sibling in exactly this shape, with A6-style combo refusals (cleanup×merge, cleanup×dispatch-mode, stray passthrough, `--models`) and an injectable runner seam for the export subprocess.

**Refusal diagnostics (D14-08 precedent)** — lane-equality refusal (`run_sweep_shard.py:944-964`): collect-all over `_lane_signature` per flag, naming the value per root; adapt to name the differing flag **per cell**. `_canonical_lane_value` (`:649-670`) canonicalizes deterministically.

**Dispatch-root refusal (D14-11)** — reuse verbatim `_root_has_dispatch_evidence` (`:728-775`, evidence-based: `dispatch_state.json` / `dispatch_ledger` / `orchestrator_mode` manifest marker — never directory shape) + the named-refusal builder shape at `:778-785`:

```python
def _dispatch_merge_refusal(path):
    return (
        f"dispatch root {path} needs no merge — dispatch mode writes "
        "ONE shared root (MGPU-06); refusing before any copy ...")
```

**Removal target naming authority** — `worker_root` (`run_sweep_shard.py:200-216`): `Path(f"{base}-mgpu-w{index}")` — the ONLY place worker root names are derived; `--cleanup` must remove via this function, never re-format strings. Collect-all exit idiom: `if problems: sys.exit(f"[Error] {'; '.join(problems)}")` (`:991-992`). New flags are additive `parser.add_argument` entries (the `--mode` precedent, `:372-384`) so the static passthrough stays byte-identical (Pitfall 8).

---

### `script/export_runs.py` — `--dry-run` (utility, batch walk)

**Analog:** its own walk + main. Module top imports numpy/yaml/scipy (`:117-119`) — the orchestrator must reach it ONLY via `sys.executable` subprocess with an injectable runner seam (never a direct import; stdlib-headless). Tests MAY import in-process (conftest puts `script/` on sys.path; data group rides in `make test`).

- Walk authority: `load_run_records(root)` (`export_runs.py:498-551`) — walks `{root}/{model}/{task}/seed_{n}/run_record.json`, `FileNotFoundError` on missing root, loud abort on malformed.
- `export_runs_tree` (`:745-895`) walks AND writes — the `--dry-run` flag short-circuits before writes (walk + count + print). Surgical preference: flag on `main()` (`:898-957`), no refactor.

---

### `schemas/dispatch_state.json` (NEW, config/contract)

**Analog:** the 14 existing tracked schemas in `schemas/` (e.g. `schemas/flops_report.json`, `schemas/run_template.json`) + the jsonschema-based consumer tests from Phases 8/9 (`jsonschema >=4.26.0` already in dev group). Freeze the v2 shape (queue_depth, workers[], failures, timestamps) in the SAME commit as the writer change + `DISPATCH_STATE_SCHEMA_VERSION` bump + gen_progress keep-parsing test (D14-04).

---

### `tests/test_dispatch_core.py` / `tests/test_sweep_shard.py` / `tests/test_export_runs.py` (EXTEND, test)

**Analog:** the existing harness in the same files.

**Per-cell scripted fake child — the D14-15 fixture primitive** (`tests/test_dispatch_core.py:210-256`): `make_child_spawner(calls, exit_for=None)` derives the cell dir exactly as the real child does and `exit_for` maps `(save, task, seed) → returncode` — use it to inject failures on BOTH workers. Plus `make_fake_spawner` (`:198-207`), `run_cli(monkeypatch, argv, spawner=None, clock=None)` (`:159-165`), spy-child idiom (`:352-400`), ENOSPC-style monkeypatched `_write_state` wrappers (`:1840`, `:1857`), hand-materialized claims `_write_hand_claim` (`:1397-1406`).

```python
        code = 0
        if exit_for is not None:
            code = exit_for.get((save, task, seed), 0)
```

Cleanup tests reuse merge fixtures in `tests/test_sweep_shard.py`: `write_manifest` (:853), `make_lane_pair` (:884), `make_worker_pair` (:1051), `run_merge_cli` (:1129), `_snapshot_tree` (:1111-1127). pty lane precedent: `tests/tui/test_pty_driver.py` (pexpect 4.9.0, dev group). Static byte-identity pins to re-run in every affected verify: `test_mode_static_explicit_matches_default` (:1257), `test_static_mode_explicit_pins_argv_roots_and_logs` (:2139).

---

### `Makefile` (conditional, config)

**Analog:** `PHASE13_MODULES := $(foreach s,pipeline/dispatch_core.py,$(if $(wildcard $(s)),$(s)))` (Makefile:181), appended to the ruff line at :191. Only needed if the renderer becomes a new pipeline sibling (`PHASE14_MODULES`); keeping it in `dispatch_core.py` means zero Makefile change. `ci.yml` stays byte-identical (D14-16).

## Shared Patterns

### Atomic single-writer JSON
**Source:** `pipeline/dispatch_core.py:370-385` (`_atomic_write_json`: tmp + `os.replace`; `_dump_json_handle` = `indent=4, ensure_ascii=False, sort_keys=True`)
**Apply to:** every state/claim/schema-adjacent write in this phase. Never hand-roll a new writer.

### Collect-all fail-fast refusals
**Source:** `pipeline/run_sweep_shard.py:991-992` (`if problems: sys.exit(f"[Error] {'; '.join(problems)}")`) and the `problems.append(...)` blocks in `main()` (:1185-1264)
**Apply to:** `--cleanup` validation, re-run lane-diff refusal (D14-08), combo refusals.

### Named, evidence-based refusals (never shape inference)
**Source:** `_root_has_dispatch_evidence` + `_dispatch_merge_refusal` (`run_sweep_shard.py:728-785`)
**Apply to:** D14-11 dispatch-root "needs no cleanup" error (base root AND every worker root — defense-in-depth, the `run_merge` precedent at :879-884).

### Tolerant reads that fail SAFE
**Source:** `read_claim` (`dispatch_core.py:317-343` — corrupt → `{}` → requeue, never crash-or-trust)
**Apply to:** ledger scan for failed cells, lane replay over stale pre-Phase-14 claims (`lane.get("cache_dir")`).

### Injectable seams (spawner / clock / runner)
**Source:** `seam = subprocess.Popen if spawner is None else spawner` (`dispatch_core.py:1176`); `make_fake_spawner` (`tests/test_dispatch_core.py:198-207`)
**Apply to:** the export dry-run subprocess (`runner=subprocess.run` default, tests inject), the confirmation gate (`input` monkeypatch), renderer output.

### Frozen naming authorities
**Source:** `worker_root` (`run_sweep_shard.py:200-216`), `claim_filename` (`dispatch_core.py:242-270`), run_sweep constants (`run_sweep.py:309-316`)
**Apply to:** cleanup removal targets, re-run claim genealogy names. Import the function; never re-derive the string.

### Lazy import for cycle breaking
**Source:** `import dispatch_core` inside `main()` and `_root_has_dispatch_evidence` (`run_sweep_shard.py:749-753, 1181`) — dispatch_core imports run_sweep_shard at its top
**Apply to:** any new sibling module that needs dispatch_core constants.

## No Analog Found

None — all files compose over verified Phase 12/13 seams. Genuinely new state machines (frozen v2 schema shape, `rerun_of` genealogy, cleanup confirmation gate) are covered by the design sketches in `14-RESEARCH.md` §Code Examples.

## Metadata

**Analog search scope:** `pipeline/`, `script/`, `schemas/`, `tests/`, `Makefile` (all directly read; RESEARCH.md line citations cross-checked against the live tree)
**Files scanned:** 8 analog files (dispatch_core, run_sweep_shard, run_sweep, export_runs, 3 test files, Makefile) + schemas/ listing
**Pattern extraction date:** 2026-10-20
