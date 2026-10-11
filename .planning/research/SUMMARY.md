# Project Research Summary

**Project:** DNALLM-Mark v1.2 — TUI operator console (Textual) over the subprocess-driven sweep platform
**Domain:** Terminal UI console for ML benchmark launching/monitoring (brownfield integration)
**Researched:** 2026-10-11
**Confidence:** HIGH overall (stack facts verified against PyPI + Textual v8.2.8 source; architecture facts verified by direct repo inspection; feature/pitfall tiers MEDIUM — official docs + convergent community evidence)

## Executive Summary

The v1.2 milestone adds a Textual 8.2.8 TUI console that lets benchmark operators select from the 62-model x 50-dataset matrix, manage dataset downloads, configure and safely launch sweeps, and monitor/recover multi-day GPU runs over SSH — without changing any existing pipeline contract. Research converged strongly on one architectural posture: **the TUI is a thin read-plan-launch-observe shell, never a participant in the sweep**. Execution always goes through `python pipeline/run_sweep.py` as a subprocess (argv list, `PYTHONUNBUFFERED=1`, `start_new_session=True`); preview imports the same module's already-pure, stdlib-only planning functions (`enumerate_matrix`, `apply_priority_order`) so preview and execution cannot diverge; live state is derived by polling the filesystem (per-cell `run_record.json`, `trainer_state.json` markers) — not in-process callbacks, because Textual 8.x has no file-watching API and cross-process truth is on disk anyway. A `tui/services/` layer kept strictly free of textual imports, with constructor-injected fakes, keeps every service unit-testable CPU-side in CI.

The stack addition is surgically small: a new `[tui]` uv group (`textual>=8.2,<9`, `platformdirs`), `pytest-asyncio>=1.4,<2` in dev with `asyncio_mode = "auto"`, ty/ruff coverage of `tui/` from day one, zero new CI jobs. The critical-safety and critical-UX patterns are all well-precedented: terraform-style confirmation gates (dry-run preview -> ModalScreen confirm -> typed phrase for the full E2' sweep, which must never be a persisted default), k9s-style filter+mark-set selection over row tables (never an editable 3,100-cell matrix), Optuna-style poll-and-attach monitoring, and tee-to-file log streaming (RichLog bounded, disk file authoritative). The four sanctioned `run_sweep.py` argv-threading additions (`--subset_file`, `--effective-batch`, `--num_train_epochs`, `--cache_dir`) are the only pipeline modifications.

Key risks are all P1-foundation decisions that are near-impossible to retrofit: event-loop blocking (never sync-call the executor/SDK in handlers — subprocess or `@work(thread=True)` always), view-vs-filesystem desync (one tolerant artifact-loader module; cold-read on re-launch detection; `sweep_failures.json` is deleted at sweep start), terminal-matrix fragility over SSH/tmux (glyph+color redundancy, keyboard-first, blessed tmux config; known open Textual bug #6668 on reattach), and client-side duplication of benchmark semantics (hard rule: TUI orchestrates, never computes — import or subprocess the existing implementations). Maintainer-fixed boundaries anchor the roadmap: FlopsCounter port is an early, TUI-independent work package before P3; multi-GPU (P4) is hard-gated on single-GPU validation; no pipeline runs without explicit authorization.

## Key Findings

### Recommended Stack

From STACK.md. Real install delta is ~2 pure-Python packages; rich/pygments/markdown-it-py/pyyaml are already in uv.lock transitively.

- **Textual 8.2.8** (`>=8.2,<9`, new `[tui]` group) — the only pure-Python full-screen TUI framework with a first-class headless test driver; strict SemVer with frequent tiny majors means the `<9` cap and deliberate CHANGELOG-driven upgrades are mandatory discipline.
- **pytest-asyncio 1.4.0** (dev group, `asyncio_mode = "auto"`) — runs `App.run_test()` Pilot tests under the existing pytest 9.1.1 suite.
- **platformdirs 4.x** (declared in `[tui]`) — `~/.config/dnallmmark/` persistence; already a textual transitive, declared to stop transitive-luck imports.
- **JSON (stdlib)** for settings, templates, download queue — matches repo data contract.
- **Do NOT add:** textual-dev/textual-serve in committed groups (use `uv run --with` on demand), pytest-textual-snapshot (churn; behavioral Pilot assertions instead), PyYAML pre-need, JS tooling.
- **Load-bearing API facts (verified):** workers (`@work`, `exclusive=True`, thread workers + `post_message`) for all blocking work; `asyncio.create_subprocess_exec` + `readline()` loop into RichLog (never `communicate()`); **no filesystem-watching API exists in 8.x** — poll with `set_interval`.

### Expected Features

From FEATURES.md. Evidence: k9s, nvitop, Optuna Dashboard, lm-eval, accelerate, terraform plan, hf CLI.

**Must have (table stakes):**
- FC1 — filterable model/task tables + spacebar mark-set multi-select + presence columns from `n_audit.json` + tier presets; read-only matrix pane as summary only
- FC2 — run-config form validated against registries, defaults from `finetune_config.yaml`, derived-value preview, persisted profiles
- FC3 — launch gate: env_smoke preflight -> dry-run cell-table preview -> ModalScreen confirm -> **typed phrase for full E2' sweep**
- FC4 — polling monitor (2-5 s, adjustable), state-colored cell table, attach-to-running-sweep mode, resume recognition
- FC5 — log tailing with `PYTHONUNBUFFERED=1` fix, bounded RichLog, tee-to-file, failed-cell log retrieval from disk
- FC6 — failure list -> log drill-down -> confirmation-gated `--from-failures` re-run; no auto-retry loops
- FC7 — download manager: presence table, persistent resumable queue (maintainer answered "needed"), modelscope CLI subprocess, n_audit row-count verification (a genuine cheap differentiator)
- FC8 — JSON template import/export with registry validation, `sweep_priorities.json` tier interop, `schema_version`

**Should have (differentiators):** cross-axis selection preview ("72 cells, 2 datasets missing"), dry-run cost estimate from historical runtimes, saved-plan exact-cell launch, per-cell performance drill-down.

**Defer (v2+/out):** multi-GPU orchestration view (P4, hard-gated), web read-only mirror, analytics, Zenodo bulk bundle, DDP layer (P4 decision).

### Architecture Approach

From ARCHITECTURE.md. Three repo-verified anchors drive everything: (1) the filesystem is the progress API — `run_record.json` is written per cell inside the loop; manifests are post-run audit artifacts only; (2) child logs flow through run_sweep's uncaptured stdout, so piping run_sweep's stdout yields interleaved training logs for free; (3) planning functions in `run_sweep.py` are pure and importable, proven by `tests/test_sweep.py`.

**Major components:**
1. `tui/app.py` — composition root only (wires services, MODES, bindings); no business logic
2. `tui/screens/` — Selection, DataManager, RunConfig, Monitor, Modal gates; receive services via constructor injection
3. `tui/services/` — registries, sweep_plan (wraps run_sweep pure functions), launcher (async subprocess + stream + terminate/detach), monitor (frontier filesystem scan), downloads (CLI + queue state machine), settings (XDG), templates, env_gate — **zero textual imports, enforced by a 5-line import test**
4. `~/.config/dnallmmark/` — settings.json, templates/, downloads.json; atomic writes; never repo-local
5. Two-tier tests: tier-1 headless service tests (no textual, CI-safe), tier-2 Pilot tests with fakes

**Patterns:** subprocess execution + pure-import preview (dual-use of run_sweep); filesystem-as-API polling with frontier-first scanning at 9,300-cell scale (~10 ms full rescan every 60 s); detach-by-default supervision with explicit Kill/Detach/Cancel exit prompt; static model sharding (not work-stealing) for P4.

### Critical Pitfalls

From PITFALLS.md. All prevention is P1-foundation work except where noted.

1. **Blocking the event loop** (sync subprocess/SDK calls in handlers) — never import-and-run the executor; subprocess or `@work(thread=True)` + `post_message` always; `exclusive=True` on single-slot workers. P1, non-retrofittable.
2. **View-vs-filesystem desync** — `sweep_failures.json` deleted at sweep start (WR-06); `run_record.json` written non-atomically; resume marker written last. One tolerant artifact-loader (keep last-known-good on truncated JSON), drop-all-cache on re-launch detection, cold-read on reattach.
3. **Terminal matrix fragility over SSH/tmux** — mouse-eats-scrollback, Textual #6668 reattach crash, 256-color degradation. Glyph+text+color status redundancy, keyboard-first, blessed tmux config documented, restart-after-reattach guidance.
4. **Client-side duplication of benchmark semantics** — the correctness brand's #1 threat (the web UI already has this anti-pattern). TUI reads artifacts and orchestrates; imports/subprocesses existing implementations; shows the actual argv it will exec.
5. **The "TUI becomes the only interface" trap** — every capability must exist as CLI capability and stay CI-exercised; E2' authorization records the exact CLI command, never a persisted TUI state.

Also load-bearing: dependency-group hygiene (`[tui]` group day one; data/gpu lanes never see textual), Pilot test discipline (`await pilot.pause()`, no `time.sleep`, injectable intervals), log tee-to-file (never skip), and resource ceilings (bounded RichLog, one log-tail per viewed cell, overnight soak check).

## Implications for Roadmap

### Phase 0/WP-A: FlopsCounter port (pipeline-side, parallel track, BEFORE P3)
**Rationale:** Maintainer directive (must land before P3); independent of every TUI phase; benefits E2' FLOPs correctness and the leaderboard efficiency axis regardless of TUI fate.
**Delivers:** FlopsCounter (20+ architecture hooks) ported from `dnallmmark_pipeline.py` into `run_finetune.py`, with tests. Do not couple its verification to TUI phases.

### Phase 1: TUI foundation (skeleton + selection)
**Rationale:** Worker/subprocess discipline, loader seam, dependency group, test harness, and color/glyph conventions are all non-retrofittable — they must land with the first screen. Every later phase consumes settings/registries.
**Delivers:** `tui/` package (`python -m tui`), services skeleton (settings, registries, tolerant artifact-loader), selection screen (filterable tables + mark-set + presets + presence columns), `[tui]` group + ty/ruff wiring + `make tui`, tier-1/tier-2 test harness + CI decision, import-linter test pinning services textual-free.
**Addresses:** FC1, FC8 validation module foundation. **Avoids:** Pitfalls 1, 3, 4, 5, 6, 7, 8 (all have P1 prevention).
**Gate:** 62x50 matrix renders with filters; CI green without GPU/dnallm.

### Phase 2: Data manager (downloads + verification)
**Rationale:** Depends only on P1 (registries/settings). Must land before launch because env_smoke checks dataset presence — a FAIL there is undiagnosable without the manager. FC7 blocks honest FC3.
**Delivers:** `services/downloads.py` persistent queue + modelscope CLI driver + n_audit row-count verification via `script/audit_n_frequencies.py` subprocess; double-nesting zip gotcha detection.
**Addresses:** FC7. **Avoids:** sync-SDK freezing (thread/subprocess discipline), token leakage (no credentials stored).
**Gate:** one real missing dataset round-trips download -> verify -> presence flips.

### Phase 2.5: run_sweep argv threading (small; lands with P2 or P3, before RunConfig full surface)
**Rationale:** The config form cannot promise flags that do not exist; pipeline-side flags land first with tests (CLI-first rule), then get surfaced in the TUI.
**Delivers:** The four sanctioned additive flags on `run_sweep.py` — `--subset_file`, `--effective-batch`, `--num_train_epochs`, `--cache_dir` — byte-identical when absent, argv-shape asserted in `tests/test_sweep.py`. These are the ONLY pipeline modifications.

### Phase 3: Run config + single-GPU launch + monitoring
**Rationale:** Consumes P1 (screens/services), P2 (data readiness), P2.5 (flags), WP-A (FLOPs-correct runs). Launcher stdout stream and monitor filesystem scan are one screen — they land together.
**Delivers:** RunSpec form + preview via imported pure functions (NOT `--dry-run` against a real output root — Anti-Pattern 3), env_smoke gate, E2' typed-confirm modal, `services/launcher.py` (PIPE + tee-to-file + detach semantics + Kill/Detach exit prompt), monitor screen, failure list + log drill-down + gated `--from-failures` re-run, FC8 template import/export.
**Addresses:** FC2, FC3, FC4, FC5, FC6, FC8. **Avoids:** Pitfall 2 (output loss/teardown), terminal-matrix verification (4-environment manual checklist), desync under live timing.
**Gate:** bounded smoke (1 model x 1 task x 1 seed, 1 epoch) launched, monitored, failure re-run exercised end-to-end on GB10; E2' gate provably blocks full sweeps. **No E2' execution without explicit maintainer authorization.**

### Phase 4: Multi-GPU orchestration (HARD-GATED on P3 single-GPU validation)
**Rationale:** Maintainer decision (single-GPU success before multi-GPU). Architecture is N launchers + static model shards — cheap only after single-GPU is proven; sharding must equally be CLI-invocable.
**Delivers:** N `SweepProcess`es with `CUDA_VISIBLE_DEVICES` + disjoint model shards, per-worker health, isolation re-run, merged read-only dashboard, explicit DDP-vs-sharding decision documented.
**Addresses:** FC4 differentiator (worker/GPU pane). **Avoids:** Pitfall 9 regression point (orchestration must not become TUI-only).

### Phase Ordering Rationale

- WP-A first/parallel: pipeline-critical-path, TUI-independent (maintainer sequencing).
- Settings/registries before everything: every screen consumes them.
- Downloads before launch: env_smoke presence FAILs are undiagnosable otherwise; missing data must not fail deep in a sweep.
- Flag-threading before RunConfig: the form cannot promise nonexistent flags (CLI-first rule).
- Monitoring with launch (same phase): the launcher's stdout stream and the monitor's scan are one screen.
- Multi-GPU last: N copies of a proven launcher + shard math; dynamic work-stealing rejected (marker-skip is the only concurrency guard).
- TUI restart never loses the view (attach-mode monitoring) — which also neutralizes the known tmux-reattach crash (#6668): restarting the TUI is cheap by design.

### Research Flags

Phases likely needing `--research-phase` during planning:
- **Phase 4 (multi-GPU):** scheduling strategy (static sharding vs alternatives), DDP-vs-sharding decision, per-worker health design — genuinely open design space.
- **Phase 2 (downloads, narrow item):** ModelScope CLI progress parsing / resume behavior specifics (MEDIUM confidence flags) — confirm in phase, not a full research phase.

Phases with standard patterns (skip research-phase):
- **Phase 1 (foundation):** Textual scaffolding, workers, Pilot testing — exceptionally well documented officially; all API facts pre-verified in STACK/ARCHITECTURE.
- **Phase 2.5 (argv threading):** established repo pattern (`--peft`/`--train_fraction` precedent), tests shape known.
- **Phase 3 (launch/monitor):** every pattern (subprocess streaming, polling, modal gates) is documented and repo-anchored; pitfall checklist already enumerated.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Every version/footprint fact verified against PyPI JSON API + Textual v8.2.8 source tree; ty compatibility verified (py.typed present) |
| Features | MEDIUM | Official docs of k9s/Optuna/lm-eval/accelerate/terraform/hf read directly; Context7 unavailable this run capped tiers at MEDIUM; no single-source claims relied upon |
| Architecture | HIGH | Repo facts verified by direct inspection of run_sweep/run_finetune/env_smoke/tests; Textual API facts from official docs fetched fresh |
| Pitfalls | MEDIUM | Community + official-docs triangulated; no single authoritative corpus exists for Textual integration post-mortems — inherent ceiling |

**Overall confidence:** HIGH for architecture/stack (the roadmap-shaping decisions), MEDIUM for practice-level details (ModelScope CLI flags, tmux edge behavior) — each flagged for in-phase confirmation.

### Gaps to Address

- **ModelScope progress plumbing:** SDK callbacks vs subprocess tqdm parsing — affects FC7 estimate; confirm during Phase 2.
- **`--effective-batch` final semantics** (open Q7, maintainer decision Pending): GA = max(1, N//batch_size), default 16 — TUI only surfaces it; decision needed before P2.5.
- **CI tier-2 (Pilot) lane policy:** ARCHITECTURE recommends running Pilot tests in CI via `--group tui` (textual is CPU-only, pure-Python); resolve the "CI must not introduce TUI runtime" checkbox at P1 discuss — recommendation: allow textual-the-library in the test lane, forbid any display/GPU runtime.
- **platformdirs vs hand-rolled XDG:** STACK recommends declaring platformdirs (already a transitive); ARCHITECTURE sketched a ~10-line hand-rolled helper. Resolution: use platformdirs (explicit declaration costs nothing, avoids transitive-luck imports) — trivially swappable behind `services/settings.py`.
- **Preview mechanism:** FEATURES/PITFALLS suggested `--dry-run` subprocess for preview; ARCHITECTURE proved dry-run writes `sweep_manifest.json` into the output root (Anti-Pattern 3, clobbers real manifests). Resolution: import pure functions for preview; dry-run subprocess only against a throwaway temp root if ever needed.
- **Per-cell log persistence format** (rotation/naming): decide in Phase 3 planning.
- **Multi-GPU strategy** (open Q3): Phase 4 discuss item.

## Sources

### Primary (HIGH confidence)
- PyPI JSON API — textual 8.2.8, rich, pytest-asyncio, platformdirs, pyyaml, ty (versions, requires_dist, wheel purity), fetched 2026-10-11
- Textual v8.2.8 source tree + CHANGELOG at tag — no watcher API, py.typed present, major-version break history
- Textual official guides (workers, testing, screens, CSS, DataTable/RichLog) — fetched 2026-10-11
- Repo inspection — `pipeline/run_sweep.py`, `run_finetune.py`, `env_smoke.py`, `pyproject.toml`, `tests/conftest.py`, `docs/TUI-REQUIREMENTS.md`, `.planning/PROJECT.md`

### Secondary (MEDIUM confidence)
- Textualize discussions #3788/#245/#2689 (subprocess streaming, buffering pitfall); issue #6668 (tmux reattach crash)
- k9s, nvitop, Optuna Dashboard (+TrialState reference, Tunny mirror), lm-evaluation-harness, accelerate, terraform plan, huggingface_hub download docs — feature-pattern evidence
- textual-shell, terraform-tui, physicsnemo-curator, c3t — convergent community implementation patterns
- ModelScope CLI flag details (channel validated in-repo at 50/50; specific flags MEDIUM)

### Tertiary (LOW confidence)
- Windows Terminal support matrix (moot — Linux/GB10 only)
- Textual example gallery claims (404s; not relied upon)

### Maintainer-fixed boundary decisions incorporated
- FlopsCounter port = early work package, before P3, TUI-independent
- Multi-GPU P4 hard-gated on single-GPU validation
- Sanctioned run_sweep argv threading limited to `--subset_file` / `--effective-batch` / `--num_train_epochs` / `--cache_dir`
- No pipeline runs (code only); E2' needs explicit maintainer authorization; DNALLM sibling repo read-only

---
*Research completed: 2026-10-11*
*Ready for roadmap: yes*
