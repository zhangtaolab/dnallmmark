---
phase: 12-multi-gpu-orchestration-console-hardening
plan: "02"
subsystem: web
tags: [web-mirror, progress-page, static-site, gen-progress, scanner-import]
requires:
  - "tui/services/sweep_monitor.py pure scanners (Phase 11, textual-free by import lock)"
  - "12-01 PHASE12_MODULES lint guard (gen_progress.py joins make lint on arrival)"
  - "the existing static site's controller/CSS vocabulary (finetuning.js, components.css)"
provides:
  - "script/gen_progress.py — the frozen sweep.json generator (WEB-01 data half)"
  - "the frozen sweep.json data contract, v1 (version/generated_at/sweeps[]; golden-pinned)"
  - "dnallm-mark/progress.html + js/progress.js + css/progress.css — the read-only progress mirror (WEB-01 page half)"
  - "DataAPI.loadProgress() (cache.progress slot) + the site-wide Progress NAV_LINKS entry"
  - "tests/tui/test_gen_progress.py (8 golden-JSON tests) + tests/js/progress-page.test.js (8 DOM-less tests)"
affects:
  - "12-04 (docs/multi-gpu.md documents gen_progress usage + the never worker-and-merged-roots rule)"
  - "12-05 (verification may regenerate sweep.json from a fixture root for the served-page check)"
  - "future regeneration: uv run --group tui --group dev python script/gen_progress.py [ROOT ...]"
tech-stack:
  added: []
  patterns:
    - "scanner-import serialization (dataclass fields verbatim, zero re-derivation — D-05 same-source, generator-side)"
    - "deterministic JSON discipline (sort_keys/indent 4/ensure_ascii False) + injected-clock stamp for byte-stable regeneration"
    - "event delegation on the persistent controls wrapper (change AND click both bubble — re-render-safe selects/tags)"
    - "structural negative pins in the DOM-less JS lane (zero-CDN, no timers, .gitkeep-only)"
key-files:
  created:
    - script/gen_progress.py
    - tests/tui/test_gen_progress.py
    - dnallm-mark/progress.html
    - dnallm-mark/js/progress.js
    - dnallm-mark/css/progress.css
    - dnallm-mark/data/progress/.gitkeep
    - tests/js/progress-page.test.js
  modified:
    - dnallm-mark/js/data.js
    - dnallm-mark/js/config.js
    - dnallm-mark/css/styles.css
decisions:
  - "skip predicate = the scanner yields nothing (no full_scan summary, or a non-finished root whose cells_view is empty) — derived purely from scanner outputs, no new walk"
  - "done/total/current/elapsed/eta serialize from stats() (the MON-02 canonical surface); state from full_scan classification — one consistent source per field group"
  - "data/progress/ landed .gitkeep ONLY (no fabricated sample JSON on the public site — every-number-is-real; the live page honestly shows the fetch-error empty state until the maintainer first regenerates)"
  - "running CLI sweeps (no manifest yet) honestly mirror total:null -> Unknown total + empty bar + ETA — (the generator threads no expected_total; only a manifest supplies one)"
  - "page controls row uses the .category-nav flex-wrap pattern with change+click delegation on the persistent wrapper; model/task truncation via layout-only inline styles + title full keys (the frozen CSS budget stays unspent)"
metrics:
  duration: "30m"
  completed: "2026-10-13"
estimate:
  tokens: 66000
actuals:
  tokens: 13790   # chars/4 over the realized diff (git diff 7b74ac2..HEAD)
  tasks: 2
  commits: 2      # MEASURED: git rev-list --count 7b74ac2..HEAD
plan_head_before: 7b74ac2e666bcec52d36e204497eb0a26f103ff4
plan_head_after: c9058b8353f24ae293ec11bd6db92b88c50ff490
status: complete
---

# Phase 12 Plan 02: Web Progress Mirror (Generator + Static Page) Summary

One-liner: `script/gen_progress.py` serializes the pure scanner's dataclasses verbatim into the frozen byte-stable `sweep.json` contract (argv-order multi-root, [Skip] tolerance, injected-clock stamp), and a zero-CDN static `progress.html` page renders it — summary card with the five-glyph state chips, sweep selector only when >1, Model/Task/status filters, curve-cell title pairs, and every designed honesty state — integrated site-wide with one-line NAV_LINKS/DataAPI/styles edits.

## What Was Built

### Task 1 — script/gen_progress.py (NEW, 250 lines) + tests/tui/test_gen_progress.py (8 tests)

- **Import shape (pinned):** dual sys.path bootstrap inlined from the tests/conftest.py contract (repo root for `tui`, `pipeline/` for the scanner's top-level siblings), then `from tui.services import sweep_monitor` — the textual-free chain (import-lock-tested), so the generator runs headless under `uv run --group tui --group dev`.
- **Zero derivation (D-05 same-source):** `full_scan` (classification) + `cells_view` (cell rows) + `stats` (done/total/current/elapsed/ETA) are the ONLY data sources; the generator serializes dataclass fields under their frozen names. `newest_mtime` deliberately dropped; `state_counts` derived from the same cells pass (exactly the five vocabulary states — unknown record statuses pass through verbatim in `cells[]` and are not counted in the chips).
- **main(argv=None, now=None):** positional ROOT nargs=* defaulting to `sweep_monitor.DEFAULT_OUTPUT_ROOTS`; `--output` default `dnallm-mark/data/progress/sweep.json`; argv-order one-entry-per-root emission, no dedupe; the never-worker-and-merged-roots double-count warning in the module docstring (runbook rule, 12-04).
- **Tolerance:** a root the scanner yields nothing for prints one `[Skip]` line and is absent (never a half-entry); a truncated run_record degrades via the scanner's tolerant readers — main exits 0.
- **Determinism:** `_write_json` discipline (sort_keys=True, indent=4, ensure_ascii=False) + `generated_at` from the injected clock (`%Y-%m-%dT%H:%M:%SZ`), falling back to the real clock — same roots + same pinned now = byte-identical output (test-pinned).
- **Tests:** golden exact-dict over three real fixture roots (finished with manifest+3 records / running worker root with a runs/-churn cell / artifacts_only with back-dated mtime), byte-stability, generated_at clock seam, argv-order worker roots (w1 before w0), DEFAULT_OUTPUT_ROOTS via monkeypatch, empty+missing-root [Skip], truncated-record degrade, curve fraction_states pairs. Clock determinism: pinned now = real+60s whole seconds (fresh fixtures inside the 600s grace, backdated ones outside) with record stamps derived from it — exact elapsed/ETA floats on any host date.

### Task 2 — the page set (progress.html/js/css + site one-liners + 8 JS tests)

- **progress.html:** the finetuning.html shell with the SheetJS CDN `<script>` line DELETED (this page loads zero CDN scripts — structurally pinned), title `DNALLM Mark | Progress`, module `./js/progress.js`; regions per the frozen IA: summary container → controls wrapper → leaderboard container → stamp container → standard footer.
- **js/progress.js (427 lines):** `PROGRESS` copy constants verbatim from the UI-SPEC copy table (English, D-10) + `CELL_STATES` map (the five TUI glyphs `✓ ⠋ ✗ ⊘ ◌` with css modifiers and legend words). `ProgressPage` follows the house controller pattern: navbar-first WR-03, single `this.state`, null-guarded containers, delegation on the persistent controls wrapper (change AND click both bubble; controls re-render safely on sweep change / status toggle with state-driven `selected`/`.active`).
  - Honesty rules web-side: null total → `1 / Unknown total` + width:0% bar; ETA pending → `Estimating…`, none → `—`, point/range per the D-17 grammar (`≈2.1h`, `≈{lo}–{hi}`); unknown record statuses render the raw string in the glyph slot; `generated_at` rendered VERBATIM in the footer stamp — never a client clock (a missing stamp renders nothing).
  - Sweep selector only when `sweeps.length > 1` (index-keyed, roots may repeat); Model/Task selects derived from cells with the verbatim `-- All Models --` / `-- All Tasks --` defaults; `.tag[data-status]` set-toggle + All-clears (the main.js data-filter grammar); cell table Model | Task | s{seed} columns (union over all cells, ascending), per-seed glyph spans, curve cells carry `frac_{name}: {state}` pairs in the title attribute, model/task cells truncate with full keys in titles; the three empty states (no-data / fetch-fail / no-match); zero timers (structurally pinned — deferred auto-refresh stays deferred).
- **Site one-liners:** `DataAPI.loadProgress()` (loadDataManifest shape, own `cache.progress` slot, throws on !ok); `NAV_LINKS` gains `{ name: 'Progress', url: './progress.html' }` appended last (navbar.js renders it on every page with zero navbar edits); `css/styles.css` `@import './progress.css';` appended last.
- **css/progress.css (the frozen CSS budget):** ONLY the summary stat-card refinement + the five `.cell-state--done/-running/-failed/-skipped/-queued` classes — every value a variables.css token, no hardcoded hex (structurally pinned); running uses `--color-info`, queued muted at 60% opacity.
- **data/progress/:** `.gitkeep` ONLY — no fabricated sample JSON (see Deviations).
- **tests/js/progress-page.test.js (8 tests, the two lane idioms):** loadProgress memoize-into-cache + throw-on-!ok; progress.html single-script/zero-CDN/title; NAV_LINKS appended-last; styles.css import order; the five state classes token-only; PROGRESS copy-table pins + no-timer negative; .gitkeep-only directory.

### Served-page check (SUMMARY evidence)

`python3 -m http.server` over the site with a locally generated sweep.json (fixture root `finetuned-mgpu-w0`: 1 completed + 1 running cell): `progress.html`, `data/progress/sweep.json`, `css/progress.css`, `js/progress.js` all HTTP 200; zero `cdn.jsdelivr` references in the page. A DOM-stub render smoke over the real imported module verified all 17 markup assertions (summary name/`1 / Unknown total`/`Elapsed 2.7h`/`ETA —`/chips/width:0%, sweep selector with 2 sweeps, `-- All Models --` defaults, status tags, legend, `s42/s43` columns, glyph spans, `frac_0.5: completed; frac_0.7: queued` title, full-key titles, verbatim stamp). The transient sweep.json was then deleted (`.gitkeep`-only re-verified by the JS lane).

Golden sweep.json over the three-root fixture (spot evidence, trimmed):

```json
{
    "generated_at": "2026-10-13T11:41:10Z",
    "sweeps": [
        {
            "root": "finetuned-mgpu-w0",
            "state": "running",
            "done": 1,
            "total": null,
            "elapsed_seconds": 9670.98,
            "current": { "model": "model-a", "task": "GUE__emp_H3", "seed": 42 },
            "eta": { "mode": "none", "point_seconds": null, "lo_seconds": null, "hi_seconds": null },
            "state_counts": { "completed": 1, "failed": 0, "queued": 0, "running": 1, "skipped": 0 },
            "cells": [ { "model": "model-a", "task": "GUE__emp_H3",
              "seeds": [ { "seed": 42, "state": "completed", "fraction_states": null },
                         { "seed": 43, "state": "running", "fraction_states": null } ] } ]
        }
    ],
    "version": 1
}
```

## Verification

- Module lanes during TDD: `pytest tests/tui/test_gen_progress.py -q` 8 passed (stable across 3 consecutive runs); ruff clean on both new Python files after two auto-fixes (import order, an unused noqa under ruff 0.16 defaults); `node --test tests/js/progress-page.test.js` 8 passed.
- **Full gate (SPEED DIRECTIVE — once green):** `make test` → **1531 passed** pytest (baseline 1523 + 8 new) + node lane **26/26** (existing 18 + 8 new); `make lint` → All checks passed (gen_progress.py joined via 12-01's PHASE12_MODULES existence guard — zero Makefile edits, as planned); `make typecheck` → All checks passed. Note: the FIRST full-gate run failed only `test_chain_is_deterministic_and_matches_committed` because the then-untracked `dnallm-mark/data/progress/` tripped its committed-data-tree porcelain guard — commit ordering, not a code fault; green immediately after the Task-2 commit.
- Hard constraints verified: `git diff --stat 7b74ac2..HEAD -- pipeline/ tui/strings.py pyproject.toml uv.lock Makefile` is EMPTY (frozen surfaces byte-untouched); the plan diff is exactly the 10 planned files (+1352/−2).

## TDD Cycle (both tasks tdd="true")

- **RED:** Task 1 — module absent (collection ModuleNotFoundError). Task 2 — 8/8 node tests failing (files absent, loadProgress missing).
- **GREEN:** Task 1 — three test-side argv-construction bugs fixed (multi-positional args into `main()`), one clock-arithmetic fix (pinned now must sit INSIDE the 600s stale grace for fresh fixtures: +60s, not +3600s); the generator itself landed unchanged from the behavior rows. Task 2 — one class-body syntax slip (stray comma) caught by `node --check` before the lane; no behavioral fixes needed.
- **REFACTOR:** none needed — both files were written to the row order.

## Deviations from Plan

None requiring Rules 1-4 (no bugs found, no blockers). Executor-owned details, recorded:

- **.gitkeep-only data dir** (the plan's own sanctioned choice, called out here as instructed): NO sample sweep.json is committed — a fabricated-progress sample on the public site would violate every-number-is-real; until the maintainer first regenerates, the live page honestly renders the fetch-error empty state (the designed state, UI-SPEC empty row 2).
- **Page region layout:** the shell adds two small containers (`.progress-summary-container`, `.progress-stamp-container`) so the DOM matches the UI-SPEC wireframe order (summary → selector/filters → table → stamp) while keeping every named bone (selector wrapper, leaderboard container, footer, module script). All other styling comes from existing classes (`.category-nav` controls row, `.model-selector` selects, `.leaderboard` cards, `.tag`, `.progress-bar`, `.empty-state`, `.grid` utilities).
- **Visual truncation of model/task cells** is delivered via layout-only inline styles + `title` full keys (the finetuning.html inline-style-with-tokens precedent) rather than new progress.css rules — the frozen CSS budget (five state classes + stat-card refinement only) stays unspent.
- **Full gate ran twice** (first red on commit ordering, then green) — documented above; no code changed between runs.

## Threat Mitigations Landed

| Threat | Mitigation | Proof |
|--------|------------|-------|
| T-12-02-01 untrusted JSON → innerHTML XSS | every dynamic string through `DataAPI.escapeHTML` (roots, models, tasks, statuses incl. unknown, fraction names, stamp) | progress.js render sites; the DOM-stub smoke over hostile-shaped data paths |
| T-12-02-02 fabricated progress values | null passthrough pinned by the golden test; footer stamp verbatim from JSON; no client clock; percent only when total known | `test_golden_contract_over_three_root_kinds`, `test_generated_at_follows_injected_clock`, render smoke (`1 / Unknown total`, `width: 0%`) |
| T-12-02-03 sweep.json size | accepted per OQ4 (no cap) | n/a |
| T-12-02-04 generator path escape | `--output` is an explicit operator Path; no traversal primitives | argparse surface |
| T-12-02-SC package installs | zero packages; stdlib + scanner + vanilla ES modules | empty pyproject/uv.lock diff |

## Known Stubs

None. No placeholder data, no unimplemented paths, no skipped tests, no unrun `<verify>` steps. (The empty `data/progress/` dir is the designed state, not a stub — see Deviations.)

## What 12-04 / 12-05 Can Now Assume

- **12-04** (docs/multi-gpu.md): cite `uv run --group tui --group dev python script/gen_progress.py <worker roots...> --output dnallm-mark/data/progress/sweep.json`; the runbook's never-both-worker-and-merged-roots rule is already stated verbatim in the generator docstring; the page's sweep selector is the multi-worker consumption story (one entry per worker root, argv order).
- **12-05** (verification): can regenerate a demo sweep.json from any fixture root via the same command; the JS lane pins the zero-CDN/no-timers/.gitkeep-only seams so verification only needs the served-page walk-through; both module suites (8+8) and the full gate (1531 + 26) are the regression net.
- The data contract is frozen and golden-pinned: any future field change bumps `version` and updates `tests/tui/test_gen_progress.py` + `12-UI-SPEC.md` together.

## Self-Check: PASSED

Files found: script/gen_progress.py, tests/tui/test_gen_progress.py, dnallm-mark/progress.html, dnallm-mark/js/progress.js, dnallm-mark/css/progress.css, dnallm-mark/data/progress/.gitkeep, tests/js/progress-page.test.js (+ the three modified one-liner files). Commits 3db47ae (Task 1) and 4096bb3 (Task 2) are ancestors of HEAD. Measured commit count 2 matches the ledger (7b74ac2..HEAD).
