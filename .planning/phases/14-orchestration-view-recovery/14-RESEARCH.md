# Phase 14: 编排运行视图与失败恢复 (Orchestration View & Failure Recovery) - Research

**Researched:** 2026-10-20
**Domain:** Multi-GPU dispatch observability + failure recovery (stdlib Python pipeline tooling, CPU-testable)
**Confidence:** HIGH (every seam read directly in the live tree with line citations; milestone design research at `.planning/research/ARCHITECTURE.md` §A/§B is the ratified backbone and was NOT re-derived)

## Summary

Phase 14 is a pure consumer/extension pass over the Phase 13 dispatch engine (`pipeline/dispatch_core.py`, landed 2026-10-20, 53+ tests) plus one new sibling mode on `pipeline/run_sweep_shard.py`. Three deliverables: (1) freeze and extend `dispatch_state.json` with the MGPU-03 consumer fields (queue depth, per-worker in-flight cell, failures, timestamps) and render a plain-line terminal table on every state write; (2) a ledger-driven failure re-run surface that replays lane flags recorded at claim time (the 12-04 lane-blindness fix); (3) a `--cleanup` sibling mode that verifies a merged static root (export dry-run + manifest-count equality) before offering confirm-gated worker-root removal.

The engine is in excellent shape for this: `_write_state` (dispatch_core.py:634-641) is a single choke point invoked at every state transition under `state_lock`; the claim payload already records lane flags at claim time (`_claim_payload`, dispatch_core.py:402-435) with the docstring explicitly naming Phase 14 MGPU-04 as the consumer; `run_sweep_shard.main()` (run_sweep_shard.py:1161-1184) already routes sibling modes with lazy `dispatch_core` import; and `run_merge`'s lane-equality refusal (run_sweep_shard.py:944-964) is the verbatim refusal-shape precedent for D14-08/D14-11.

Three load-bearing gaps discovered by reading the code (all must become plan tasks):

1. **The claim `lane` dict lacks `cache_dir`** — the live dict is exactly `{"peft", "config_variant", "subset_file", "effective_batch_size", "num_train_epochs"}` (dispatch_core.py:1237-1243), but D14-06 locks cache_dir into the replayed lane. The lane dict must be extended (and stale pre-Phase-14 claims tolerated on replay).
2. **Claim filenames are keyed by cell identity only** (`claim_filename`, dispatch_core.py:242-270), so D14-07's "FRESH O_EXCL claims … old claims are never mutated" collides structurally with the one-file-per-cell naming: a fresh O_EXCL create on a re-run cell EEXISTs against the original failed claim. The plan must pick an audit-trail-preserving scheme (retire-rename, archive-copy + atomic replace, or generation-suffixed names) — see Open Questions Q1.
3. **`script/export_runs.py` has NO dry-run mode today** (grep verified: zero "dry" hits) — the D14-10 verification seam must be ADDED (a `--dry-run` flag or equivalent), and because export_runs imports `numpy`/`yaml`/`scipy` at module top (export_runs.py:117-119), the stdlib-headless orchestrator can only reach it through a **subprocess seam with injection** (never a direct import).

**Primary recommendation:** Extend `dispatch_state.json` in place with a `schema_version` bump to 2 + a committed `schemas/dispatch_state.json` consumer contract; hook the renderer inside the `_write_state` choke point (render under `state_lock`, `print(..., flush=True)`); implement the re-run as a new orchestrator-owned flag branching in `run_dispatch` BEFORE the `--models`/`--seeds` requirement refusals; implement `--cleanup` as a fourth sibling mode in `main()` reusing `_root_has_dispatch_evidence` for the dispatch-root refusal and a subprocess-injectable export dry-run for verification.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Live Run View (MGPU-03)**
- **D14-01:** The state file is Phase 13's `{root}/dispatch_state.json` EXTENDED (single-writer, atomic) — no second file; Phase 14 freezes the consumer schema (queue depth, per-worker in-flight cell, failures, timestamps)
- **D14-02:** Terminal table = plain-line renderer (stdlib prints) inside dispatch_core.py or a thin sibling, rendering per-worker rows on every state write — no timer loop, no TUI library
- **D14-03:** Render cadence = on each state write (claim/finalize/event); pty/capsys tests assert row content after scripted events
- **D14-04:** Schema frozen and parseable by a consumer test BEFORE Phase 16 (TUI) touches it; `script/gen_progress.py` mirror updated in the same commit as any schema change

**Failure Re-Run (MGPU-04)**
- **D14-05:** Re-run surface = `--from-failures`-style flag on dispatch mode itself (one command re-runs the union of failed cells), reusing the CR-01 filter machinery landed in Phase 13
- **D14-06:** Lane flags (peft/config_variant/num_train_epochs/subset_file/effective_batch_size/cache_dir) recorded at claim time are replayed verbatim on re-run — the 12-04 lane-blindness fix, fixture-proven
- **D14-07:** Failure-union semantics: ledger `state: failed` cells across ALL prior runs on the root form the re-run set; re-runs create FRESH O_EXCL claims carrying a `rerun_of` link to the original — old claims are never mutated (audit trail preserved)
- **D14-08:** Heterogeneous lane signatures among failed cells refuse loudly, naming the differing flag per cell (mirrors the merge lane-equality refusal discipline)

**Post-Merge Verify + Cleanup (MGPU-05)**
- **D14-09:** Helper shape = `run_sweep_shard.py --cleanup --workers N --output-root R` sibling mode: verify THEN offer removal behind an explicit confirmation gate
- **D14-10:** Verification = `script/export_runs.py` dry-run over the merged root + manifest cell-count equality vs the union of worker manifests — both green before removal is offered
- **D14-11:** Removal gate = explicit typed confirmation (interactive `--yes` typed phrase or non-interactive refusal); refusal paths tested; static-merge roots only — dispatch roots get a named "needs no cleanup" error (one root by construction)
- **D14-12:** Scope: static-mode worker roots only

**Testing & CI Shape**
- **D14-13:** Table assertions via capsys/pty lane over scripted fake-child event sequences (worker/cell/state strings per step); no full-screen golden snapshots
- **D14-14:** State-schema consumer test parses dispatch_state.json against a frozen schema definition committed with any field change
- **D14-15:** Re-run fixture = two-worker fake run with injected failures on BOTH workers → one re-run → exactly the failed cells re-claimed with original lane flags, healthy cells untouched
- **D14-16:** Full CPU lanes stay green (pytest/ruff/ty + node); static mode byte-identical; zero CI changes; stdlib-headless held; fake children + injected seams only

### Claude's Discretion
- Exact table column set/format (worker id, cell key, state, elapsed) provided the frozen-schema and capsys assertions cover it
- Whether the renderer lives in dispatch_core.py or a thin sibling module (follow Phase 13's compose-as-sibling ergonomics)
- The `rerun_of` link's exact JSON shape inside the claim payload

### Deferred Ideas (OUT OF SCOPE)
- TUI slot-5 consumption + G GPU-lanes display → Phase 16 (TUI-03/TUI-01)
- Real-GPU exercise of the view/re-run on 2×5090 → Phase 15 (VAL-03 small real sweep uses this machinery end-to-end)
- `gen_progress.py` web-mirror enhancements beyond keeping it parsing → follow Web phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MGPU-03 | Live orchestrator run view — a terminal progress table AND a single-writer atomic `dispatch_state.json` (queue depth, per-worker in-flight cell, failures, timestamps) consumable by the TUI and `gen_progress.py` | Current state shape + all 7 `_write_state` call sites mapped (Current-Seam Inventory S1); renderer choke point identified; schema-freeze mechanics (schemas/ dir + jsonschema in dev group) verified |
| MGPU-04 | Cross-worker failure re-run — one command re-runs the union of failed cells across workers with full lane context (peft/variant/epochs) recorded at claim time, fixing the v1.2 lane-blindness limitation | Claim-lane seam mapped incl. the cache_dir gap; CR-01 filter machinery located (dispatch_core.py:1061-1085); claim-filename collision knot documented with options; relaunch_decision interplay documented |
| MGPU-05 | Post-merge verify + cleanup helper — verifies the merged root (export dry-run + manifest count check), then removes worker roots behind an explicit confirmation gate (replaces the manual `rm -rf` recipe) | `main()` mode-routing block + A6 combo-refusal precedent located; `_root_has_dispatch_evidence` reusable for the dispatch-root refusal; export_runs dry-run gap + subprocess-seam requirement documented; merge-test fixtures reusable for cleanup tests |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Tech stack frozen:** vanilla ES-module JS (no build step) and Python — public release must not change the architecture (this phase is Python-only)
- **CI feasibility:** GitHub Actions must not require GPU or the external `dnallm` package — test scope limited to stdlib/numpy/pandas scripts and static checks (D14-16 restates: zero CI changes)
- **Fix discipline:** Surgical fixes only; no opportunistic refactors that widen review surface
- **Reproducibility:** Fixes may change aggregated numbers only through documented before/after comparison (this phase touches NO aggregation — leaderboard numbers move only through zero-drift-proven additive changes per the phase's binding constraints)
- **Python conventions (pipeline/):** Google-style docstrings with RST double-backtick markup; `# ===== Configuration =====` block at top of `main()`; stdlib-headless (no torch/dnallm at module top)
- **GSD workflow enforcement:** work enters through GSD commands (this research is part of `/gsd-plan-phase`); no direct repo edits outside a GSD workflow
- **Memory rules (user):** all data/models/caches under `/root/autodl-tmp` (2.1T data disk), never `/` or `/root`; commits are plain messages with no Co-Authored-By/attribution trailers; push as part of the flow

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| dispatch_state.json authoring (single-writer, atomic) | Dispatcher process (dispatch_core worker threads under `state_lock`) | — | Single-writer discipline is the Phase 13 contract (P10); exactly one dispatcher per root via the singleton lock |
| Terminal live table rendering | Dispatcher process (pipeline-side plain prints) | — | D14-02 locks this pipeline-side; the TUI (Phase 16) only READS the state file, never renders the sweep itself ("TUI orchestrates never computes") |
| Frozen consumer schema definition | `schemas/dispatch_state.json` (repo artifact) | Consumer tests (pytest + jsonschema) | The schemas/ dir is the established home for frozen JSON contracts (14 existing schemas) |
| Failure re-run decision + lane replay | Dispatcher (`run_dispatch` re-run branch) | Ledger claim files (source of truth for failed cells + lanes) | The ledger is the designed MGPU-04 feed (claim docstring says so verbatim) |
| Merged-root verification (export dry-run) | `script/export_runs.py` (subprocess, numpy/scipy lane) | `--cleanup` mode (stdlib orchestrator, injectable subprocess seam) | export_runs imports numpy/yaml/scipy at module top → the stdlib-headless orchestrator must not import it in-process |
| Worker-root removal | `--cleanup` mode (run_sweep_shard.py) | Operator (typed confirmation gate) | Destructive action behind an explicit gate; static-mode roots only |
| gen_progress.py compatibility | Offline generator (unchanged behavior) | Consumer test in the schema-change commit | gen_progress reads the tui scanner, NOT dispatch_state (verified: zero dispatch references in `tui/services/sweep_monitor.py`) — the D14-04 obligation is keep-it-parsing |

## Current-Seam Inventory (verified in the live tree)

> This is the phase's implementation map. Every citation was opened with Read this session; verbatim quotes accompany load-bearing values.

### S1. The state file (MGPU-03 extension target)

Current minimal payload, written at `run_dispatch` (dispatch_core.py:1184-1192) — verbatim:

```python
    state = {
        "schema_version": DISPATCH_STATE_SCHEMA_VERSION,
        "mode": "dispatch",
        "run_id": run_id,
        "status": "running",
        "started_at": started_at,
        "updated_at": started_at,
        "counts": dict(counts),
    }
```

with `DISPATCH_STATE_SCHEMA_VERSION = 1` (dispatch_core.py:123) and `counts = {"total": len(cells), "completed": 0, "failed": 0, "skipped": 0}` (dispatch_core.py:1178-1183). Status vocabulary observed in code: `"running"` (initial), `"done"` (dispatch_core.py:1250, 1332), `"incomplete"` (dispatch_core.py:1314) `[VERIFIED: pipeline/dispatch_core.py:1184-1192,123,1178-1183,1250,1314,1332]`.

`_write_state` is the single write choke point (dispatch_core.py:634-641): `_atomic_write_json(state_path, state)` — tmp file + `os.replace` (`_atomic_write_json`, dispatch_core.py:370-385, `_dump_json_handle` discipline `indent=4, ensure_ascii=False, sort_keys=True`). Call sites (all seven): mode-evidence-before-any-claim (:1193), post-skip-filter (:1208), per-cell finalize under `state_lock` (:781), containment-path failure (:830), nothing-to-do (:1252), incomplete accounting (:1316), done (:1334) `[VERIFIED: pipeline/dispatch_core.py:634-641,370-385 + call sites]`.

**What is MISSING vs MGPU-03** (all must be added): per-worker in-flight cell, queue depth, a failures view, per-worker counters in state (they exist only in `worker_stats`, dispatch_core.py:1213-1215: `{i: {"cells": 0, "completed": 0, "failed": 0}}`), and any state write at claim time (today the first per-cell write happens at finalize — D14-03 wants a render on claim too).

**Lock structure:** `context["queue_lock"]` guards pending pops (dispatch_core.py:670-673); `context["state_lock"]` guards count updates + state writes (:771-781). Queue depth capture at write time must decide how to snapshot `len(context["pending"])` across the two locks (CPython `len()` on a list is atomic; a depth counter maintained inside the same critical sections is the consistent-snapshot alternative).

### S2. The claim ledger (MGPU-04 feed)

- Ledger dir: `LEDGER_DIR_NAME = "dispatch_ledger"` under the root; lock `DISPATCHER_LOCK_NAME = "dispatcher.lock"` inside it (dispatch_core.py:106-114) `[VERIFIED: pipeline/dispatch_core.py:106-114]`
- State vocabulary: `CLAIM_STATE_CLAIMED = "claimed"`, `CLAIM_STATE_COMPLETED = "completed"`, `CLAIM_STATE_FAILED = "failed"` (dispatch_core.py:118-120) `[VERIFIED: pipeline/dispatch_core.py:118-120]`
- Claim payload keys (`_claim_payload`, dispatch_core.py:421-434): `cell` (via `_cell_key` → `{"model", "task", "seed", "fraction"}`), `state`, `lane`, `gpu`, `dispatcher_pid`, `child_pid`, `run_id`, `claimed_at`, `finished_at`, `exit_code`, `error` `[VERIFIED: pipeline/dispatch_core.py:421-434]`
- **Lane flags at claim time** — the live lane dict (dispatch_core.py:1237-1243) verbatim:

```python
        "lane": {
            "peft": sweep_args.peft,
            "config_variant": config_variant,
            "subset_file": subset_file_abs,
            "effective_batch_size": sweep_args.effective_batch_size,
            "num_train_epochs": sweep_args.num_train_epochs,
        },
```

  with the per-cell fraction merged in `_claim_payload` (dispatch_core.py:424-425: `"lane": {**lane, "train_fraction": (cell[3] if len(cell) > 3 else None)}`). **GAP: `cache_dir` is NOT recorded** (D14-06 locks it into the replay set); `model_root`/`dataset_root`/`log_dir` are also absent (in `context` at :1233-1236 but not in `lane`) `[VERIFIED: pipeline/dispatch_core.py:1237-1243,402-435]`
- Claim naming (`claim_filename`, dispatch_core.py:264-270): percent-encoded `model`/`task`/`seed{n}`[/`frac{f}`] joined `--`, then `-` + `sha256(canonical tuple JSON)[:12]` + `.json` — **keyed by cell identity only**; one file per cell `[VERIFIED: pipeline/dispatch_core.py:242-270]`
- Claim mechanics: `claim_cell` O_EXCL create-or-refuse (:288-314, EEXIST → None → SC3 skip), `overwrite_claim` atomic replace of a stale claim (:346-367), `finalize_claim` rewrite with terminal state (:388-399), tolerant `read_claim` (missing → None; unusable → `{}`) (:317-343) `[VERIFIED: pipeline/dispatch_core.py:288-399]`
- **Relaunch interplay (critical):** `relaunch_decision` (dispatch_core.py:592-626) returns requeue for a present `failed` claim — a PLAIN relaunch of the same root today already re-runs failed cells via `overwrite_claim` (the old claim is REPLACED, losing the audit trail). The MGPU-04 re-run must be distinct: ledger-driven cell set, lane replay from claims, and audit-trail preservation (D14-07) `[VERIFIED: pipeline/dispatch_core.py:592-626,685-691]`

### S3. The CR-01 `--from-failures` machinery (the reuse target of D14-05)

In `run_dispatch` (dispatch_core.py:1061-1085): if `sweep_args.from_failures` is set → `run_sweep.load_failure_pairs(path, registry_dir)` → filter `cells` to those whose `(run_sweep.base_model_name(cell[0], peft, config_variant), cell[1])` is in the pairs set. Source is a **sweep_failures.json manifest FILE**; the re-run **fans out over all requested seeds** of each failed (model, task) pair. `load_failure_pairs` (run_sweep.py:1001-1089) validates entries against the registry collect-all (unknown model/task, no-train tasks, structure) and returns `set[tuple[str, str]]` `[VERIFIED: pipeline/dispatch_core.py:1061-1085; pipeline/run_sweep.py:1001-1089]`.

D14-07's ledger-driven semantics differ on three axes: source = ledger claims (not a manifest file), granularity = exact `(model, task, seed[, fraction])` cells (not pair × seed fan-out), lane = replayed from claims (not from the new command line). The "machinery reuse" is the discipline (collect-all validation, registry join, zero-cell refusal, alias handling via `base_model_name`, run_sweep.py:1105-1136), not the literal manifest reader.

### S4. run_sweep frozen contract surface (import, never re-implement — D-07)

- `build_argv(model, task, seed, output_root, peft="none", train_fraction=None, subset_file=None, effective_batch_size=None, num_train_epochs=None, cache_dir=None, config_variant="none", model_root=None, dataset_root=None, log_dir=None)` (run_sweep.py:1139-1143) — the lane keys map 1:1 onto these kwargs; `--output_dir` receives the ROOT (the child derives the cell dir) `[VERIFIED: pipeline/run_sweep.py:1139-1255]`
- `cell_dir_for(output_root, model, task, seed, fraction=None)` → `{root}/{model}/{task}/seed_{seed}/[frac_{f}/]` (run_sweep.py:1092-1102) `[VERIFIED: pipeline/run_sweep.py:1092-1102]`
- Constants (run_sweep.py:309-316): `MANIFEST_NAME = "sweep_manifest.json"`, `FAILURES_NAME = "sweep_failures.json"`, `RESUME_MARKER = "trainer_state.json"`, `METRICS_NAME = "final_metrics.json"` `[VERIFIED: pipeline/run_sweep.py:309-316]`
- `--seeds` is REQUIRED in run_sweep's parser — a dispatch launch without it dies at the remainder re-parse with argparse usage exit code 2 (dispatch_core.py:905-921, pinned by `test_dispatch_missing_seeds_exits_argparse_code_2`); `--models` is dispatch-mode-required with a named refusal (dispatch_core.py:888-896). **A ledger-driven re-run that needs neither flag must branch BEFORE these requirements** `[VERIFIED: pipeline/dispatch_core.py:888-921; tests/test_dispatch_core.py:1060]`

### S5. run_sweep_shard mode routing + refusals (MGPU-05 insertion point + D14-08/D14-11 precedent)

`main()` routing (run_sweep_shard.py:1161-1184): A6 combo refusal (`--mode dispatch` + `--merge`, :1166-1173) → `run_merge(args, passthrough)` → lazy-import `dispatch_core.run_dispatch` → static launch path. The A6 block is the verbatim precedent for `--cleanup` combination refusals `[VERIFIED: pipeline/run_sweep_shard.py:1161-1184]`.

Lane-equality refusal (run_merge, run_sweep_shard.py:944-964): `_lane_signature` collects per-flag value sets over every non-identity cell key; a differing flag produces a collect-all diagnostic listing the value per root per flag. `_canonical_lane_value` (:649-670) canonicalizes sets deterministically. This is the D14-08 refusal discipline (adapted to name the differing flag **per cell**) `[VERIFIED: pipeline/run_sweep_shard.py:618-670,944-964]`.

Dispatch-evidence detection (`_root_has_dispatch_evidence`, run_sweep_shard.py:728-775): reads ONLY the three run-recorded markers — `dispatch_state.json` at the root, the `dispatch_ledger` dir, or a `sweep_manifest.json` whose cells carry `orchestrator_mode: "dispatch"` — never directory shape. `_dispatch_merge_refusal` (:778-785) builds the named refusal. **Reuse directly for D14-11's "dispatch roots get a named 'needs no cleanup' error"** `[VERIFIED: pipeline/run_sweep_shard.py:728-785]`.

Frozen worker-root naming (`worker_root`, run_sweep_shard.py:200-216): `{base}-mgpu-w{index}` — the cleanup removal target. The manual recipe this helper replaces lives at `docs/multi-gpu.md:157-160` and `:242-245` (`rm -rf pipeline/finetuned-mgpu-w{0,1}` + `rm -f ...-*.log` — note it also deletes per-launch LOGS; whether `--cleanup` also removes logs is a scope decision, see Q5) `[VERIFIED: pipeline/run_sweep_shard.py:200-216; docs/multi-gpu.md:157-160,242-245]`.

Collect-all exit idiom (every mode): `if problems: sys.exit(f"[Error] {'; '.join(problems)}")` (run_sweep_shard.py:991-992, 1268-1269) `[VERIFIED: pipeline/run_sweep_shard.py:991-992]`.

### S6. export_runs.py (D14-10 verification target)

- **No dry-run exists** (grep for "dry" over the file: zero hits). The CLI (`main`, export_runs.py:898-957) always writes task/model/stats outputs `[VERIFIED: script/export_runs.py grep + main read]`
- The walk is `load_run_records(root)` (export_runs.py:498-551): walks `{root}/{model}/{task}/seed_{n}/run_record.json`, returns `{model: {task: {seed: record}}}`, raises `FileNotFoundError` for a missing root, aborts loudly on malformed records, tolerantly adopts `seed_result.json` `[VERIFIED: script/export_runs.py:498-551]`
- Module-top imports: `numpy` (line 117), `yaml` (118), `scipy.stats` (119) — the module is NOT stdlib-headless and must NOT be imported by `run_sweep_shard.py`/`dispatch_core.py`; reach it via `sys.executable` subprocess with an injectable runner seam `[VERIFIED: script/export_runs.py:117-119]`
- `export_runs_tree` (export_runs.py:745-895) both walks AND writes — a dry-run needs either a `--dry-run` flag short-circuiting before writes (walk + count + print) or a pure-count helper factored next to `load_run_records`. Surgical preference: a `--dry-run` flag on `main()` that performs the walk + counts and writes nothing `[VERIFIED: script/export_runs.py:745-957]`
- Test lane: `tests/test_export_runs.py` exists; `tests/conftest.py` puts `script/` on sys.path (conftest.py:42); `make test` runs `uv run --group dev --group tui pytest` + node — the default `data` group (numpy/scipy) rides along, so in-process TEST imports of export_runs are fine; only the PRODUCTION orchestrator must use the subprocess seam `[VERIFIED: Makefile:101-103; tests/conftest.py:42; pyproject.toml default-groups note]`

### S7. gen_progress.py (D14-04 keep-parsing obligation)

gen_progress serializes the tui scanner (`tui/services/sweep_monitor`) verbatim (gen_progress.py:92, :221-235); it has NO dispatch_state.json reader, and neither does `sweep_monitor.py` (grep verified: zero hits in both). The scanner classifies a root via manifest/churn rules — a real dispatch root (no manifest) is already handled by the manifest-less path (12-02 ruling: `total:null` → Unknown). Phase 14's same-commit obligation is therefore minimal: a test that gen_progress still parses/parses-over a dispatch fixture root after the schema change; anything more is deferred to the Web phase per CONTEXT `<deferred>` `[VERIFIED: script/gen_progress.py:92,221-235; tui/services/sweep_monitor.py grep]`.

### S8. The test harness (what Phase 14 extends)

`tests/test_dispatch_core.py` (2233 lines) + `tests/test_sweep_shard.py` (1662 lines), both with the autouse machine-independence pin (`DNALLMMARK_CUSTOM_REGISTRY_DIR` + `XDG_CONFIG_HOME` → empty tmp dir, test_dispatch_core.py:110-116):

- `run_cli(monkeypatch, argv, spawner=None, clock=None)` — drives `run_sweep_shard.main` with patched `sys.argv` and the injectable seams (test_dispatch_core.py:159-165)
- `FakeProc` (scripted returncode + pid 4242, :183-196), `make_fake_spawner(calls, returncodes)` (:198-207)
- `make_child_spawner(calls, exit_for=None)` (:210-256) — the **per-cell scripted child**: derives the cell dir exactly as the real child does (root + save-name + task + `seed_{n}` [+ `frac_{f}`]), writes `final_metrics.json` + `trainer_state.json` for exit-0 cells, and `exit_for` maps `(save, task, seed) → returncode` — this IS the D14-15 fixture primitive (targeted failures on both workers) `[VERIFIED: tests/test_dispatch_core.py:210-256]`
- `spawn_identities(calls)` (:259-266), `_write_hand_claim` (:1397-1406), `_write_marker` (:1408-1417) — hand-materialized ledger/resume fixtures
- Spy-child idiom (mid-wait claim reads, :352-400); ENOSPC-style injection via monkeypatched `_write_state`/`finalize_claim` wrappers (`_flaky_finalize` :1840, `_worker_state_writes_always_fail` :1857)
- Merge fixtures in test_sweep_shard.py, directly reusable for cleanup tests: `write_manifest` (:853), `make_manifest_cell` (:869), `make_lane_pair` (:884), `_write_cell_artifacts` (:1018), `make_worker_pair` (:1051), `run_merge_cli` (:1129), `_snapshot_tree`/`_worker_allowlisted_files` (:1111-1127) `[VERIFIED: tests/test_sweep_shard.py structure scan]`
- pty lane precedent: `tests/tui/test_pty_driver.py` (pure pexpect, permanent real-terminal regression lane); pexpect 4.9.0 is in the dev group (runtime-verified) `[VERIFIED: tests/tui/test_pty_driver.py; uv run --group dev python -c import pexpect → 4.9.0]`
- Static byte-identity tripwire: `test_static_mode_explicit_pins_argv_roots_and_logs` (test_dispatch_core.py:2139) + the 49-test shard suite; `test_mode_static_explicit_matches_default` (:1257) `[VERIFIED: tests/test_dispatch_core.py:1257,2139]`

### S9. Lint/type gates

`make lint` covers `pipeline/dispatch_core.py` via `PHASE13_MODULES` wildcard existence-guard (Makefile:181,191) and `script/export_runs.py` explicitly (Makefile:191). **If the renderer stays inside dispatch_core.py, zero Makefile change; a NEW pipeline sibling needs a `PHASE14_MODULES` guard in the same idiom** (13-PATTERNS.md documents the recipe; ci.yml stays byte-identical) `[VERIFIED: Makefile:174,181,191]`.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib (`json`, `os`, `subprocess`, `threading`, `hashlib`, `pathlib`, `urllib.parse`) | 3.13+ (repo pin) | The entire phase — state writes, renderer, ledger, cleanup | D14-16 locks stdlib-headless; Phase 13 engine is already pure stdlib |
| pytest | 9.1.1 (dev group, runtime-verified) | Test harness extension | The established tier-1 lane (`make test`) |
| pexpect | 4.9.0 (dev group, runtime-verified) | pty lane for live-render assertion (D14-13) | Precedent: tests/tui/test_pty_driver.py; already in dev group since 261017-eea |
| jsonschema | >=4.26.0 (dev group, pyproject.toml:31) | Frozen-schema consumer test (D14-14) | Same library the Phase 8/9 schema tests use; in-repo precedent |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| numpy / scipy / yaml | (data group, via uv.lock) | Only inside export_runs.py's dry run — reached via SUBPROCESS from the orchestrator, imported in-process only by tests | The `--dry-run` verification subprocess |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Plain-line renderer (D14-02) | Rich/curses/textual table | REJECTED by D14-02 (no TUI library) and the binding constraint that the terminal view is pipeline-side plain output; Phase 16 owns TUI consumption |
| Direct import of export_runs in the cleanup mode | — | Not an alternative: stdlib-headless forbids it (numpy/scipy/yaml at module top). Subprocess seam with injection is the only compliant shape |
| A second state file for the view | — | REJECTED by D14-01 (extend dispatch_state.json, no second file) |

**Installation:** none — no new packages. `uv sync` unchanged; `uv.lock` untouched; CI byte-identical (D14-16).

**Version verification:** runtime-verified this session: Python 3.14.6 (system), uv 0.13.0, pexpect 4.9.0 (`uv run --group dev`), pytest 9.1.1, node v26.4.0. The repo data-chain pin is Python 3.13 via `.python-version` (CLAUDE.md); the project venv resolves under uv.

## Package Legitimacy Audit

No external packages are installed or recommended by this phase (stdlib-only + already-locked dev-group tools). **Audit: N/A — no new registry packages.**

## Architecture Patterns

### System Architecture Diagram

```
                        ┌──────────────────────────────────────────────────────────┐
                        │  run_sweep_shard.py main()  (mode routing, :1161-1184)   │
                        └──────┬───────────────┬──────────────┬────────────────────┘
                               │               │              │
              --mode dispatch  │      --merge  │     --cleanup │  (NEW sibling mode)
                               ▼               ▼              ▼
                 ┌──────────────────┐  ┌───────────────┐  ┌──────────────────────────┐
                 │ dispatch_core    │  │ run_merge     │  │ run_cleanup (NEW)        │
                 │ run_dispatch     │  │ (frozen)      │  │ 1. refuse dispatch roots │
                 │ ┌──────────────┐ │  └───────────────┘  │    (_root_has_dispatch_  │
                 │ │ ENUMERATE    │ │                     │     evidence)            │
                 │ │ (or RE-RUN   │ │                     │ 2. verify merged root:   │
                 │ │  scan: NEW)  │ │                     │    a. export_runs.py     │
                 │ ├──────────────┤ │                     │       --dry-run          │
                 │ │ LOCK (O_EXCL)│ │                     │       [SUBPROCESS seam]  │
                 │ ├──────────────┤ │                     │    b. manifest cell-count│
                 │ │ STATE write  │ │                     │       == union of worker │
                 │ │  + RENDER ◀──┼─┼── every _write_state│       manifests          │
                 │ │ (NEW: frozen │ │                     │ 3. typed confirmation    │
                 │ │  schema v2)  │ │                     │    (non-interactive =    │
                 │ ├──────────────┤ │                     │    refusal)              │
                 │ │ worker loops │ │                     │ 4. rm worker roots       │
                 │ │ claim→spawn→ │ │                     │    {root}-mgpu-w{i}      │
                 │ │ wait→finalize│ │                     └──────────────────────────┘
                 │ └──────┬───────┘ │
                 └────────┼─────────┘
                          ▼
        {root}/dispatch_state.json  (frozen consumer schema, single writer)
          consumed by: terminal renderer (this phase)
                       TUI slot 5 (Phase 16) · gen_progress mirror (keep-parsing)
        {root}/dispatch_ledger/*.json  (claims w/ lane flags + rerun_of)
          consumed by: failure re-run (this phase, MGPU-04)
```

The primary use case traces: a failed two-worker dispatch run → operator issues ONE re-run command → the ledger's `state: failed` claims across all prior runs form the exact cell set → lane flags replay verbatim from each claim's `lane` dict → fresh claims with `rerun_of` links → children spawn → the terminal table renders claim/finalize events live → final state carries the frozen v2 schema.

### Recommended Project Structure (touch list)

```
pipeline/dispatch_core.py        # MODIFY: state extension + renderer hook + re-run branch + lane(cache_dir) + rerun_of
pipeline/run_sweep_shard.py      # MODIFY: --cleanup flag + mode routing + combo refusals (+ re-run flag routing if orchestrator-owned)
script/export_runs.py            # MODIFY: --dry-run (walk + count, write nothing)
schemas/dispatch_state.json      # NEW: frozen consumer schema (D14-14)
tests/test_dispatch_core.py      # EXTEND: schema consumer test, renderer capsys/pty, re-run fixtures (D14-15)
tests/test_sweep_shard.py        # EXTEND: --cleanup verify/refusal/confirm-gate tests (reuse merge fixtures)
tests/test_export_runs.py        # EXTEND: --dry-run unit tests (if the dry run lands as CLI behavior)
Makefile                         # ONLY if a new pipeline sibling module: PHASE14_MODULES guard
```

### Pattern 1: Renderer at the `_write_state` choke point (D14-02/D14-03)
**What:** one render call inside (or immediately after) every `_write_state`, executed under `state_lock` so renders never interleave; plain prints with explicit flush.
**When to use:** every state transition — mode evidence, skip filter, claim (NEW write site), finalize, containment, terminal statuses.
**Design sketch (over the verified seam, not landed code):**

```python
# Source: design sketch over [VERIFIED: pipeline/dispatch_core.py:634-641]
def _write_state(state_path, state, render=None):
    _atomic_write_json(state_path, state)
    if render is not None:
        render(state)  # plain prints, flush=True; called under state_lock
```

The render input must be the FROZEN state payload itself (queue depth, workers[], counts, failures, timestamps) — the same bytes the TUI will read — never a richer side-channel, or the consumer schema and the rendered view drift.

### Pattern 2: Frozen schema as a repo artifact + jsonschema consumer test (D14-04/D14-14)
**What:** commit `schemas/dispatch_state.json` describing the v2 shape; a consumer test loads real `dispatch_state.json` files produced by the fake-children fixtures and validates them with `jsonschema` (dev group).
**When to use:** any field change to the state file — the schema and the `DISPATCH_STATE_SCHEMA_VERSION` bump ride the same commit as the writer change, and the gen_progress keep-parsing test rides with it (D14-04).

### Pattern 3: Ledger-driven re-run branch BEFORE the flag requirements (D14-05/07)
**What:** the re-run flag branches in `run_dispatch` ahead of the `--models` requirement refusal (dispatch_core.py:888-896) and ahead of the remainder re-parse's argparse-code-2 `--seeds` requirement — the failed-claim set defines models AND seeds; collect-all validation still joins every claim cell against the registry (unknown names refuse loudly, the `load_failure_pairs` discipline).
**When to use:** the one-command re-run. Heterogeneous lanes among the failed claims refuse per D14-08 with a per-cell, per-flag diagnostic in the `_lane_signature`/`run_merge` refusal shape.

### Pattern 4: `--cleanup` as the fourth sibling mode (D14-09..12)
**What:** route in `main()` after the A6-style combination refusals (`--cleanup` × `--merge`, `--cleanup` × `--mode dispatch`, stray passthrough, `--models`); verify; gate; remove.
**When to use:** post-merge only, static roots only. Reuse `_root_has_dispatch_evidence` for the named "needs no cleanup" refusal on dispatch roots (base root AND any worker root in the set — defense-in-depth, the run_merge precedent checks both, run_sweep_shard.py:879-884).

### Anti-Patterns to Avoid
- **Rendering from a side-channel state:** the table must render the frozen state payload; a renderer reading `context` internals directly makes the schema freeze untestable and lets view and file drift.
- **Timer-loop rendering / TUI libraries:** D14-02 forbids; render cadence is state writes only.
- **Importing export_runs (or numpy) into pipeline/:** breaks stdlib-headless and the CI lane contract; the only compliant production path is a subprocess seam.
- **Mutating/overwriting the original failed claim on re-run without preserving it:** violates D14-07's audit-trail intent; the existing `overwrite_claim` requeue path is for plain relaunch, not the re-run.
- **Infering mode/cleanup-safety from directory shape:** evidence-based only (`_root_has_dispatch_evidence` reads run-recorded markers, never shape).
- **Silent zero-cell fallbacks:** every filtered-to-empty outcome gets an explicit named verdict (zero-enumeration refusal at dispatch_core.py:1086-1096; clean-manifest message at :1072-1079; drained-root verdict at :1246-1259 — pick the matching precedent deliberately).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Atomic single-writer JSON writes | New write helpers | `_atomic_write_json` (dispatch_core.py:370-385) | Already the P10 discipline; tested tmp+replace |
| Cell enumeration / argv / layout | Re-implement matrix or argv building | `run_sweep.enumerate_matrix` / `build_argv` / `cell_dir_for` (D-07) | Frozen contracts pinned by tier-1 suites |
| Registry validation of failed cells | New join logic | The `load_failure_pairs` collect-all discipline + `_load_registry_key_sets` (run_sweep.py:1001-1089) | Same refusals every re-run path already performs |
| Lane-difference diagnostics | New diff format | `_lane_signature` + `_canonical_lane_value` shape (run_sweep_shard.py:618-670) | Deterministic set canonicalization (WR-05 iteration-order fix already solved) |
| SHA256 file verification (if cleanup re-verifies) | New hashing | `_sha256_file` (run_sweep_shard.py:536-554) | Streamed, OSError-tolerant, merge-proven |
| JSON schema validation | Hand-rolled key checks | `jsonschema` (dev group) + `schemas/` artifact | The repo's established frozen-contract pattern (14 schemas) |
| Terminal tables | Box-drawing/curse libraries | Plain prints (D14-02) | Stdlib-headless; Phase 16 owns TUI |

**Key insight:** this phase composes exclusively over frozen, test-pinned Phase 12/13 seams — the only genuinely new state machines are (a) the frozen v2 state shape, (b) the re-run claim genealogy, and (c) the cleanup gate. Everything else is wiring.

## Common Pitfalls

### Pitfall 1: Claim-filename collision on re-run (the D14-07 knot)
**What goes wrong:** `claim_filename(cell)` is keyed by cell identity only, so "FRESH O_EXCL claims" on a re-run cell EEXIST against the original failed claim; naive `claim_cell` returns None and the worker SILENTLY SKIPS the cell (the SC3 path, dispatch_core.py:694-704 increments `skipped`).
**Why it happens:** Phase 13's one-file-per-cell naming never needed generations (plain relaunch replaces stale claims atomically).
**How to avoid:** pick an explicit genealogy scheme BEFORE writing tasks — (A) retire-rename the superseded claim (canonical name always holds the latest attempt; audit files retained in place), (B) generation-suffixed claim filenames (breaks O(1) `read_claim` lookups and the `*.json`-glob invariants tests rely on), or (C) archive-copy the original to an audit name O_EXCL, then atomically replace the canonical slot (closest to existing mechanics; `rerun_of` links to the archived attempt). Whichever is chosen, the skip-filter (`relaunch_decision`) and every ledger-globbing test must be re-examined in the same task.
**Warning signs:** re-run tests seeing `skipped` counts instead of spawns; ledger file counts ≠ cell counts.

### Pitfall 2: Block-buffered stdout hides the live table
**What goes wrong:** the dispatcher's own stdout is block-buffered when piped (e.g. `python ... | tee log`); plain `print()` rows appear in bursts long after the event — the "live" view is not live, and a pty-lane test may hang waiting for a row.
**Why it happens:** Python's default buffering on non-tty stdout; existing dispatcher prints never needed flushing (end-of-run output).
**How to avoid:** `print(..., flush=True)` (or `sys.stdout.flush()` after each table render) inside the renderer; cover with the pty/piped lane, not just capsys (capsys captures at the Python layer and cannot see buffering).
**Warning signs:** capsys assertions pass while a real `| tee` run shows no table until exit.

### Pitfall 3: Queue-depth snapshot across two locks
**What goes wrong:** pending pops happen under `queue_lock` while state writes happen under `state_lock`; a depth read at write time can momentarily disagree with per-worker in-flight (a cell popped-but-not-yet-claimed is neither queued nor in-flight).
**Why it happens:** the two-lock structure predates the consumer contract.
**How to avoid:** either accept the transient (document that depth+in-flight is a best-effort snapshot; CPython `len()` is atomic) or maintain `queue_depth`/`in_flight` counters inside the SAME critical sections that change them, and snapshot under one lock. Decide once, encode in the schema doc, and pin with a test over a scripted sequence (D14-13's per-step assertions make the chosen semantics checkable).
**Warning signs:** schema consumers (Phase 16 TUI) double-counting or losing cells at boundaries.

### Pitfall 4: Stale pre-Phase-14 claims on lane replay
**What goes wrong:** claims written by Phase 13 lack `lane.cache_dir` (and any field Phase 14 adds); a replay that assumes the key exists KeyErrors or, worse, refuses to re-run old failures.
**Why it happens:** the lane dict extension changes the claim payload shape.
**How to avoid:** replay with tolerant reads (`lane.get("cache_dir")` → None = flag absent = build_argv contributes zero elements, the absent-parity discipline); fixture BOTH an old-shape and new-shape failed claim in the re-run tests.
**Warning signs:** re-run tests only ever using fresh claims.

### Pitfall 5: The re-run flag colliding with run_sweep's `--from-failures`
**What goes wrong:** naming the new orchestrator flag `--from-failures` (or letting it land in the passthrough) triggers the CR-01 manifest-file path (dispatch_core.py:1061-1085) — a ledger-driven value would fail `load_failure_pairs` validation or silently take the pair-fan-out semantics.
**Why it happens:** `--from-failures` is run_sweep-owned passthrough vocabulary with manifest-file semantics and seed fan-out; D14-07 needs exact-cell, ledger-driven semantics.
**How to avoid:** a NEW orchestrator-owned flag (shard parser, so it never reaches the passthrough), with an explicit refusal if the passthrough ALSO carries `--from-failures` on a re-run launch (two scoping mechanisms on one command = refuse, the collect-all discipline).
**Warning signs:** double-scoped re-run commands; argparse code-2 on missing `--seeds` when the ledger already defines seeds.

### Pitfall 6: Cleanup verification false-green on incomplete merges
**What goes wrong:** manifest-count equality alone can pass while the merged FILE TREE is missing cells (a worker manifest records planned cells; a never-run cell has no files — the merge tolerates and counts `never_ran`, run_sweep_shard.py:1019-1026); conversely a tree walk alone can miss stale-cell leaks the WR-03 guard exists for.
**Why it happens:** manifest and tree are two different truths; D14-10 deliberately requires BOTH checks.
**How to avoid:** verify = export dry-run (the exporter walks the FILE tree — `load_run_records`, export_runs.py:498) AND manifest cell-count equality vs the union of worker manifests; both green before the removal prompt; refuse naming the discrepancy otherwise.
**Warning signs:** cleanup tests that only assert the happy path; a removal offered after a deliberately-corrupted verification fixture.

### Pitfall 7: `--models`/`--seeds` requirements blocking the re-run (and the empty re-run)
**What goes wrong:** routing the re-run through the ordinary dispatch validation trips the `--models is required` refusal (dispatch_core.py:888-896) and the argparse-code-2 `--seeds` death; separately, a root with ZERO failed claims needs an explicit verdict, not a fall-through into full-matrix enumeration.
**Why it happens:** every existing path assumes operator-supplied scope; the re-run's scope is the ledger.
**How to avoid:** branch the re-run before those requirements; a zero-failed set prints an explicit "no failed cells to re-run" verdict (choose exit code deliberately — the drained-root precedent exits 0, dispatch_core.py:1246-1259; the clean-manifest precedent refuses non-zero, :1072-796 + tests; document the choice).
**Warning signs:** re-run e2e tests needing `--models`/`--seeds` to pass; empty-ledger re-run exiting via the zero-enumeration refusal.

### Pitfall 8: Static-mode byte-identity regressions
**What goes wrong:** any parser/routing drift in `run_sweep_shard.main()` changes static behavior; the 49-test shard suite + static pins fail (or worse, pass while argv/logs drift).
**Why it happens:** new flags touch the shared parser.
**How to avoid:** new flags are additive `parser.add_argument` entries (the `--mode` precedent, run_sweep_shard.py:372-384); the passthrough remainder for existing command lines must be byte-identical; run the static-identity pins (`test_mode_static_explicit_matches_default`, `test_static_mode_explicit_pins_argv_roots_and_logs`) in every affected task's verify.
**Warning signs:** shard-suite failures in unrelated tests.

## Code Examples

> These are DESIGN SKETCHES composed from the verified seams cited inline — building blocks are `[VERIFIED]`, compositions are proposals for the planner (marked `[ASSUMED]` as designs).

### State extension shape (MGPU-03, sketch)

```python
# Building blocks [VERIFIED: pipeline/dispatch_core.py:1184-1192,1213-1215]
state = {
    "schema_version": 2,          # bump DISPATCH_STATE_SCHEMA_VERSION (was 1, :123)
    "mode": "dispatch",
    "run_id": run_id,
    "status": "running",          # vocabulary: running | done | incomplete (:1250,1314,1332)
    "started_at": started_at,
    "updated_at": _now_iso(),
    "counts": {"total": ..., "completed": ..., "failed": ..., "skipped": ...},  # unchanged
    # ---- Phase 14 additive consumer fields (exact names = planner decision,
    #      frozen in schemas/dispatch_state.json in the SAME commit) ----
    "queue_depth": len(pending),              # Pitfall 3 snapshot semantics
    "workers": [                              # one entry per --workers index
        {"index": i, "gpu": gpus[i], "in_flight": None | cell_key,
         "cells": n, "completed": n, "failed": n}   # worker_stats (:1213-1215) + in_flight
        for i in range(workers)],
    "failures": [ ... ],                      # failed cell view w/ timestamps (count-vs-list tradeoff)
}
```

### Renderer row (D14-02, sketch)

```python
# Plain-line renderer; called under state_lock at every _write_state (Pitfall 2)
def render_state(state):
    print(f"[Dispatch] status={state['status']} "
          f"queue={state['queue_depth']} "
          f"done={state['counts']['completed']}/{state['counts']['total']} "
          f"failed={state['counts']['failed']}", flush=True)
    for worker in state["workers"]:
        cell = worker["in_flight"]
        cell_str = (f"{cell['model']}/{cell['task']}/seed_{cell['seed']}"
                    if cell else "-")
        print(f"  worker {worker['index']} gpu={worker['gpu']}: {cell_str}",
              flush=True)
```

### Cleanup mode routing (D14-09, sketch over the A6 precedent)

```python
# [VERIFIED precedent: pipeline/run_sweep_shard.py:1161-1184]
args, passthrough = parse_args()
if args.merge and args.mode == "dispatch":
    sys.exit("[Error] --mode dispatch cannot combine with --merge: ...")
if args.cleanup:
    # NEW combo refusals in the A6 shape: cleanup×merge, cleanup×dispatch-mode,
    # stray passthrough, --models; then:
    return run_cleanup(args, passthrough, runner=_DEFAULT_RUNNER)
```

### Export dry-run invocation seam (D14-10, sketch)

```python
# Production: subprocess (stdlib-headless — export_runs imports numpy/scipy/yaml
# at module top [VERIFIED: script/export_runs.py:117-119]); tests inject `runner`.
_DEFAULT_RUNNER = subprocess.run

def _export_dry_run(merged_root, runner):
    proc = runner([sys.executable,
                   str(run_sweep.PIPELINE_DIR.parent / "script" / "export_runs.py"),
                   "--dry-run", "--input-root", str(merged_root)],
                  capture_output=True, text=True)
    return proc.returncode == 0, proc.stdout
```

### Failed-claim scan (MGPU-04, sketch)

```python
# Ledger glob minus the lock (the happy-path test's exclusion idiom
# [VERIFIED: tests/test_dispatch_core.py:322-324])
claims = []
for path in sorted(ledger_dir.glob("*.json")):
    if path.name == DISPATCHER_LOCK_NAME:
        continue
    payload = read_claim(ledger_dir, ...)  # tolerant read (:317-343)
    ...
# A claim qualifies when its cell key matches the filename's tuple and
# state == CLAIM_STATE_FAILED; collect (cell, lane) pairs; D14-08 diff on lanes.
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `dispatch_state.json` minimal counts-only shape (schema v1) | Frozen consumer schema v2 (queue/workers/failures) + committed JSON Schema | This phase | TUI (Phase 16) and any consumer can parse against a contract; schema changes are same-commit gated (D14-04) |
| Manual `rm -rf` runbook step (docs/multi-gpu.md:157-160) | Verify-then-confirm `--cleanup` mode | This phase | Destructive cleanup becomes an evidence-gated command with tested refusal paths |
| `--from-failures` manifest-file re-run, lane flags re-typed by hand ("[same lane flags as this launch]", run_sweep_shard.py:1356-1362) | Ledger-driven exact-cell re-run with claim-time lane replay | This phase | Closes the 12-04 lane-blindness limitation (MGPU-04) |

**Deprecated/outdated:** none in this phase's scope (frozen contracts `run_sweep.py`/`run_finetune.py` untouched).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The renderer belongs at the `_write_state` choke point (vs. explicit render calls at each site) | Patterns 1 | Low — either works; choke point minimizes call sites (7) |
| A2 | `schemas/dispatch_state.json` + jsonschema is the right freeze mechanism (vs. a Python-dict-as-schema test) | Patterns 2 | Low — 14-schema precedent is strong; planner may prefer a lighter frozen-shape assert |
| A3 | The re-run flag is orchestrator-owned (shard parser), not a passthrough token | Pitfall 5 | Medium — if named/placed as run_sweep passthrough it collides with manifest-file semantics |
| A4 | A `--dry-run` FLAG on export_runs.py (walk+count, no writes) is the intended D14-10 seam (the decision says "export_runs.py dry-run" but no such mode exists today) | S6, Patterns 4 | Medium — alternative: a pure-count helper; flag keeps CLI parity and subprocess shape |
| A5 | The gen_progress D14-04 obligation is a keep-parsing test (gen_progress reads the tui scanner, not dispatch_state — verified), not a feature addition | S7 | Low — CONTEXT's deferred section explicitly excludes enhancements |
| A6 | pty lane shape = driver script under pexpect with fake spawner (the real CLI under pty would spawn real run_finetune children — impossible CPU-side) | S8 | Low — capsys carries the assertion matrix; one pty test proves terminal behavior |
| A7 | Zero-failed-cells re-run should exit 0 with an explicit verdict (drained-root precedent) rather than the non-zero zero-cell refusal (clean-manifest precedent) | Pitfall 7 | Low — planner picks; both precedents exist in-repo |
| A8 | `model_root`/`dataset_root`/`log_dir` MAY join the claim lane beyond D14-06's six-flag list (discretion; they affect re-run fidelity but are storage-location, not experiment, flags) | S2 | Low — additive; merge lane vocabulary records them when present |

## Open Questions

1. **Re-run claim genealogy (the D14-07 knot)** — options in Pitfall 1: (A) retire-rename superseded claims, (B) generation-suffixed filenames, (C) archive-copy + atomic replace of the canonical slot. Option C is closest to existing mechanics (canonical name keeps its O(1) meaning; the archive create can be the literal "FRESH O_EXCL" of D14-07; `rerun_of` points at the archive). Recommendation: C, with the skip-filter and ledger-glob tests updated in the same task. Needs planner ruling.
2. **`failures` in the frozen state: count vs. list** — a list gives Phase 16 a ready feed but rewrites O(failures) bytes per event on big sweeps; a count + ledger pointer keeps writes O(1). Recommendation: list of compact cell keys + timestamps (bounded by real sweep scales here), schema documents the growth bound. Planner decides.
3. **Exact re-run flag name and its passthrough interplay** (A3/Pitfall 5) — e.g. `--rerun-failed` (no value) vs. a valued form; plus the explicit refusal when the passthrough also carries `--from-failures`.
4. **Confirmation gate mechanics for D14-11** — "interactive `--yes` typed phrase or non-interactive refusal": recommend prompt-then-read-stdin requiring an exact typed phrase; a non-tty/EOF/mismatch refuses removal (workers untouched); tests drive stdin or monkeypatch `input`. Whether `--yes` also exists as an explicit phrase-carrying flag for automation is a planner call consistent with "refusal paths tested".
5. **Does `--cleanup` also remove per-launch worker LOGS?** — the manual recipe deletes both roots and logs (`rm -rf ...-mgpu-w{0,1}` + `rm -f ...-mgpu-w{0,1}-*.log`, docs/multi-gpu.md:159-160). D14-09 says "worker-root removal". Recommendation: remove roots; offer/mention logs in the same gate or leave logs (crash evidence, WR-02 spirit). Planner decides and tests it.
6. **Renderer module home (Claude's discretion)** — inside dispatch_core.py (zero Makefile change; file grows ~100 lines) vs. thin sibling `pipeline/dispatch_view.py` (needs PHASE14_MODULES lint guard + a lazy-import or parameter seam to avoid import cycles — dispatch_core already imports run_sweep_shard, so a sibling importing dispatch_core for constants must follow the lazy-import precedent at run_sweep_shard.py:749-753). Recommendation: keep it in dispatch_core.py unless line-count ergonomics argue otherwise.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python (uv-managed venv) | all pipeline work | ✓ | 3.14.6 system / 3.13 repo pin | — |
| uv | test/lint/typecheck lanes | ✓ | 0.13.0 | — |
| pytest | test harness | ✓ | 9.1.1 (dev group) | — |
| pexpect | pty lane (D14-13) | ✓ | 4.9.0 (dev group) | capsys-only if pty lane blocked |
| jsonschema | frozen-schema consumer test (D14-14) | ✓ | >=4.26.0 (dev group) | — |
| numpy/scipy/yaml | export_runs dry-run (subprocess + tests) | ✓ | data group via uv.lock | — |
| node | node lane (D14-16) | ✓ | v26.4.0 | — |
| GPU / dnallm | NOT required (CPU-only, fake children) | deliberately absent | — | by design (D14-16) |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** none. (Known environmental noise: 6 chmod-based + 1 version-pin pytest failures are pre-existing and outside any phase blast radius — MEMORY.md + 13-02-SUMMARY; targeted lanes run green.)

## Security Domain

`security_enforcement: true`, ASVS level 1, block-on high. This phase is local CLI tooling with no network surface; the applicable categories:

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Local operator tool; no auth surface |
| V3 Session Management | no | — |
| V4 Access Control | yes (operator-gated destructive action) | The cleanup removal gate: typed confirmation, static-roots-only, evidence-based dispatch-root refusal, refusal paths tested (D14-11) |
| V5 Input Validation | yes | Collect-all validation of every flag/path/JSON input (the `_validate_filters` discipline); tolerant reads of claims/manifests; percent-encoded + digest-suffixed claim filenames (no path traversal from registry names); `--gpus` arity-only validation |
| V6 Cryptography | no (no secrets) | SHA256 used for integrity verification only (`_sha256_file` reuse) |

### Known Threat Patterns for stdlib pipeline orchestration

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Symlink redirect of O_EXCL claim/lock creates | Tampering | POSIX no-follow guarantee of `O_CREAT\|O_EXCL` (documented in `claim_cell`, dispatch_core.py:288-311) — keep for any NEW claim-shaped create |
| Poisoned/unreadable ledger or manifest JSON on recovery paths | Tampering/Elevation | Tolerant reads that fail SAFE (requeue/refuse), never crash-or-trust (read_claim contract :317-343) |
| Destructive deletion of the wrong tree | Tampering | Removal restricted to frozen `{root}-mgpu-w{i}` names derived from the ONE `worker_root` authority; typed confirmation; refusal tests |
| State-file torn reads by external consumers | Denial of Service | Atomic tmp+`os.replace` writes (single writer) — consumers always parse a complete document |
| Second dispatcher / concurrent mutation | Elevation | Singleton O_EXCL lock + pid-liveness reclaim (A5/CR-02) — unchanged this phase |

## Sources

### Primary (HIGH confidence)
- `pipeline/dispatch_core.py` — read in full (1346 lines): state/claim/lock/worker seams, all line citations above
- `pipeline/run_sweep_shard.py` — read in full (1367 lines): mode routing, merge refusals, worker naming, spawn discipline
- `pipeline/run_sweep.py` — targeted reads: `load_failure_pairs` (:1001-1089), `cell_dir_for`/`base_model_name`/`build_argv` (:1092-1255), constants (:309-316), public surface scan
- `script/export_runs.py` — targeted reads: imports (:107-119), `load_run_records` (:498-551), `export_runs_tree`/`main` (:745-960); grep: no dry-run exists
- `script/gen_progress.py` — read in full (250 lines); `tui/services/sweep_monitor.py` grep: zero dispatch references
- `tests/test_dispatch_core.py` — harness block (:100-275), happy path (:281-350), CR-01 tests (:667-756), structure scan
- `tests/test_sweep_shard.py` — structure + merge-fixture scan
- `.planning/phases/14-orchestration-view-recovery/14-CONTEXT.md` — D14-01..D14-16 verbatim
- `.planning/REQUIREMENTS.md` (MGPU-03/04/05), `.planning/STATE.md` (Phase 13 rulings), `.planning/research/ARCHITECTURE.md` §A/§B
- `.planning/phases/13-dynamic-dispatch-core/13-PATTERNS.md`, `13-01-SUMMARY.md`, `13-02-SUMMARY.md`
- `pyproject.toml` (dev/tui groups), `Makefile` (:101-112, :174-208), `tests/conftest.py` (:42-44), `docs/multi-gpu.md` (:157-160, :242-245)
- Runtime probes: python/uv/pexpect/pytest/node versions (this session)

### Secondary (MEDIUM confidence)
- None — all claims are in-repo-verified or explicitly marked ASSUMED (design sketches A1-A8)

### Tertiary (LOW confidence)
- None — no web research used (config disables search providers; the phase is entirely in-repo)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies; everything runtime-verified
- Architecture: HIGH — every seam read with line citations; milestone research pre-ratified
- Pitfalls: HIGH — derived from actual code gaps discovered by reading (cache_dir lane gap, claim-filename collision, missing dry-run) plus harness idioms from the live tests
- Design sketches (A1-A8): ASSUMED by definition — flagged for planner/discuss confirmation

**Research date:** 2026-10-20
**Valid until:** 2026-11-20 (stable, in-repo; re-verify line numbers only if Phase 14 execution itself moves them)
