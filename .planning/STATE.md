---
gsd_state_version: "1.0"
milestone: v1.2
milestone_name: TUI任务
current_phase: 08
current_phase_name: TUI Foundation (Env Check & Selection)
status: executing
stopped_at: Completed 08-02-PLAN.md
last_updated: "2026-10-11T11:36:01.074Z"
last_activity: 2026-10-11
last_activity_desc: Phase 08 execution started
state_head: ef56567c24206fdd5af0275a990e961a5efd4092
progress:
  total_phases: 6
  completed_phases: 1
  total_plans: 13
  completed_plans: 8
  percent: 17
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-11)

**Core value:** Every number on the public leaderboard is correct and reproducible from code that external reviewers can trust. (v1.2 extension: operators drive the platform confidently from one terminal console without losing CLI parity.)
**Current focus:** Phase 08 — TUI Foundation (Env Check & Selection)

## Current Position

Phase: 08 (TUI Foundation (Env Check & Selection)) — EXECUTING
Plan: 3 of 7
Status: Ready to execute
Last activity: 2026-10-11 — Phase 08 execution started

Progress (v1.2): [██████░░░░] 62% (8/13 plans)

## Performance Metrics

**Velocity (v0.7.1, archived):**
- Total plans completed: 24 (6 phases)
- Average duration: ~24 min/plan
- Total execution time: ~9.7 hours

**By Phase (v0.7.1):**

| Phase | Plans |
|-------|-------|
| 01 / 02 / 03 | 3 / 3 / 4 — all complete |
| 04 / 05 / 06 | 5 / 4 / 5 — all complete |

**v1.2:** Phase 7 complete (6 plans, 2026-10-11); Phase 8 plans 1-2 of 7 complete (08-01, 08-02).

*Updated after each plan completion*
**Per-Plan Metrics:**

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 07 P01 | 13 min | 3 tasks | 7 files |
| Phase 07 P02 | 11 min | 3 tasks | 5 files |
| Phase 07 P03 | 12 min | 3 tasks | 2 files |
| Phase 07 P03 | 12 min | 3 tasks | 2 files |
| Phase 07 P04 | 8 min | 2 tasks | 2 files |
| Phase 07 P05 | 10 min | 3 tasks | 10 files |
| Phase 07 P06 | 5 min | 3 tasks | 1 files |
| Phase 08 P08-01 | 17 min | 2 tasks | 2 files |
| Phase 08 P08-02 | 84 min | 2 tasks | 11 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table. Recent decisions affecting current work:

- Roadmap v1.2 revision (maintainer, 2026-10-11): custom entries split along the maintainer-drawn seam — the pipeline-side registry overlay (CUST-05) joined Phase 7 (same run_sweep/run_finetune files, same byte-identical-when-absent discipline as argv parity, must precede wizard consumption); the wizard surface (CUST-01..04, CUST-06) is a dedicated Phase 9 directly after the selection foundation it marks; downstream phases renumbered 9→10, 10→11, 11→12 (free — zero plans existed)
- Custom/official registry separation is binding (maintainer refinement: 自定义不与官方放在一起，免得冲突): wizards write only user-owned `~/.config/dnallmmark/custom_{models,datasets}.json`; official `pipeline/{models,datasets}_info.json` never written by custom flows; overlay fails fast on custom-key collision with official; absent custom files = byte-identical behavior, existing tests untouched — recorded as binding constraint 11 in ROADMAP.md
- Roadmap v1.2 (pre-revision): pipeline enablement → TUI foundation → data manager → config/launch/monitor (single-GPU) → multi-GPU + extras; Phase 12 hard-gated on Phase 11 validation (maintainer sequencing 单卡→多卡); requirement count corrected 28 → 32 → 38 (CUST category added by revision)
- Roadmap v1.2: all three PIPE-* plus CUST-05 in Phase 7 — pipeline-side verification deliberately uncoupled from TUI phases; PIPE-02 folded there per coarse granularity (research sketched it as a separate "Phase 2.5")
- Roadmap v1.2: WEB-01 + TEST-01 attached to Phase 12 (canonical screens are final only after multi-GPU views exist; keeps Phase 11 focused on the bounded-smoke gate). TEST-01 follows the requirement (official snapshot goldens) over the research preference (Pilot-only assertions) — requirement wins
- Carried binding constraints (full list in ROADMAP.md): E2' maintainer dual-gate; CI GPU/dnallm-free with textual-the-library allowed in a CPU test lane (ratify in Phase 8 discuss); DNALLM repo read-only; CLI parity rule; TUI orchestrates never computes; ruff + ty gates from Phase 7 on
- [Phase 07]: flops_report.json v1 schema published exactly as derived (maintainer ratified publish-as-derived at the 07-01 Task-1 checkpoint, 2026-10-11); D-27 one-way contract — field names immutable downstream
- [Phase 07]: flops_report layer_details/total_flops_exact values typed number (not integer): the verbatim HyenaFilter FFT formula emits fractional FLOPs, and an integer map would reject legitimate writer output (Rule-1; every ratified field name unchanged)
- [Phase 07]: FlopsCounter ported behind lazy _torch_nn/_torch seams with no module-top torch import — the CPU dev/CI lane imports and stub-tests the full 20+ architecture dispatch (PIPE-01 criterion 2)
- [Phase 07]: CUST-05 registry overlay seam landed: DNALLMMARK_CUSTOM_REGISTRY_DIR whole-dir override (D-07 覆盖整个目录 — no suffix on the env value; the dnallmmark join applies to the XDG/~/.config bases only); custom entries add-only, collision fails fast naming key + both file paths
- [Phase 07]: platformdirs refinement: hand-rolled env>XDG>home resolver in registry_loader (platformdirs undeclared in every CPU-side group — RESEARCH Pitfall 2; reserved for Phase 8 [tui] by constraint 10); identical Linux path, Phase 8 may consolidate behind the seam
- [Phase 07]: 07-03 PIPE-02 argv threading: the four sweep flags are pure pass-through with zero GA arithmetic (GA=max(1, N//bs_new) stays child-side, D-10/D-16); underscore names only, bare --effective_batch_size=16, absent flag = zero argv elements and zero manifest keys (D-11/D-12/D-13)
- [Phase 07]: D-14 implemented as sweep-owned shallow collect-all (_validate_subset_file: readable-JSON/object/registry-key/int-list with bool exclusion) against the overlay-merged registry view; child validate_subset_file stays authoritative — defense-in-depth, no shared import (sweep stays stdlib-only headless-importable)
- [Phase 07]: Manifest records present flags in cells only (D-13); run_record.json untouched (D-02 spirit); dry-run path now routes through _manifest_payload so planned and executed cells record identically; byte-determinism tests green unmodified
- [Phase 07]: 07-04 PIPE-01 integration: FLOPs always-on via the pre-training calibration slot (count_split_tokens -> unconditional FlopsCounter -> single no_grad forward via calibration_forward -> remove_hooks BEFORE the DNATrainer ctor) + a single post-success flops_report.json write ordered final_metrics < flops_report < trainer_state marker (WR-13 three-artifact chain); run_record/final_metrics payload contracts untouched (D-01/D-02)
- [Phase 07]: 07-04 hardware capture (D-05): gpu_device verbatim from torch.cuda.get_device_name() (no enum normalization, 5090D/4090D pass through), train_time from metrics.get('train_runtime') (None-tolerant), max_mem_gb from the peak-memory counter read at write time inside the rank-0 success block BEFORE trainer.evaluate() — scopes the captured peak to training
- [Phase 07]: [Phase 07]: 07-05 D-04 closed: dnallmmark_pipeline.py deleted (final commit 1b74037e — git history is the reference); the five parity expectations in test_run_finetune_contracts.py are self-contained sha-documented verbatim literals; zero live-code references remain and .claude/CLAUDE.md's FLOPs reference of record is pipeline/flops_counter.py
- [Phase 07]: [Phase 07]: 07-05 provenance convention: after a D-04-style deletion, live-code/test comments cite the deleted source by description + final commit sha, never by live path (the Task-1 comment template vs Task-2 zero-grep-gate reconciliation)
- [Phase 07]: 07-06 runtime proof: bounded GB10 smoke (plant-dnabert-6mer x iDNA_ABF_datasets__5mC, 1 epoch, default mode, 77s wall, 1.56GB peak) emitted flops_report.json with all six D-23 criteria green — ratio 0.332 vs HF total_flos (the ~1/3 fwd-only expectation), gpu_device 'NVIDIA GB10' verbatim, uncovered_layers empty; PIPE-02 proven live via dry-run (present flags recorded, absent flags leave no keys, D-13)
- [Phase 07]: 07-06 evidence discipline: real run artifacts stay gitignored under pipeline/finetuned/ (D-26) — the committed evidence is the SUMMARY's pasted key fields + mechanical assertion outputs (D-25); the bounded-smoke evidence shape is the template for Phase 11's bounded smoke
- [Phase 08]: 08-01 D-02 landed: env_smoke kernels return frozen CheckResult(name/ok/lines) with zero printing; main() is the sole renderer (_emit + two segment loops); CLI stdout and 0/1 exit proven byte-identical by a golden characterization suite (S1/S2/S3) recorded from live runs + live before/after diff + the three untouched grep-lock tests
- [Phase 08]: 08-01 check_peft stays byte-exact un-annotated (def check_peft(): pinned by test_env_smoke_peft_check_is_gating); torch-unavailable cuda/matmul become ok=False empty-lines CheckResult placeholders (same two-failed-groups semantics, type-clean list)
- [Phase 08]: 08-02 package legitimacy gate closed (maintainer verdict 2026-10-11, delegation on record): textual 8.2.8 (Textualize), platformdirs 4.13.0 (tox-dev, signed provenance — same-day release accepted), pytest-asyncio 1.4.0 (pytest-dev) all APPROVED via PyPI page + JSON API; uv.lock pins exactly these versions; verdict lines recorded verbatim in 08-02-SUMMARY.md
- [Phase 08]: 08-02 typecheck lane gains --group tui (Rule 3, empirically proven): ty cannot resolve textual's py.typed types in a fresh env — make typecheck failed tui/app.py with unresolved-import in exactly CI's lint-typecheck state, so the recipe installs the maintainer-approved [tui] group in that existing CPU static lane; NO replace-imports-with-any entry (real types, per RESEARCH); data/gpu lanes still never see textual; ci.yml byte-identical
- [Phase 08]: 08-02 spine landed: [tui] group (exactly textual>=8.2,<9 + platformdirs>=3.6,<5), make tui (--group tui --group gpu, Pitfall 10), PHASE8_TUI wildcard lint guard (later tui files join coverage with zero Makefile edits), asyncio_mode=auto (A3 proven — 560 sync tests green), tui/ skeleton with the services-textual-free contract declared and the __file__-derived REPO_ROOT bootstrap; uv sync for the tui group must use --inexact (plain sync is exact and strips the GB10 GPU stack + dnallm)

### Pending Todos

None yet.

### Blockers/Concerns

- GB10 GPU work is permanently outside CI scope; ALL pipeline execution (including Phase 11's bounded smoke) requires explicit maintainer authorization — this milestone is code-first
- Zenodo record 19135551 not yet public — DATA-04's bulk entry is designed in Phase 10 but activates only when the record publishes
- ModelScope CLI flag/progress-parsing specifics are MEDIUM confidence — confirm during Phase 10 (narrow in-phase item, not a research phase)
- Custom-registry storage location (`~/.config/dnallmmark/` vs repo-local ignored dir) and the exact overlay read seam are Phase 7/9 discuss items — the user-owned-file principle itself is fixed
- v0.7.1 carryover registry questions (space/SPACE merge decision; 7 models without locatable public cards) remain maintainer-owned — outside v1.2 scope unless registries are touched

## Deferred Items

Items acknowledged and deferred at milestone close, most recent first:

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| *(none)* | | | | |

## Session Continuity

Last session: 2026-10-11T11:36:01.041Z
Stopped at: Completed 08-02-PLAN.md
Resume file: None

## Operator Next Steps

- Continue Phase 8 execution: plans 08-03..08-07 pending — `/gsd-execute-phase 08` (next: 08-03 tui skeleton tracer on the 08-02 spine)
