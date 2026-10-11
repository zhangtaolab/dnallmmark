---
gsd_state_version: "1.0"
milestone: v1.2
milestone_name: TUI任务
current_phase: 07
current_phase_name: Pipeline-Side Enablement (FlopsCounter Port, argv Threading & Registry Overlay)
status: executing
stopped_at: Completed 07-02-PLAN.md
last_updated: "2026-10-11T07:02:08.876Z"
last_activity: 2026-10-11
last_activity_desc: Phase 07 execution started
state_head: 50e0cfc3a95f6c470abeffe8ee30bf398e48e580
progress:
  total_phases: 6
  completed_phases: 0
  total_plans: 6
  completed_plans: 2
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-11)

**Core value:** Every number on the public leaderboard is correct and reproducible from code that external reviewers can trust. (v1.2 extension: operators drive the platform confidently from one terminal console without losing CLI parity.)
**Current focus:** Phase 07 — Pipeline-Side Enablement (FlopsCounter Port, argv Threading & Registry Overlay)

## Current Position

Phase: 07 (Pipeline-Side Enablement (FlopsCounter Port, argv Threading & Registry Overlay)) — EXECUTING
Plan: 3 of 6
Status: Ready to execute
Last activity: 2026-10-11 — Phase 07 execution started

Progress (v1.2): [░░░░░░░░░░] 0%

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

**v1.2:** no plans executed yet.

*Updated after each plan completion*
**Per-Plan Metrics:**

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 07 P01 | 13 min | 3 tasks | 7 files |
| Phase 07 P02 | 11 min | 3 tasks | 5 files |

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

Last session: 2026-10-11T07:02:01.307Z
Stopped at: Completed 07-02-PLAN.md
Resume file: None

## Operator Next Steps

- Maintainer reviews/approves the revised v1.2 roadmap, then `/gsd-discuss-phase 7` (config discuss_mode: discuss)
