---
phase: 18-docs-authoring
title: 文档撰写 (Documentation)
status: approved
created: 2026-10-22
---

# Phase 18: 文档撰写 - Context

**Gathered:** 2026-10-22
**Status:** Ready for planning

<domain>
## Phase Boundary

All v1.3 surfaces are documented for the public release: docs/multi-gpu.md and
related runbooks rewritten for dispatch mode with copy-pasteable commands;
README + onboarding gain the multi-GPU dispatch and 5% subset workflow; TUI
usage documented in the TUI-DEMO.md precedent shape; version surfaces
consistent at 1.3.0. PLUS the maintainer-requested milestone test-results
report: a comprehensive HTML document with embedded screenshots/SVG covering
every phase's test outcomes, including real TUI execution captures and
analysis.

</domain>

<decisions>
## Implementation Decisions

### DOCS-01..04 (milestone requirements)
- **D18-01:** docs/multi-gpu.md rewritten for dispatch mode — every command copy-pasteable (incl. subset generation); the N=2 smoke procedure matches the EXECUTED Phase-15 reality (the r2 evidence); legacy static-shard mode documented as coexisting (--mode static, merge/cleanup semantics)
- **D18-02:** README + ONBOARDING/GETTING-STARTED gain the multi-GPU dispatch section + the 5% subset workflow (generate → configure → run → consume); zero stale static-sharding-only instructions remain
- **D18-03:** TUI multi-GPU usage documented (multi-GPU launch, monitoring, G lanes) in the TUI-DEMO.md precedent shape, verified against shipped screens (the Phase-16 UI-SPEC is the source of truth)
- **D18-04:** Version surfaces consistent at 1.3.0 (pyproject, uv.lock, TUI about milestone stage) — verify-only unless drift found; the about-screen milestone-stage row is rewritten to the DELIVERED v1.3 scope

### Milestone Test-Results Report (maintainer-requested 2026-10-22)
- **D18-05:** A comprehensive HTML report (self-contained, offline-viewable: inline CSS, relative/absolute asset links) at `baseline/v1.3-test-report.html` (or docs/ — planner picks the committed home) covering ALL SIX phases: goal, what shipped, test evidence (suite counts, key test names), the two gap-closure stories (15-04 run_record, 15-05 eval merge), GPU run evidence (smoke 155s/2 cells, sweep 272s/12 cells, dispatch_state done 12/12), and the review-loop outcomes
- **D18-06:** Screenshots/SVG embedded: (a) the Phase-17 browser pixel-verification PNGs (scatter + floating bars w/ whisker caps — already captured at /root/autodl-tmp/phase17-preview/); (b) TUI execution captures — the SVG snapshot goldens (monitor w/ G lanes + dispatch rows, run_config w/ 多GPU section, confirm golden) rendered/committed as report assets, PLUS at least one REAL execution capture of the TUI monitor via the pty lane if feasible (analysis text accompanies each image explaining what it proves)
- **D18-07:** Test-suite summary table: per-lane counts (pytest full-suite 2236-passed baseline vs 6 environmental, node 44/44, pty byte-silence, tier-1 contracts, determinism/vendored unmodified) + the known environmental exclusions (root-chmod class, HF-egress note)
- **D18-08:** The report is a DOCUMENT artifact (committed, linked from README or docs index) — not a CI job; regeneration is manual per the repo's static-file philosophy

### Claude's Discretion
- Report structure/sections order; asset directory layout (e.g. docs/report-assets/ vs baseline/)
- Whether TUI "execution" captures come from the SVG golden machinery re-run vs the existing committed goldens (uncommitted #50 batch may be referenced — planner notes the dependency)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- docs/multi-gpu.md (Phase-15-rewritten dispatch procedure — D18-01 extends, not rewrites), docs/TUI-DEMO.md (the TUI doc precedent), docs/METHODOLOGY.md (Phase-17 appendix already landed), README.md, docs/ONBOARDING.md
- .planning/phases/1[3-7]-*/[SUMMARY|VERIFICATION].md — the evidence corpus
- tests/tui/__snapshots__/*.svg (committed goldens + the 4 uncommitted #50 batch) — TUI visual material
- /root/autodl-tmp/phase17-preview/*.png + geometry evidence — browser chart verification
- /root/autodl-tmp/phase15-evidence/ — GPU run logs, SHA packs, dispatch_state snapshots
- The pty lane (tests/tui/test_pty_driver.py) — real-app execution harness if a live TUI capture is needed

### Established Patterns
- Docs verified against the codebase (the gsd-docs-update discipline); TUI-DEMO.md precedent shape
- Version surfaces: pyproject.toml / uv.lock / tui/services/about.py milestone row

### Integration Points
- README ↔ docs/multi-gpu.md ↔ TUI-DEMO.md cross-links; report linked from README's docs index

</code_context>

<specifics>
- Binding constraints: copy-pasteable commands must be exactly what executed (or verified equivalents); zero CI changes; static hosting philosophy; the report must be honest about environmental exclusions
- WINDOWS #50 (the 4 uncommitted TUI goldens) remains a maintainer-review item — the report may embed those SVGs but notes their pending-review status
- No push until milestone close (v1.3 policy)

</specifics>

<deferred>
- Post-milestone full leaderboard regeneration with multi-seed data (maintainer decision)

</deferred>
