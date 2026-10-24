# Phase 13: 动态调度核心 (Dynamic Dispatch Core) - Research

**Researched:** 2026-10-20
**Domain:** CPU-provable multi-GPU work-queue orchestration over the existing run_sweep/run_sweep_shard seams (Python stdlib, zero new dependencies)
**Confidence:** HIGH (every seam quoted verbatim from live code read this session; milestone research 2026-10-20 already HIGH and NOT re-derived)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Worker Process Shape**
- Thin per-GPU worker loop owned by the dispatcher: claim cell → spawn one child per cell → wait → record → claim next (research Shape 1; run_sweep stays the single-sweep authority, run_finetune argv surface untouched)
- Child argv built by importing `run_sweep.build_argv()` verbatim — orchestrator composes, never re-implements (D-07 discipline)
- Cell enumeration via `run_sweep.enumerate_matrix` unchanged; priority tiers reapplied for queue order
- Single dispatcher owns an in-memory queue; idle workers pull the next cell (no cost-prediction — explicitly out of scope)

**Mode Declaration & CLI Grammar (MGPU-06)**
- Explicit `--mode {static,dispatch}` on `run_sweep_shard.py`, default `static`; legacy static launch stays byte-identical (test-pinned)
- Dispatch mode writes ONE shared root with ordinary per-cell subpaths (`{root}/{model}/{task}/seed{k}`) — worker-independent; `--merge` refuses dispatch-mode roots with a named "dispatch roots need no merge" error; static merge untouched
- Mode is recorded by the run (dispatch state / manifest marker) so refusal is evidence-based, never inferred from directory shape
- Help text in English, matching the run_sweep/run_sweep_shard CLI convention (D-10)

**Claim Ledger & Resume (MGPU-02)**
- Per-cell claim file via `os.open(O_CREAT|O_EXCL)` in a dispatch ledger dir inside the shared root (tee O_EXCL precedent); JSON content: cell key, lane flags, gpu, pid, run_id, timestamps
- Child `trainer_state.json` marker stays the authoritative completion guard; the dispatcher additionally skips ledger-completed cells on relaunch (D-06 two-layer guard extended)
- Singleton dispatcher lock per root (O_EXCL): a second orchestrator on the same root is refused loudly; stale claims from a dead run are reclaimable precisely because no second dispatcher can exist — no lease/timeout protocol
- Worker death mid-cell ⇒ claim is unfinished ⇒ relaunch requeues it; exactly-once (no duplicates, no orphans) is proven by the fake-children kill test (SC2 — the P1 acceptance test)

**Testing & CI Shape (SC1/SC2/SC5)**
- Kill-test harness uses fake children through the existing `main(spawner=...)` seam: scripted exits incl. SIGKILL mid-cell; assertions read the ledger + artifact counts
- Dry-run enumeration committed as a golden: byte-identical across runs AND equal to static-mode enumeration for identical inputs
- CI stays CPU-only: no GPU, no dnallm, no N>1 device assumptions anywhere; fake children + injected seams only
- Full CPU gates stay green (pytest/ruff/ty + node lanes); zero CI changes; new code keeps the stdlib-headless contract

### Claude's Discretion
- Internal module split inside `run_sweep_shard.py` vs a new sibling module (e.g. `dispatch_core.py`) — follow the existing compose-as-sibling-modules pattern and file-size ergonomics
- Exact ledger directory name/layout and claim-file naming, provided O_EXCL semantics and the frozen naming tests cover it
- Queue hand-off mechanics (in-process thread vs select loop over Popen handles) as long as single-dispatcher semantics hold

### Deferred Ideas (OUT OF SCOPE)
- Live terminal table + `dispatch_state.json` consumer contract → Phase 14 (MGPU-03)
- Cross-worker failure re-run + post-merge verify/cleanup helper → Phase 14 (MGPU-04/05)
- N=2 real-GPU smoke + subsets → Phase 15 (VAL)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MGPU-01 | Orchestrator dispatches (model×dataset×seed) cells as a work queue — idle GPU workers pull the next cell; each cell runs entirely on exactly one GPU; enumeration is deterministic and dry-run-provable | Enumeration reuses `run_sweep.enumerate_matrix` + `apply_priority_order` verbatim (Seam Inventory §1/§2); workers = thin loops claiming from ONE in-memory queue, each cell one child spawned via `run_sweep.build_argv` + the verbatim static spawn discipline (one `CUDA_VISIBLE_DEVICES` per worker); dry-run golden pattern + static-union equality test (Test Patterns) |
| MGPU-02 | Cell output paths are worker-independent (one root, ordinary cell subpaths) with an exactly-once O_EXCL claim ledger; killing a worker mid-cell and relaunching re-dispatches that cell to exactly-once completion (test-pinned) | ONE shared root + `cell_dir_for` layout (live code quoted — note `seed_{seed}`, not `seed{k}`); O_EXCL claim ledger design (Claim Ledger §1) grounded in the sweep_launcher tee precedent and POSIX EEXIST semantics; resume algorithm (skip = marker OR ledger-completed; requeue = stale claim) + fake-children kill-test harness (Test Patterns) |
| MGPU-06 | Legacy static model-sharding mode coexists behind the same CLI with explicit mode declaration; `--merge` refuses mixed-mode roots loudly; dispatch-mode roots need no merge (documented) | `--mode {static,dispatch}` default `static` routed in `main()` with the static path byte-identical (Mode Surface); evidence-based mode marker (dispatch_state.json written before first claim) checked in `run_merge`'s collect-all validation block (Merge Refusal); static-mode "launch never writes the base root" pin reconciled (Pitfall 6) |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Tech stack**: Python (pipeline/ + script/); no frontend work in this phase
- **Fix discipline**: surgical, no opportunistic refactors — dispatch mode is ADDITIVE to `run_sweep_shard.py` (+ optional new sibling module, a discretion decision); `run_sweep.py`/`run_finetune.py` argv surfaces untouched
- **CI feasibility**: GitHub Actions CPU-only — no GPU, no `dnallm` package, no N>1 device assumptions; "zero CI changes" = `.github/workflows/ci.yml` byte-identical (a Makefile lint-list extension for a new module does NOT touch ci.yml — see Gates)
- **Conventions**: Google-style docstrings with RST markup, module docstrings with `See also:`, `# ===== Configuration =====` discipline, stdlib-headless pipeline orchestration code (no torch import at module top), English help text (D-10), collect-all fail-fast refusals via `sys.exit(f"[Error] {'; '.join(problems)}")`
- **GSD enforcement**: work flows through GSD commands; this file is the phase research artifact

## Summary

Phase 13 turns `pipeline/run_sweep_shard.py` (1253 lines, launch+merge modes) into a three-mode entry (`--mode {static,dispatch}` over the existing launch/merge) whose dispatch mode runs ONE dispatcher process holding a deterministic in-memory (model×task×seed) cell queue, feeds idle per-GPU worker loops, and lands every cell at worker-independent paths under ONE shared root guarded by an O_EXCL claim ledger and a singleton dispatcher lock. Everything the dispatcher needs already exists as importable, CPU-safe functions in `run_sweep.py`: `enumerate_matrix` (line 533), `apply_priority_order` (line 957), `load_priority_tiers` (line 861), `build_argv` (line 1139), `cell_dir_for` (line 1092), `PIPELINE_DIR` (line 309), and the `MANIFEST_NAME`/`FAILURES_NAME`/`RESUME_MARKER`/`METRICS_NAME` constants (lines 312–316). The orchestrator COMPOSES these — never re-implements (D-07). The one genuinely new parsing problem is that dispatch mode must consume the enumeration/lane axes (`--tasks --seeds --peft --curve --config-variant --priority-file` + the pass-through lane family) that today live in the `parse_known_args` remainder; the recommended answer is re-parsing the remainder through `run_sweep.parse_args()` itself via a `sys.argv` swap, keeping run_sweep the single flag owner.

The load-bearing correctness machinery is the exactly-once trio: (1) the child-side `trainer_state.json` marker stays authoritative (`run_finetune.py:1320-1321` — `if os.path.exists(outdir + "trainer_state.json"): continue`), extended by (2) the dispatcher's ledger-completed skip on relaunch, and (3) the singleton O_EXCL dispatcher lock per root, which is what makes "no lease/timeout protocol" sound — stale claims are reclaimable precisely because a second dispatcher structurally cannot exist. The P1 acceptance test (SC2) drives this entirely through the existing `main(spawner=None, clock=None)` seam with fake children: script a SIGKILL-returning child mid-cell, let run 1 drain, relaunch over the same root, and assert from the ledger + artifact counts that every cell completed exactly once. All of this is CPU-provable with the exact test idioms already proven in `tests/test_sweep_shard.py` (fake spawner capturing argv/kwargs, per-argv scripted returncodes, autouse overlay pin, real-subprocess dry-run chain).

**Primary recommendation:** implement dispatch mode as a new `run_dispatch(args, passthrough, spawner, clock)` sibling of `run_merge` inside `run_sweep_shard.py` (extract to `pipeline/dispatch_core.py` only if the file exceeds ergonomics — the merge mode is the precedent for keeping modes in-file), re-parse the remainder through `run_sweep.parse_args()` for the enumeration/lane namespace, spawn each cell with the verbatim static spawn kwargs minus worker-root naming, and pin SC1/SC2/SC3/SC4 with the fake-spawner idioms already in the shard suite. Do not write `sweep_manifest.json`/`run_record.json` for dispatch roots this phase (see Open Question 1).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Cell enumeration + determinism | `run_sweep.enumerate_matrix` (imported, unchanged) | dispatcher applies `apply_priority_order` for queue order | Single authority (D-07); enumeration must stay byte-identical between modes (SC1) |
| Queue ownership + claim hand-off | dispatcher process (in-memory) | — | Single dispatcher = exclusivity by construction; workers pull when idle (MGPU-01) |
| Cell argv composition | `run_sweep.build_argv` (imported verbatim) | dispatcher threads lane flags as kwargs | Frozen child argv surface; orchestrator never re-implements (D-07) |
| Child process spawn + GPU pin | dispatcher worker loop (spawner seam) | — | One child per cell, one `CUDA_VISIBLE_DEVICES` per worker, `start_new_session=True` verbatim discipline |
| Per-cell artifact writes | `run_finetune.py` child (untouched) | — | Child owns `final_metrics.json`/`flops_report.json`/`trainer_state.json` (WR-13 order); the dispatcher never writes cell artifacts |
| Completion truth | child `trainer_state.json` marker | dispatcher claim ledger (completed state) | Two-layer guard (D-06 extension): marker authoritative, ledger-completed is the relaunch skip |
| Double-claim impossibility | O_EXCL claim file (filesystem) | in-memory queue exclusivity | Structural refusal (SC3), defense-in-depth over the single-queue hand-off |
| Single-dispatcher enforcement | O_EXCL lock file per root | — | Refuses a second orchestrator loudly; underwrites no-lease claim reclaim |
| `dispatch_state.json` | dispatcher (single writer, atomic) | — | Phase 13 minimal (queue/claims ground truth + mode evidence); Phase 14 adds the consumer contract |
| Mode declaration + merge refusal | `run_sweep_shard.parse_args` / `run_merge` validation block | dispatch mode marker written before first claim | Evidence-based refusal, never directory-shape inference (MGPU-06) |
| Static-mode behavior | existing `main()` launch path (byte-identical) | — | Default `--mode static`; all existing tests must pass unmodified |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `subprocess` | 3.13 (venv) | per-cell child spawn via the injectable spawner seam | existing `_DEFAULT_SPAWNER = subprocess.Popen` [VERIFIED: pipeline/run_sweep_shard.py:197] |
| Python stdlib `os` (`os.open` with `O_CREAT\|O_EXCL`) | 3.13 | claim files + singleton lock | `os.open(path, O_CREAT\|O_EXCL)` fails EEXIST→`FileExistsError` when the path exists — guaranteed even through a planted symlink (no-follow) [CITED: docs.python.org/3/library/os.html + man7.org/linux/man-pages/man2/open.2.html]; in-repo precedent opens tee logs with mode `"x"` + numeric-suffix retry cap [VERIFIED: tui/services/sweep_launcher.py:763-798] |
| Python stdlib `threading` OR `selectors`-free poll loop | 3.13 | worker loops inside the dispatcher | discretion item (see Worker Shape); threads recommended — `Popen.wait()` blocks release the GIL |
| Python stdlib `json`/`pathlib`/`argparse` | 3.13 | ledger/state serialization, paths, `--mode` flag | `_write_json` discipline: `json.dump(payload, f, indent=4, ensure_ascii=False, sort_keys=True)` [VERIFIED: pipeline/run_sweep.py:1308-1311] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `run_sweep` (sibling module import) | repo HEAD | enumeration, argv, layout, constants | always — the dispatcher composes it [VERIFIED: pipeline/run_sweep_shard.py:182] |
| `registry_loader` (sibling module import) | repo HEAD | registry views for validation joins | model-name join (already used at `run_sweep_shard.py:1111-1115`) |
| `directories_config` (sibling module import) | repo HEAD | directories.json seeding for lane flags | if dispatch threads cache/model/dataset/log roots with file-tier defaults [VERIFIED: pipeline/run_sweep.py:1650-1670] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `sys.argv` swap + `run_sweep.parse_args()` over the remainder | hand-rolled `_registry_dir_from_passthrough`-style readers for ~11 flags | readers duplicate argparse choices/types/`nargs='?'` semantics and drift; the swap keeps run_sweep the single flag owner (recommended) |
| threads per worker | single-thread poll loop over `Popen.poll()` | poll loop makes scripted-exit ordering fully deterministic and avoids any thread-safety surface, at the cost of a hand-rolled wait loop; both are sanctioned by the discretion clause |
| in-file `run_dispatch` in `run_sweep_shard.py` | new `pipeline/dispatch_core.py` sibling | sibling module matches the compose pattern (flops_counter/registry_loader precedent) if the file grows past ergonomic size; merge-mode precedent favors in-file |

**Installation:** nothing — zero new dependencies (milestone STACK.md verdict, re-confirmed: every capability lands with stdlib + sibling imports).

**Version verification:** no packages to verify against registries; the runtime is the repo venv: `.venv/bin/python` → Python 3.13.14, uv 0.13.0, node v26.4.0, system python3 3.14.6 [VERIFIED: local probe this session].

## Package Legitimacy Audit

No external packages are installed, added, or recommended by this phase. **Packages removed due to [SLOP] verdict:** none. **Packages flagged as suspicious [SUS]:** none. (Gate not applicable — zero-dependency phase.)

## Architecture Patterns

### System Architecture Diagram

```text
                        python pipeline/run_sweep_shard.py --mode dispatch ...
                                        |
                          parse_args() -> (args, remainder)
                                        |
              --mode routing in main(spawner, clock)  (default static = today's path, byte-identical)
                                        |
                        run_dispatch(args, remainder, spawner, clock)
                                        |
        remainder re-parsed via run_sweep.parse_args()  (sys.argv swap; run_sweep stays flag owner)
                                        |
        enumerate_matrix(models, tasks, seeds, registry_dir, peft, fractions, variant)
                                        |
        apply_priority_order(cells, tiers)      <-- queue order (priority tiers reapplied)
                                        |
        [1] acquire singleton O_EXCL dispatcher lock on the shared root (refuse loudly if held)
        [2] write mode evidence (dispatch_state.json) BEFORE any claim
        [3] relaunch filter:  skip cell iff trainer_state.json marker exists  OR  claim.state == completed
                              stale claims (claimed, unfinished) -> requeued
                                        |
              ONE in-memory queue of pending cells
                                        |
        +----------------+----------------+ ... (one worker loop per --workers entry)
        | worker i @ gpus[i]             |
        |  claim cell (O_EXCL claim file: cell key, lane flags, gpu, pid, run_id, timestamps)
        |  argv = run_sweep.build_argv(model, task, seed, SHARED_ROOT, <lane kwargs>)
        |  child = spawner(argv, start_new_session=True, cwd=PIPELINE_DIR,
        |                   env={**os.environ, PYTHONUNBUFFERED:"1",
        |                        CUDA_VISIBLE_DEVICES:gpus[i]}, stdout=worker tee,
        |                   stderr=STDOUT)
        |  wait() -> exit code
        |  record: marker+final_metrics present? claim->completed : claim->failed (NO in-run requeue)
        |  claim next ...
        +--------------------------------+
                                        |
        queue drained -> verdict table, lock released (finally)
                                        |
   (external) --merge --output-root <root>:  run_merge validation refuses dispatch-evidence
   roots with the named "dispatch roots need no merge" error; static merge byte-identical
```

A reader can trace the primary use case: CLI entry → mode routing → deterministic enumeration → lock/state evidence → filtered queue → per-GPU claim/spawn/wait/record loops → exactly-once artifacts under the ONE root.

### Seam Inventory (live code, read this session)

**1. Orchestrator entry — `pipeline/run_sweep_shard.py`**

- Injectable seam + default spawner [VERIFIED: pipeline/run_sweep_shard.py:1042, 197]:
  ```python
  def main(spawner=None, clock=None):
  ```
  ```python
  _DEFAULT_SPAWNER = subprocess.Popen
  ```
- Flag surface: the parser owns `--workers --gpus --models --output-root --dry-run --merge --include-checkpoints` and returns `parser.parse_known_args(argv)` — everything unrecognized is the verbatim remainder [VERIFIED: pipeline/run_sweep_shard.py:297-396]. `--mode {static,dispatch}` joins this parser (default `static`); it must NOT change what lands in the remainder for existing command lines.
- Mode routing today [VERIFIED: pipeline/run_sweep_shard.py:1067-1069]:
  ```python
  args, passthrough = parse_args()
  if args.merge:
      return run_merge(args, passthrough)
  ```
  `run_dispatch(args, passthrough, spawner, clock)` slots in exactly here on `args.mode == "dispatch"`.
- Frozen naming authority [VERIFIED: pipeline/run_sweep_shard.py:200-216]:
  ```python
  def worker_root(base_root, index):
      base = Path(base_root)
      return Path(f"{base}-mgpu-w{index}")
  ```
- Spawn discipline to copy verbatim (minus root naming) [VERIFIED: pipeline/run_sweep_shard.py:1201-1212]:
  ```python
  procs.append(seam(
      list(argv),
      start_new_session=True,
      cwd=str(run_sweep.PIPELINE_DIR),
      env={
          **os.environ,
          "PYTHONUNBUFFERED": "1",
          "CUDA_VISIBLE_DEVICES": gpus[i],
      },
      stdout=tee,
      stderr=subprocess.STDOUT,
  ))
  ```
- Static-mode validations that must NOT fire in dispatch mode: empty-shard refusal (`--workers exceeds the ... model(s)`, lines 1120-1124), LPT sharding (line 1164), frozen-root collision guard (lines 1131-1151 — dispatch has no sibling roots), and the static-only spawn argv composition (lines 1179-1187, which forwards `--models`/`--output-root` of the worker root to a `run_sweep.py` process — dispatch spawns `run_finetune.py` children instead, so this whole block is bypassed).
- Merge refusal insertion point: `run_merge`'s collect-all `problems` list, before `if problems: sys.exit(f"[Error] {'; '.join(problems)}")` [VERIFIED: pipeline/run_sweep_shard.py:766-898]. MERGE_ALLOWLIST verbatim [VERIFIED: pipeline/run_sweep_shard.py:498-504]:
  ```python
  MERGE_ALLOWLIST = (
      "run_record.json",
      "final_metrics.json",
      "trainer_state.json",
      "seed_result.json",
      "flops_report.json",
  )
  ```

**2. Sweep driver — `pipeline/run_sweep.py`** (everything below imported, never re-implemented)

- Constants [VERIFIED: pipeline/run_sweep.py:309-316]:
  ```python
  PIPELINE_DIR = Path(__file__).resolve().parent
  RUN_FINETUNE = PIPELINE_DIR / "run_finetune.py"

  MANIFEST_NAME = "sweep_manifest.json"
  FAILURES_NAME = "sweep_failures.json"
  RECORD_NAME = "run_record.json"
  RESUME_MARKER = "trainer_state.json"
  METRICS_NAME = "final_metrics.json"
  ```
- Enumeration [VERIFIED: pipeline/run_sweep.py:533-534, 576-577, 610-615]:
  ```python
  def enumerate_matrix(models_filter, tasks_filter, seeds, registry_dir,
                       peft="none", fractions=None, config_variant="none"):
  ```
  Returns `list[tuple]`: sorted `(model, task, seed)` triples — or `(model, task, seed, fraction)` quadruples under `--curve`; the model component is the ALIAS name under peft/variant lanes (`{model}+lora` etc., `head` keeps base for `("evo2_1b_base", "megaDNA_updated")` = `HEAD_KEEP_BASE_NAMES` [VERIFIED: pipeline/run_sweep.py:328]).
- Priority order [VERIFIED: pipeline/run_sweep.py:957]: `def apply_priority_order(cells, tiers):` — stable reorder, rank `(tier index, entry specificity)`, best rank wins, unmatched keep `sorted()` order. Tiers load+validate via `load_priority_tiers(path, registry_dir)` (line 861, SystemExit collect-all).
- Cell layout [VERIFIED: pipeline/run_sweep.py:1092-1102]:
  ```python
  def cell_dir_for(output_root, model, task, seed, fraction=None):
      cell = Path(output_root) / model / task / f"seed_{seed}"
      if fraction is not None:
          cell = cell / f"frac_{fraction}"
      return cell
  ```
  ⚠ The CONTEXT decision text writes the subpath as `{root}/{model}/{task}/seed{k}` — the LIVE layout is `seed_{seed}` (underscore). Always derive paths through `cell_dir_for`; never re-derive from the CONTEXT shorthand.
- Child argv builder [VERIFIED: pipeline/run_sweep.py:1139-1143, 1225-1233]:
  ```python
  def build_argv(model, task, seed, output_root, peft="none",
                 train_fraction=None, subset_file=None,
                 effective_batch_size=None, num_train_epochs=None,
                 cache_dir=None, config_variant="none",
                 model_root=None, dataset_root=None, log_dir=None):
  ```
  ```python
  argv = [
      sys.executable,
      str(RUN_FINETUNE),
      "--target_model",
      str(base_model_name(model, peft, config_variant)),
      "--target_dataset", str(task),
      "--seed", str(seed),
      "--output_dir", str(output_root),
  ]
  ```
  NOTE: `--output_dir` receives the sweep ROOT (not the cell dir) — the child derives the cell subdir itself. Optional flags append exactly two elements each when present, zero when absent (pinned tail order `--model_root`, `--dataset_root`, `--log_dir` last).
- `launch_subprocess` (line 1258) is `subprocess.run(argv, cwd=PIPELINE_DIR, check=True)` — the dispatch worker does NOT reuse it (it needs Popen + tee + env), it reuses `build_argv` and copies the kwargs discipline.
- Resume authority in `run_matrix` [VERIFIED: pipeline/run_sweep.py:1531-1534]:
  ```python
  if (cell_dir / RESUME_MARKER).exists():
      # Seed-scoped resume marker (G1): only THIS (model, task,
      # seed) cell is done — a sibling seed still runs.
      record["status"] = "skipped"
  ```
- Failure boundary to mirror in the dispatch worker's per-cell verdict [VERIFIED: pipeline/run_sweep.py:1592 + docstring lines 85-102]: a cell is failed when the executor raises `subprocess.SubprocessError`/`OSError` OR exits 0 with no `final_metrics.json` in the cell dir (CR-02 — the child's blind-except isolation swallows training failures at exit 0) OR the metrics file is present but not valid JSON (WR-11).
- Manifest payload builder (for the dry-run plan artifact if manifest-shaped) [VERIFIED: pipeline/run_sweep.py:1390-1428]: `_manifest_payload(matrix, records, sweep_flags=None)` — five identity keys + `**flags`; `_write_json` = `json.dump(..., indent=4, ensure_ascii=False, sort_keys=True)` (lines 1308-1311).
- `parse_args()` takes NO argv parameter — it reads `sys.argv` [VERIFIED: pipeline/run_sweep.py:331]. Dispatch-side reuse therefore needs the swap idiom (Pattern 3).
- `--seeds` is `required=True` in run_sweep's parser; `--effective_batch_size` is `nargs="?" const=16`; `--config-variant` has `choices=["head","probe","curve"]`; variant×peft combination is refused collect-all in `main()` (lines 1796-1802).
- Lane-flag resolution recipe to replicate (directories.json merge + absolute resolution) [VERIFIED: pipeline/run_sweep.py:1650-1849]: `directories_config.load_directories()` → per-key `flag > file key > default` → `Path(x).resolve()` → `sweep_flags` dict of present keys only.

**3. Child — `pipeline/run_finetune.py`** (read-only this phase)

- Outdir construction (the layout contract both sides agree on) [VERIFIED: pipeline/run_finetune.py:1291, 1306, 1315-1321]:
  ```python
  save_root = output_dir if output_dir else "./finetuned"
  ...
  outdir = f"{save_root}/{model_save_name}/{dataset_name}/seed_{seed}/"
  ...
  if train_fraction is not None:
      outdir = f"{outdir}frac_{train_fraction}/"
  os.makedirs(outdir, exist_ok=True)
  ...
  if os.path.exists(outdir + "trainer_state.json"):
      continue
  ```
- The child writes `final_metrics.json` < `flops_report.json` < `trainer_state.json` LAST (WR-13 three-artifact chain, STATE.md Phase 07 decision) — a dispatcher seeing a child exit 0 without the marker must treat the cell as failed, never complete.

### Pattern 1: Mode Surface (`--mode {static,dispatch}`)

**What:** one new orchestrator-owned flag on the existing `parse_known_args` parser; `main()` routes `static` (or absent) to the byte-identical current path and `dispatch` to `run_dispatch`.
**When to use:** always — MGPU-06.
**Example (shape):**
```python
parser.add_argument(
    "--mode",
    type=str,
    default="static",
    choices=["static", "dispatch"],
    help="Orchestration mode: 'static' (default) = legacy LPT model-sharded "
         "workers under frozen {root}-mgpu-w{i} roots; 'dispatch' = ONE "
         "dispatcher process feeding idle per-GPU workers from a "
         "deterministic cell queue under ONE shared root guarded by an "
         "O_EXCL claim ledger")
```
Guards: `--mode dispatch` + `--merge` → the named "dispatch roots need no merge" refusal (or refuse the combination outright and let the dispatch-root evidence check handle a `--merge` pointed at a dispatch root — pick ONE and pin it); `--mode` + `--merge` for static stays exactly today's behavior. Help text English (D-10).
**Byte-identity proof:** every existing test in `tests/test_sweep_shard.py` invokes the CLI WITHOUT `--mode` → default static → unchanged; add one test pinning `--mode static` explicit == default (identical argv/roots/logs).

### Pattern 2: Claim Ledger + Singleton Lock (MGPU-02)

**What:** a ledger directory inside the shared root (exact name is the sanctioned discretion item — freeze it in tests once chosen), one JSON claim file per cell, plus one O_EXCL dispatcher lock file per root.
**Example (claim create — the tee O_EXCL precedent adapted to `os.open` per the locked decision):**
```python
# Source: adapted from tui/services/sweep_launcher.py:777-791 ("x"-mode tee)
# + POSIX open(2) O_CREAT|O_EXCL EEXIST guarantee
import os, json

def claim_cell(ledger_dir, cell_key, payload):
    """Create-or-refuse one cell claim; returns the claim path or None."""
    path = ledger_dir / claim_filename(cell_key)   # frozen naming, test-pinned
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    except FileExistsError:
        return None  # structurally refused: already claimed
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=4, ensure_ascii=False, sort_keys=True)
    return path
```
Claim JSON content is pinned by the locked decision: cell key, lane flags, gpu, pid, run_id, timestamps (claimed_at; finished_at on completion). Claim state transitions: `claimed → completed | failed`, rewritten by the dispatcher only (single writer under the lock).
**Relaunch algorithm (resume semantics):**
1. Acquire lock (refuse loudly if held — see below).
2. Enumerate the matrix; for each cell: skip iff `cell_dir_for(root, ...) / "trainer_state.json"` exists OR the claim file says completed; otherwise queue (a stale `claimed` claim from a dead run is simply requeued — its file is overwritten at re-claim, safe because the singleton lock guarantees no second dispatcher; no lease, no timeout).
3. Drain; write verdict; release lock in `finally`.
**Double-claim proof (SC3):** the O_EXCL create fails EEXIST for any second claimant — including through a symlinked path (POSIX no-follow guarantee) [CITED: man7.org/linux/man-pages/man2/open.2.html]. Test: attempt to claim a live-claimed cell → refused.
**Singleton lock:** O_EXCL lock file at dispatch start (e.g. inside the ledger dir or root), content = pid + run_id + started timestamp; released in `finally` on normal exit. After a SIGKILLed dispatcher the file is stale — see Open Question 2 for the reclaim policy options (pid liveness check vs documented manual removal).

### Pattern 3: Dispatch-mode Flag Acquisition (the new parsing seam)

**What:** the enumeration/lane axes live in the passthrough remainder; the dispatcher needs them as values.
**Example (recommended — sys.argv swap, zero run_sweep edits):**
```python
def parse_sweep_remainder(passthrough):
    """Re-parse the passthrough through run_sweep's own parser so run_sweep
    stays the single owner of sweep-flag validation (D-07)."""
    old = sys.argv
    try:
        sys.argv = ["run_sweep.py", *passthrough]
        return run_sweep.parse_args()
    finally:
        sys.argv = old
```
This inherits run_sweep's `required=True` seeds, `choices`, `nargs="?"`, and collect-all-adjacent validations for free. Then replicate the `sweep_flags` resolution recipe (directories.json merge + `Path(...).resolve()`) exactly as `run_sweep.main()` does [VERIFIED: pipeline/run_sweep.py:1650-1849] so lane flags thread into `build_argv` with the same absolute-path discipline (D-15). The alternative — extending the `_registry_dir_from_passthrough` reader idiom [VERIFIED: pipeline/run_sweep_shard.py:430-451] to ~11 flags — duplicates argparse semantics and drifts; not recommended.

### Pattern 4: Dispatch Worker Loop (Shape 1, locked)

**What:** one worker loop per `--workers` entry, permanently bound to `gpus[i]`, spawning ONE child per claimed cell.
**Shape (per worker):**
```text
while queue not drained:
    cell = dispatcher hands next pending cell to THIS idle worker
    claim = claim_cell(...)            # O_EXCL; None => already claimed (defensive)
    argv = run_sweep.build_argv(cell.model, cell.task, cell.seed, SHARED_ROOT,
                                peft=..., train_fraction=..., subset_file=...,
                                effective_batch_size=..., num_train_epochs=...,
                                cache_dir=..., config_variant=...,
                                model_root=..., dataset_root=..., log_dir=...)
    child = spawner(list(argv), start_new_session=True,
                    cwd=str(run_sweep.PIPELINE_DIR),
                    env={**os.environ, "PYTHONUNBUFFERED": "1",
                         "CUDA_VISIBLE_DEVICES": gpus[i]},
                    stdout=worker_tee, stderr=subprocess.STDOUT)
    code = child.wait()
    ok = code == 0 and (cell_dir / run_sweep.METRICS_NAME).is_file()   # CR-02
    finalize claim (completed|failed) + update dispatch_state.json
```
Hand-off mechanics (in-process threads vs a poll loop over Popen handles) is the sanctioned discretion item. Threads: simplest, `wait()` releases the GIL. Poll loop: fully deterministic event ordering for tests. Either way single-dispatcher semantics hold (ONE process, ONE queue).
**Failure policy:** failed cells are recorded (claim + state file) and NOT requeued in the same run — Phase 14 owns re-run (assumption A3, confirm in plan).

### Pattern 5: Mode Evidence + Merge Refusal (MGPU-06)

**What:** dispatch mode records itself where `--merge` looks, BEFORE any cell runs.
**How:** `dispatch_state.json` is written at dispatcher startup (status starting/running) — its presence (or the ledger dir's) is the evidence. In `run_merge`'s collect-all validation block, append a problem when the merged target root OR any discovered worker root carries that evidence, yielding the named refusal, e.g. `dispatch root {path} needs no merge — dispatch mode writes ONE root (MGPU-06); refusing to merge dispatch-mode roots`. Static merge behavior stays byte-identical when no evidence is present (existing merge tests must pass unmodified).
**Documentation note:** "dispatch-mode roots need no merge (documented)" — docs/multi-gpu.md rewrite is Phase 18 (DOCS-01); Phase 13 lands the refusal + help text only.

### Pattern 6: Dry-Run Golden (SC1)

**What:** `--mode dispatch --dry-run` enumerates and writes a plan artifact — no children, no cell dirs (mirror run_sweep's dry-run contract: "writes ONLY sweep_manifest.json ... no subprocess, no cell directories" [VERIFIED: pipeline/run_sweep.py:104-108]).
**Recommended shape:** manifest-shaped planned cells through `run_sweep._manifest_payload` with `status: "planned"` and `output_dir = cell_dir_for(root, ...)` — the same projection static dry-runs use [VERIFIED: pipeline/run_sweep.py:1909-1946]. Golden tests: (a) two consecutive dispatch dry-runs → byte-identical artifact (the `_write_json` sort_keys discipline); (b) the planned cell identity set `(model, task, seed)` equals the union of static-mode per-worker dry-run manifests for the same `--models/--tasks/--seeds` (the exact comparison idiom of `test_dry_run_disjointness_in_process` [VERIFIED: tests/test_sweep_shard.py:740-786]) — note output_dirs differ by root BY DESIGN (worker roots vs the one shared root), so equality is over cell identities/relative suffixes, never absolute paths.

### Anti-Patterns to Avoid

- **Re-implementing enumeration/argv/layout in the orchestrator** — the D-07 violation; every path/argv/value derives from `run_sweep.*` imports.
- **Keying anything on worker identity** — cell paths, claims, state entries are worker-independent (P1's root cause in v1.2 was worker-scoped roots).
- **Inferring mode from directory shape** — the refusal must read run-recorded evidence (CONTEXT: "evidence-based, never inferred from directory shape").
- **Treating child exit 0 as completion** — CR-02: exit-0-without-metrics is the child's designed training-failure signal.
- **Requeueing failed cells in-run** — doubles work and muddies the exactly-once proof; Phase 14 owns re-run.
- **Lease/timeout claim protocols** — explicitly ruled out (CONTEXT: "no lease/timeout protocol"); the singleton lock is the whole argument.
- **Editing `run_sweep.py`/`run_finetune.py` argv surfaces** — frozen by tier-1 suites and the TUI composer; Phase 13 touches only `run_sweep_shard.py` (+ optional new sibling module) + tests (+ optional Makefile lint-list line for a new module — NOT ci.yml).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Matrix enumeration | own model×task×seed fan-out | `run_sweep.enumerate_matrix` | alias lanes, fraction expansion, registry joins, frozen determinism already test-pinned |
| Child argv | own flag composer | `run_sweep.build_argv` | the frozen child argv surface (tier-1 + TUI parity); the explicit `--save_model_name` authority prevents the retrain-forever trap |
| Cell paths | own path joins (or the CONTEXT `seed{k}` shorthand) | `run_sweep.cell_dir_for` | layout contract shared with the child's own outdir construction; `seed_{seed}` verbatim |
| Queue priority | own ordering | `run_sweep.load_priority_tiers` + `apply_priority_order` | validated tiers, stable composition over sorted() fallback |
| Exclusive create | ad-hoc "check-then-write" | `os.open(path, O_CREAT\|O_EXCL)` | check-then-write races; O_EXCL is atomic at the filesystem level and symlink-safe [CITED: man7 open(2)] |
| Plan/manifest serialization | own JSON writer | `run_sweep._write_json` discipline (`indent=4, ensure_ascii=False, sort_keys=True`) | byte-determinism goldens depend on it |
| Test fake children | real subprocesses / GPU assumptions | the `make_fake_spawner`/`FakeProc`/monkeypatched-`subprocess.run` idioms | CI is CPU-only, N>1-free (P9, carried constraint) |

**Key insight:** this phase's production code is ~all orchestration over already-frozen seams; the intellectual content is the exactly-once protocol (lock + ledger + marker) and its fake-children proof, not new computation.

## Common Pitfalls

### Pitfall 1: `seed{k}` vs `seed_{seed}`
**What goes wrong:** the CONTEXT decision text writes the subpath as `{root}/{model}/{task}/seed{k}`; the live layout is `seed_{seed}` (underscore) in BOTH `cell_dir_for` [VERIFIED: pipeline/run_sweep.py:1099] and the child's own construction [VERIFIED: pipeline/run_finetune.py:1306]. A hand-derived path from the shorthand breaks marker checks and artifact assertions.
**How to avoid:** derive every path from `run_sweep.cell_dir_for`; never from prose.
**Warning signs:** a test asserting a `seed42` directory; a marker check that never fires.

### Pitfall 2: `--output_dir` carries the ROOT, not the cell dir
**What goes wrong:** fake children (and any new consumer) that assume `--output_dir` is the cell dir write artifacts to the root — the exact 12-05 fixture fault recorded in STATE.md ("the fake child wrote metrics to the root, not the cell dir — --output_dir carries the ROOT").
**How to avoid:** fake children derive the cell dir exactly as the real child does: root + `--target_model`(save name semantics) + `--target_dataset` + `seed_{--seed}` [VERIFIED: the working idiom at tests/test_sweep_shard.py:1545-1566]. Dispatcher-side marker checks use `cell_dir_for`.
**Warning signs:** "executor exited 0 but final_metrics.json is missing" in a green-fake test.

### Pitfall 3: Static-mode validations leaking into dispatch (and vice versa)
**What goes wrong:** the empty-shard refusal (`--workers` > model count), LPT, and the frozen-root collision guard are STATIC-only invariants; firing them in dispatch mode refuses legal launches (dispatch workers are not model-bound). Conversely, running the singleton-lock acquisition on the static path would break static's documented resume-by-relaunch semantics.
**How to avoid:** route mode-specific validation inside `run_dispatch`; keep `main()`'s static prelude shared only where genuinely common.
**Warning signs:** `--mode dispatch --workers 2 --models m1` refusing; static relaunch asking for a lock.

### Pitfall 4: Passthrough-parse drift
**What goes wrong:** hand-rolled readers for `--peft`/`--config-variant`/`--curve`/`--effective_batch_size` mis-handle `choices`, `nargs="?" const=16`, or the variant×peft refusal, silently diverging from run_sweep's validation.
**How to avoid:** the `sys.argv` swap through `run_sweep.parse_args()` (Pattern 3); the remainder is by construction all-run_sweep-owned tokens.
**Warning signs:** a dispatch launch accepting `--peft lora --config-variant probe` (run_sweep refuses the pair collect-all [VERIFIED: pipeline/run_sweep.py:1796-1802]).

### Pitfall 5: Claim-filename aliasing
**What goes wrong:** claim filenames built by naive joining (`f"{model}_{task}_{seed}.json"`) can collide or become unreadable: model aliases contain `+` (`model-a+lora`), task keys contain `__` (`GUE__emp_H3`), fractions are floats (`frac_0.5`). Two different cells must never map to one filename.
**How to avoid:** a frozen, test-pinned encoding (e.g. sanitize `+`/`.`/`/` to fixed escape tokens, or a deterministic digest of the cell tuple with the tuple ALSO stored inside the JSON). The ledger naming is the sanctioned discretion item — but its tests must include an aliasing/collision case.
**Warning signs:** a claim file whose JSON cell key disagrees with its filename.

### Pitfall 6: "Static never writes the base root" pin vs dispatch writing it
**What goes wrong:** the static N=1 smoke asserts `not base.exists()` — "the launch mode writes ONLY frozen sibling roots — never the base root itself" [VERIFIED: tests/test_sweep_shard.py:1656-1662]. Dispatch mode legitimately writes the base root. If mode routing is wrong, that pin (correctly) fails.
**How to avoid:** dispatch writes the base root ONLY in dispatch mode; keep the static assertion untouched as the mode-isolation tripwire; add the mirror assertion (dispatch dry-run creates the base root's plan artifact, no `-mgpu-w{i}` roots).
**Warning signs:** static tests failing after the mode change = routing leak, not a stale test.

### Pitfall 7: Kill-test flakiness from spawn-order coupling
**What goes wrong:** `make_fake_spawner(calls, returncodes=[...])` scripts exits BY CALL INDEX; under multi-worker dispatch the interleaved claim order across workers is scheduler-dependent, so index-scripted SIGKILLs can land on the wrong cell and make SC2 flaky.
**How to avoid:** script the fake spawner PER CELL — parse the spawned argv (`--target_model/--target_dataset/--seed`) and return the scripted code for the targeted cell, 0 otherwise (the per-argv idiom already used by the fake-child in `test_d08_from_failures_rerun_is_isolated_to_w0`).
**Warning signs:** a kill test that passes locally and flakes in CI.

### Pitfall 8: Ledger/state write ordering vs crash windows
**What goes wrong:** writing the mode evidence AFTER the first claim (or the claim after spawning the child) opens windows where a crash leaves the root without evidence or the cell without a claim — breaking both the merge refusal and exactly-once reasoning.
**How to avoid:** strict order: lock → mode evidence (`dispatch_state.json` at startup) → per-cell: claim BEFORE spawn → finalize claim after `wait()` + artifact check. State-file updates are atomic (tmp+rename, single writer — P10 prevention).
**Warning signs:** a merge-refusal test that only passes when the run completed.

### Pitfall 9: `run_sweep.parse_args` SystemExit(2) surface
**What goes wrong:** argparse errors (e.g. missing `--seeds`) exit with argparse's usage text, not the orchestrator's collect-all `[Error]` format — surfacing an unfamiliar failure shape.
**How to avoid:** acceptable as-is (static workers die the same way inside their process today, reported via the verdict table); OR catch and re-emit as a collect-all problem. Pick one, pin it. `--seeds` lives in the remainder, so a dispatch launch without it fails here — that is correct (enumeration is impossible without seeds).

### Pitfall 10: Tee handle lifetime under per-cell children
**What goes wrong:** a per-worker tee opened with a context manager closes before later children write (SIM115 — the documented rationale at run_sweep_shard.py:1193-1198); or per-cell logs multiply unboundedly.
**How to avoid:** hold per-worker (or per-run) tee handles open for the whole drain, close in `finally`; keep the WR-02 fresh-stamp-per-launch discipline via the injectable `clock`.
**Warning signs:** empty worker logs for later cells.

### Pitfall 11: Lock staleness after SIGKILL
**What goes wrong:** a SIGKILLed dispatcher leaves the O_EXCL lock file; the next launch is refused as if a live dispatcher held it — resume (SC2's relaunch) blocked by the very mechanism meant to guard it.
**How to avoid:** decide the reclaim policy in the plan (pid liveness via `os.kill(pid, 0)` + reclaim-with-overwrite, vs documented manual lock removal) — see Open Question 2. The kill test targets CHILD deaths (fake children); a dispatcher-death test may additionally pin the chosen reclaim path.
**Warning signs:** the relaunch leg of the kill test failing on lock acquisition.

## Code Examples

Verified patterns from the live suites — the planner should reference these verbatim in task actions.

### Fake spawner + FakeProc (the SC2/SC3 harness)
```python
# Source: tests/test_sweep_shard.py:199-222
class FakeProc:
    """Minimal Popen stand-in: wait() records the scripted returncode."""
    def __init__(self, returncode=0):
        self.returncode = None
        self._scripted = returncode
        self.waited = False
    def wait(self, timeout=None):
        self.waited = True
        self.returncode = self._scripted
        return self._scripted

def make_fake_spawner(calls, returncodes=None):
    """Build an injectable spawner capturing (argv, kwargs) per call."""
    def spawn(argv, **kwargs):
        calls.append({"argv": list(argv), "kwargs": kwargs})
        index = len(calls) - 1
        code = returncodes[index] if returncodes is not None else 0
        return FakeProc(code)
    return spawn
```
For SC2, prefer the per-cell variant (Pitfall 7): parse `--target_model/--target_dataset/--seed` out of `argv` inside the fake and return `-9` for the targeted cell (a negative `wait()` result is the Popen returncode convention for signal death).

### CLI invocation with the injectable seams
```python
# Source: tests/test_sweep_shard.py:175-182
def run_cli(monkeypatch, argv, spawner=None, clock=None):
    full_argv = ["run_sweep_shard.py", *argv]
    monkeypatch.setattr(sys, "argv", full_argv)
    run_sweep_shard.main(spawner=spawner, clock=clock)
    return full_argv
```

### Fake child that derives the cell dir the way the real child does
```python
# Source: tests/test_sweep_shard.py:1545-1566 (the D-08 re-run proof)
def fake_child(argv, **kwargs):
    if argv[:1] == ["git"]:
        return subprocess.CompletedProcess(argv, returncode=0, stdout="fakehash\n")
    cell_dir = (
        Path(flag_value(argv, "--output_dir"))
        / flag_value(argv, "--target_model")
        / flag_value(argv, "--target_dataset")
        / f"seed_{flag_value(argv, '--seed')}")
    cell_dir.mkdir(parents=True, exist_ok=True)
    (cell_dir / "final_metrics.json").write_text(
        json.dumps({"eval_loss": 0.5, "eval_accuracy": 0.9}), encoding="utf-8")
    (cell_dir / "trainer_state.json").write_text('{"global_step": 1}', encoding="utf-8")
    return subprocess.CompletedProcess(argv, returncode=0)
```
(Note: under `--peft`/`--config-variant` the save name is the ALIAS carried by `--save_model_name`, not `--target_model` — a lane-aware fake must use the save name for the dir.)

### Machine-independence pin (every new test module needs this)
```python
# Source: tests/test_sweep_shard.py:125-131
@pytest.fixture(autouse=True)
def _pin_custom_registry_overlay(tmp_path, monkeypatch):
    """Empty-dir pin over the custom overlay for every test here."""
    pinned = tmp_path / "no-custom-overlay"
    pinned.mkdir()
    monkeypatch.setenv("DNALLMMARK_CUSTOM_REGISTRY_DIR", str(pinned))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(pinned))
```
The root `tests/conftest.py` additionally pins the directories.json XDG config dir per-test [VERIFIED: tests/conftest.py:44-60] — inherited automatically.

### Fixture registry
```python
# Source: tests/test_sweep_shard.py:147-172 — 3 models x 3 tasks (task-y Train=0),
# sizes 100/50/10 pinning lpt partitions [[model-a], [model-b, model-c]] at workers=2
```
Reuse the same shape for dispatch tests (sizes are irrelevant to dispatch — no LPT).

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Static LPT model-sharding (v1.2 Phase 12): models partitioned once, worker roots `{root}-mgpu-w{i}`, merge to consume | Dynamic dispatch: ONE dispatcher + cell queue + shared root + O_EXCL ledger; static coexists behind `--mode` | v1.3 Phase 13 (this phase) | Resume no longer depends on which worker owns a model; tail latency stops being bound by the largest model per shard |
| Marker-skip as the ONLY resume guard (D-06) | Marker (authoritative) + ledger-completed skip (two-layer) | this phase | Relaunch skips provably-finished cells without touching cell dirs |
| `--from-failures` per worker root (lane-blind, 12-04 known limitation) | Ledger records lane flags at claim time (feed for Phase 14's MGPU-04) | this phase (record) / Phase 14 (consume) | Fixes P3 lane-blindness at its source |

**Deprecated/outdated:** nothing is removed — every v1.2 surface stays (byte-identical static mode is a success criterion).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `--workers`/`--gpus` retain their meaning (worker count / per-worker CUDA id strings, arity-validated) in dispatch mode — the same parser flags now count GPU workers pulling from a queue instead of shard owners | Mode Surface, Worker Loop | Low: flags exist and parse identically; only the empty-shard refusal must be mode-gated |
| A2 | Failed cells are NOT requeued within a live dispatch run (recorded in ledger/state; Phase 14 MGPU-04 owns re-run) — inferred from the phase boundary and v1.2 semantics, not stated verbatim in CONTEXT | Worker Loop, Pitfalls | Medium: if in-run retry were desired, SC2's "exactly once" counting must define retry-vs-duplicate; confirm in plan |
| A3 | Phase 13 dispatch roots carry child artifacts + ledger + `dispatch_state.json` but NOT `sweep_manifest.json`/`run_record.json` (no `run_matrix` involvement under Shape 1) | Open Question 1 | Medium: exporter/scanner consumers see a root without a manifest until Phase 14/15 decide the shape; must be an explicit decision |
| A4 | The dispatch dry-run plan artifact is manifest-shaped via `_manifest_payload` (recommended, not locked) | Pattern 6 | Low: any deterministic artifact satisfies SC1; the shape choice affects Phase 14+ tooling |
| A5 | Stale-lock reclaim policy (pid-liveness check recommended over manual removal) — CONTEXT pins "refused loudly" but not the post-SIGKILL path | Open Question 2, Pitfall 11 | Medium: wrong choice blocks SC2's relaunch leg or weakens the singleton guarantee |
| A6 | `--mode dispatch` + `--merge` on one command line is refused (rather than silently ordering modes) | Pattern 1 | Low: either behavior is defensible once pinned |
| A7 | `dispatch_state.json` doubles as the merge-refusal evidence marker (written at startup, before first claim) | Pattern 5, Pitfall 8 | Low: a dedicated marker file works equally well if the state file's write timing is ever delayed |

**Planner gate:** A2, A3, A5 should each become an explicit plan-level decision (or checkpoint) before execution; the rest can ride as documented defaults.

## Open Questions

1. **Manifest / run_record authorship for dispatch roots (A3)**
   - What we know: Shape 1 workers bypass `run_matrix`, so nothing writes `run_record.json` per cell or a root `sweep_manifest.json`; exporters walk `run_record.json`; the scanner falls back to no-manifest churn semantics (`total: null`) for such roots.
   - What's unclear: whether Phase 13 should emit a manifest-shaped artifact on COMPLETION (not just dry-run) so consumers see a familiar root — or defer entirely to Phase 14/15.
   - Recommendation: defer consumer-facing manifest/records to Phase 14 (its MGPU-04/05 own recovery+verify over the ledger anyway); keep Phase 13 to ledger + state + child artifacts, matching the CONTEXT phase boundary ("State-file rendering ... Phase 14"). Record the deferral in the plan.
2. **Stale-lock reclaim after a SIGKILLed dispatcher (A5)**
   - What we know: the lock is O_EXCL per root; normal exit releases it in `finally`; SIGKILL does not.
   - What's unclear: automatic reclaim (pid liveness via `os.kill(pid, 0)`, with pid-reuse caveat) vs documented manual removal (runbook step).
   - Recommendation: pid-liveness check with loud refusal naming the live pid; reclaim (overwrite) only when the recorded pid is provably dead. Cheap, testable with fake pids, preserves the loud refusal for the live case.
3. **Claim-file naming scheme (discretion, must be frozen by tests)**
   - What we know: cell keys contain `+`, `__`, digits, and fraction floats; the ledger naming is explicitly the planner's discretion provided tests freeze it.
   - Recommendation: decide once in the plan (escape-token sanitize or digest-of-tuple), and require an aliasing/collision test (Pitfall 5) plus a frozen-naming test in the pattern of `test_worker_root_and_log_naming_is_frozen`.
4. **Threads vs poll loop (discretion)**
   - What we know: both sanctioned; threads are simplest; poll loop gives deterministic event order.
   - Recommendation: threads + per-cell-scripted fake spawner (Pitfall 7 mitigation) — matches "in-process thread" first-listed reading and keeps the wait loop trivial.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python (repo venv) | all phase code/tests | ✓ | 3.13.14 (`.venv/bin/python`) | — |
| uv | running gates | ✓ | 0.13.0 | — |
| node | JS test lane (unaffected, must stay green) | ✓ | v26.4.0 | — |
| pytest / ruff / ty | CPU gates | ✓ (via `uv run --group dev --group tui`) | pinned by uv.lock | — |
| GPU / dnallm / torch | NOTHING in this phase (CPU-only constraint) | deliberately not required | — | fake children + injected seams |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** none.

Gate commands [VERIFIED: Makefile + .github/workflows/ci.yml]: `make test` (full pytest + `node --test tests/js/*.test.js`), `make test-fast`, `make lint` (ruff over tests/ + the fixed-findings list incl. `PHASE12_MODULES := pipeline/run_sweep_shard.py script/gen_progress.py` — a new `dispatch_core.py` sibling would join via the same existence-guard idiom, a Makefile edit that leaves ci.yml byte-identical), `make typecheck` (ty over pipeline/ among others). "Zero CI changes" constrains ci.yml, which invokes these targets unchanged.

## Security Domain

`security_enforcement: true`, ASVS level 1, block on high. This phase adds a local CLI orchestrator — no network, no auth, no new data stores beyond filesystem artifacts.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | local maintainer CLI; no auth boundary introduced |
| V3 Session Management | no | process lifetime = session; singleton lock is the concurrency guard |
| V4 Access Control | no | no multi-user surface |
| V5 Input Validation | yes | remainder re-parsed through `run_sweep.parse_args()` (argparse choices/types); registry joins via `registry_loader`; collect-all refusals for mode/lock/ledger states; claim filenames must not alias (Pitfall 5) |
| V6 Cryptography | no | no new crypto (merge SHA256 already exists, untouched) |
| V8 Logging | partial | verdict tables + tee logs follow the existing `[Error]`/`[Worker i]` plain-print discipline; no secrets logged (env copies pass through untouched) |

### Known Threat Patterns for local subprocess orchestration

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Shell/argv injection via registry-derived values | Tampering | argv LISTs, never a shell string (T-03-10 discipline carried into every new spawn) |
| Symlink planting on ledger/lock paths (redirect an exclusive create to overwrite an outside target) | Tampering | `O_CREAT\|O_EXCL` fails EEXIST even when the path is a symlink (POSIX no-follow guarantee) [CITED: man7.org/linux/man-pages/man2/open.2.html] |
| Second-dispatcher race (double GPU spend / claim corruption) | Repudiation | singleton O_EXCL lock per root, loud refusal naming the holder |
| Stale-lock pid reuse (false reclaim) | Elevation | lock content records pid+run_id; reclaim only on provable death; loud wording (see Open Question 2) |
| State-file torn writes read by future consumers | Tampering | single-writer + atomic tmp+rename (P10 prevention) |

## Sources

### Primary (HIGH confidence)
- Live code read this session: `pipeline/run_sweep_shard.py` (full), `pipeline/run_sweep.py` (structure + all named seams), `pipeline/run_finetune.py` (outdir/marker sections), `tests/test_sweep_shard.py` (full), `tests/test_sweep.py` (header + idioms + inventory), `tests/conftest.py`, `tui/services/sweep_launcher.py` (O_EXCL tee), `Makefile`, `.github/workflows/ci.yml`, `docs/multi-gpu.md` (structure)
- Milestone research 2026-10-20 (NOT re-derived, per orchestrator instruction): `.planning/research/SUMMARY.md`, `ARCHITECTURE.md` (§A design backbone), `PITFALLS.md` (P1–P3, P9, P10 phase-relevant), `STACK.md` (zero-deps verdict), `FEATURES.md`

### Secondary (MEDIUM confidence)
- [Python docs — os module](https://docs.python.org/3/library/os.html) (O_CREAT/O_EXCL flags) and [Linux open(2) man page](https://man7.org/linux/man-pages/man2/open.2.html) (EEXIST + symlink no-follow guarantee) — web-verified this session; digest cached via research-store

### Tertiary (LOW confidence)
- None — no claim in this file rests on unverified training memory

## Metadata

**Validation architecture:** omitted — `workflow.nyquist_validation` is explicitly `false` in `.planning/config.json`. Test-lane facts the planner still needs (commands, coverage mechanics) are in Environment Availability and Code Examples.

**Runtime state inventory:** omitted — not a rename/refactor/migration phase; no stored data, service config, OS registration, secrets, or build artifacts embed strings this phase renames (mode is additive; no renames).

**Knowledge graph:** disabled in config (`graphify.enabled: false`) — no graph context available or required.

**Confidence breakdown:**
- Standard stack: HIGH — zero new deps; every seam imported and quoted with line numbers
- Architecture: HIGH — mode routing, ledger, lock, and merge refusal all land in read, live code paths; design deltas are clearly marked as recommendations/discretion
- Pitfalls: HIGH — phase-scoped pitfalls derive from read code (seed_ naming, --output_dir ROOT semantics, static-only validations) plus the project's own recorded lessons (12-05 fixture fault, 12-04 lane blindness)
- Test patterns: HIGH — every idiom quoted from the live suites that SC1–SC5 must extend

**Research date:** 2026-10-20
**Valid until:** 2026-11-20 (stable repo-internal facts; revisit only if `run_sweep.py`/`run_sweep_shard.py` change before planning)
