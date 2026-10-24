# Phase 13: 动态调度核心 (Dynamic Dispatch Core) - Pattern Map

**Mapped:** 2026-10-20
**Files analyzed:** 4 (2 modified, 1 new-or-modified discretion, 1 optional config)
**Analogs found:** 4 / 4

All analog paths verified git-tracked (`git ls-files` non-empty). This phase is
almost pure orchestration over frozen seams — the analogs ARE the seams.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `pipeline/run_sweep_shard.py` (modify) | controller/CLI orchestrator | batch (work-queue) | itself: `main()` / `run_merge` / spawn loop | exact |
| `pipeline/dispatch_core.py` (new, discretion) | service (dispatch queue + ledger) | event-driven (claim/spawn/wait/record) | `pipeline/run_sweep_shard.py` launch path + `tui/services/sweep_launcher.py` O_EXCL tee | role-match |
| `tests/test_sweep_shard.py` (extend) and/or `tests/test_dispatch_core.py` (new) | test | request-response (fake-seam harness) | `tests/test_sweep_shard.py` fake-spawner idioms | exact |
| `Makefile` (only if `dispatch_core.py` created) | config | — | `PHASE12_MODULES` wildcard existence-guard idiom (Makefile:174) | exact |

**Note (research Pattern/recs):** primary recommendation is `run_dispatch()`
in-file inside `run_sweep_shard.py` (merge-mode precedent); extract to
`pipeline/dispatch_core.py` only on file-size ergonomics. `run_sweep.py` and
`run_finetune.py` are read-only import targets (frozen argv surfaces).

## Pattern Assignments

### `pipeline/run_sweep_shard.py` (orchestrator; add `--mode`, route `run_dispatch`, merge refusal)

**Analog:** itself — merge mode (`run_merge`, lines 756-898) is the precedent
for a second in-file mode routed from `main()`.

**Mode routing point** (lines 1067-1069 — `run_dispatch` slots in here):
```python
args, passthrough = parse_args()
if args.merge:
    return run_merge(args, passthrough)
```

**New-flag pattern** (copy the shape of `--dry-run`, lines 364-371; English
help, D-10; must not change the passthrough remainder for existing lines):
```python
parser.add_argument(
    "--mode",
    type=str,
    default="static",
    choices=["static", "dispatch"],
    help="...")
```
Parser is `parse_known_args` (line 396) — keep it; remainder discipline is
the D-07 contract.

**Merge-refusal insertion point** — `run_merge`'s collect-all `problems` list
(lines 766-787 precede it; the exit idiom):
```python
if problems:
    sys.exit(f"[Error] {'; '.join(problems)}")
```
Append the named "dispatch root {path} needs no merge" problem when the target
root carries dispatch evidence (`dispatch_state.json` / ledger), per MGPU-06.
`MERGE_ALLOWLIST` (lines ~498-504) stays untouched.

**Spawn discipline to copy verbatim (minus worker-root naming)** (lines
1201-1212):
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
Injectable seams at module top: `_DEFAULT_SPAWNER = subprocess.Popen`
(line 197), `main(spawner=None, clock=None)` (line 1042). Tee-lifetime note
(SIM115 rationale, lines 1193-1198): hold handles for the drain, close in
`finally` — per-cell children multiply this concern (research Pitfall 10).

**Frozen naming authority precedent** (lines 200-216):
```python
def worker_root(base_root, index):
    base = Path(base_root)
    return Path(f"{base}-mgpu-w{index}")
```
Define the ledger/claim/lock naming the same way — one function, test-pinned
in the pattern of `test_worker_root_and_log_naming_is_frozen`.

**Static-only validations to mode-gate OUT of dispatch** (lines 1120-1124
empty-shard, 1131-1151 frozen-root collision, 1164 LPT): route these inside
the static path only (research Pitfall 3).

**Everything the dispatcher consumes comes from `pipeline/run_sweep.py`
(imported, never re-implemented — D-07):**
- `enumerate_matrix` (line 533), `apply_priority_order` (line 957),
  `load_priority_tiers` (line 861)
- `build_argv` (line 1139) — note `--output_dir` receives the ROOT, not the
  cell dir
- `cell_dir_for` (line 1092-1102) — layout is `seed_{seed}` (underscore),
  `frac_{fraction}` nested under the seed dir:
  ```python
  cell = Path(output_root) / model / task / f"seed_{seed}"
  if fraction is not None:
      cell = cell / f"frac_{fraction}"
  ```
- Constants `PIPELINE_DIR`, `MANIFEST_NAME`, `FAILURES_NAME`, `RESUME_MARKER`,
  `METRICS_NAME` (lines 309-316)
- JSON writes: `_write_json` discipline `json.dump(..., indent=4,
  ensure_ascii=False, sort_keys=True)` (lines 1308-1311) — required for
  byte-identical dry-run goldens
- Remainder re-parse via `sys.argv` swap through `run_sweep.parse_args()`
  (which reads `sys.argv`, line 331) — Pattern 3 of the research

### `pipeline/dispatch_core.py` (new sibling, if extracted)

**Analog:** compose-as-sibling-module pattern (`flops_counter.py`,
`registry_loader.py` imported by `run_sweep_shard.py:182`) for structure; the
O_EXCL create precedent for the ledger/lock.

**O_EXCL precedent** (tui/services/sweep_launcher.py:763-798 — tee opens with
mode `"x"`, collision → suffix retry, SIM115 no-context-manager rationale):
```python
tee_handle = open(  # noqa: SIM115
    candidate, "x", encoding="utf-8")
...
except FileExistsError:
    continue
```
The claim ledger adapts this to the locked decision's `os.open` form:
```python
fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
```
`FileExistsError` = structurally refused (double-claim proof, SC3). Claim JSON:
cell key, lane flags, gpu, pid, run_id, timestamps; state transitions
`claimed → completed | failed`, single writer. Singleton dispatcher lock =
same mechanism per root; strict order lock → mode evidence → claim-before-spawn
(research Pitfall 8). Claim filenames must survive `+`/`__`/float fractions —
frozen encoding + collision test (research Pitfall 5).

Stdlib-headless contract: no torch/GPU import at module top; Google-style
docstrings with RST markup; `# ===== Configuration =====` discipline.

### `tests/test_sweep_shard.py` extension / `tests/test_dispatch_core.py`

**Analog:** `tests/test_sweep_shard.py` — reuse its helper block verbatim
(lines 125-222), all present in the same file:

```python
# lines 125-131 — REQUIRED in any new test module (machine-independence pin)
@pytest.fixture(autouse=True)
def _pin_custom_registry_overlay(tmp_path, monkeypatch):
    pinned = tmp_path / "no-custom-overlay"
    pinned.mkdir()
    monkeypatch.setenv("DNALLMMARK_CUSTOM_REGISTRY_DIR", str(pinned))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(pinned))

# lines 175-182 — CLI invocation through the injectable seams
def run_cli(monkeypatch, argv, spawner=None, clock=None):
    full_argv = ["run_sweep_shard.py", *argv]
    monkeypatch.setattr(sys, "argv", full_argv)
    run_sweep_shard.main(spawner=spawner, clock=clock)

# lines 199-222 — fake spawner harness
class FakeProc:
    def __init__(self, returncode=0):
        self.returncode = None
        self._scripted = returncode
        self.waited = False
    def wait(self, timeout=None):
        self.waited = True
        self.returncode = self._scripted
        return self._scripted

def make_fake_spawner(calls, returncodes=None):
    def spawn(argv, **kwargs):
        calls.append({"argv": list(argv), "kwargs": kwargs})
        index = len(calls) - 1
        code = returncodes[index] if returncodes is not None else 0
        return FakeProc(code)
    return spawn
```
For SC2 (kill test) use the PER-CELL scripted variant (research Pitfall 7):
parse `--target_model/--target_dataset/--seed` from argv inside the fake and
return `-9` only for the targeted cell. Fake children must derive the cell dir
exactly as the real child does (root + save-name model + task + `seed_{seed}`)
— the working idiom at tests/test_sweep_shard.py:1545-1566 (`fake_child`) —
because `--output_dir` carries the ROOT (research Pitfall 2). Fixture registry
shape: `make_registry` (lines 147-172), 3 models × 3 tasks. Existing suite
must pass unmodified (static byte-identity, including the
`not base.exists()` static pin at ~1656-1662).

### `Makefile` (only if `dispatch_core.py` is created)

**Analog:** `PHASE12_MODULES` idiom (Makefile:174) — foreach/wildcard so the
file joins lint only when present, leaving `.github/workflows/ci.yml`
byte-identical:
```make
PHASE12_MODULES := $(foreach s,pipeline/run_sweep_shard.py script/gen_progress.py,$(if $(wildcard $(s)),$(s)))
```
Add e.g. `PHASE13_MODULES := $(foreach s,pipeline/dispatch_core.py,$(if $(wildcard $(s)),$(s)))` and append to the `lint:` target's list (line 184).

## Shared Patterns

### Error handling / refusal format
**Source:** `pipeline/run_sweep_shard.py:1153-1154` (and `run_merge`)
**Apply to:** every dispatch-mode validation (lock held, mode+merge combo, malformed ledger)
```python
if problems:
    sys.exit(f"[Error] {'; '.join(problems)}")
```
Collect-all, named errors, nonzero exit. Never infer mode from directory
shape — read run-recorded evidence.

### Spawn kwargs (verbatim)
**Source:** `pipeline/run_sweep_shard.py:1201-1212` (excerpted above)
**Apply to:** every per-cell child spawn. argv is a LIST, never a shell string.

### Deterministic JSON serialization
**Source:** `pipeline/run_sweep.py:1308-1311` (`_write_json`: `indent=4,
ensure_ascii=False, sort_keys=True`)
**Apply to:** claim files, `dispatch_state.json`, dry-run plan artifact.
Atomic tmp+rename for the state file (single writer).

### Resume / completion truth (two-layer guard)
**Sources:** child marker — `pipeline/run_finetune.py:1315-1321`
(`trainer_state.json` skip, authoritative); resume-skip idiom —
`pipeline/run_sweep.py:1531-1534`; failure boundary — exit 0 WITHOUT
`final_metrics.json` = failed (CR-02), never complete.

### Testing seams
**Source:** `tests/test_sweep_shard.py` (`main(spawner=..., clock=...)`,
`FakeProc`/`make_fake_spawner`, autouse overlay pin, dry-run disjointness
comparison idiom at 740-786 for SC1's static-union equality)
**Apply to:** all SC1-SC5 tests. CPU-only; no GPU, no dnallm, no N>1 devices.

## No Analog Found

None — every file has a strong in-repo analog. The only genuinely novel logic
(exactly-once ledger state machine) is grounded in the sweep_launcher O_EXCL
precedent plus research Patterns 2-4; the planner should carry the research's
pitfall list (seed_ naming, --output_dir ROOT semantics, per-cell fakes,
claim-filename aliasing) into the plan's verification steps.

## Metadata

**Analog search scope:** pipeline/, tests/, tui/services/, Makefile
**Files scanned:** run_sweep_shard.py (full structure), run_sweep.py (named
seams), test_sweep_shard.py (helper block), sweep_launcher.py (O_EXCL),
Makefile (lint list) — all git-tracked
**Pattern extraction date:** 2026-10-20
