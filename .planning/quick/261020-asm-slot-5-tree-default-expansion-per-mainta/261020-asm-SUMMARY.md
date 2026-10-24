---
phase: quick-261020-asm
plan: 01
subsystem: tui-monitor
tags: [slot-5, tree-state, variant-E, expansion-default, pilot, pty]
requires:
  - "261019-pe0 (the tree state + the locked nav contract)"
  - "261018-rze (the cadence gate law)"
  - "261019-o8e (the filtered row map the tree derives from)"
provides:
  - "TREE-variant-E-all-expanded-entry: every model node expanded on mount, structural rebuild, and mid-session cards — named default (_TREE_DEFAULT_EXPANDED) + pinned in both lanes"
  - "TREE-collapse-survives-cadence: operator collapse choices survive 2s steady ticks (pilot-pinned)"
  - "PTY-both-models-task-rows-visible: the maintainer's exact observation pinned end-to-end through the real console"
affects: []
tech-stack:
  added: []
  patterns:
    - "guide-glyph raw-byte markers (├── / └── render inside single SGR runs, task-child rows only) — pexpect pins in paint order"
key-files:
  created: []
  modified:
    - tui/screens/monitor.py
    - tests/tui/test_pilot_monitor.py
    - tests/tui/test_pty_driver.py
decisions:
  - "The variant-E default was ALREADY the on-HEAD behavior (probe-pinned pilot + real pty); the landed change names it (_TREE_DEFAULT_EXPANDED) instead of re-writing behavior — the pins are the acceptance shape"
  - "Operator collapse persistence across structural rebuilds (the _tree_expand cache) KEPT over the ruling's acceptable full-re-expand simplification — strictly better, zero extra code"
metrics:
  duration: "~50 min"
  completed: "2026-10-20"
actuals:
  tokens: 9000
  tasks: 3
  commits: 2
status: complete
---

# Quick 261020-asm: Slot-5 Tree Default Expansion (Variant E) Summary

The maintainer's tree-variant E ruling made explicit and pinned: the slot-5 tree enters with every MODEL node expanded (mount, structural rebuild, mid-session cards), the locked pe0 nav contract stays byte-green, and operator collapse choices survive the 2s cadence — proven in both the pilot and the real-pty lane, goldens untouched.

## What Landed

| Commit  | Change |
| ------- | ------ |
| f3716e5 | `tui/screens/monitor.py` — `_TREE_DEFAULT_EXPANDED = True` names the ruling's default at the ONE build site (`_build_card_tree`, shared by the construction and rebuild legs); the 261020-asm ruling paragraph joins the module contract block; zero behavior change |
| 4064b38 | Pilot + pty pins — `test_tree_navigation_contract` entry assertions (every model `is_expanded`, 6 visible nodes) and the `*`-collapse-then-frontier-tick survival leg; `test_monitor_tree_state_navigates_and_drills` gains the ordered guide-glyph sequence proving BOTH models' task rows visible after [w] |

## The Planning Finding (recorded deviation from the diagnosis)

The task brief diagnosed "pe0's RunCardTree builds with auto_expand=False and nothing expands model nodes on mount". Probing showed the diagnosis does not hold against HEAD:

- `_build_card_tree` has carried `expand=expanded.get(model, True)` since the pe0 commit itself (e9027ee) — a fresh `_tree_expand` cache is empty, so every model takes the expanded default.
- A Pilot probe (fake service, model-a/model-b card): both models `is_expanded` at entry, 6 visible nodes, expansion unchanged after a real frontier tick.
- A real-pty probe over the enriched two-model fixture: the rendered frame shows `▼ plant-dnabert-6mer` with BOTH task rows and `▼ plant-dnamamba-6mer` with its task row — the ruled behavior, already rendering.
- The real `finetuned-smoke` root today is dead (Running (0), History (3) — no live process), so the maintainer's exact live frame cannot be re-observed; their morning session most plausibly showed the o8e live-pair-filtered truth (one live model's planned tasks), which is designed behavior, not an expansion reset.

Execution therefore made the default EXPLICIT and load-bearing (named constant + ruling in the contract block) and pinned the ruled behavior in both lanes — including a mutation check: flipping `_TREE_DEFAULT_EXPANDED` to False fails BOTH new pins (pilot entry assertion + pty guide-glyph sequence), so any future regression that reintroduces a collapsed entry trips the suite.

## Pin Design Notes

- **Pilot entry pin**: right after the entering-tree cursor pin — every `tree.root.children` node `is_expanded` and `_visible_tree_nodes(tree)` carries 6 keys (2 model headers + 4 task rows).
- **Cadence-survival pin**: inside the existing `*` collapse-all window — `screen._tick_frontier()` + `_settle`, then still all-collapsed, no task node visible. Observable-contract pin (mechanism zero-write is separately pinned by the rze/o8e tests).
- **Pty pin**: the guide forms `├── ` / `└── ` render inside single SGR runs and exist ONLY as task-child rows (model headers carry `▼ `/`▶ `), so the ordered paint sequence `0/2 → ├── → GUE__emp_H3 → └── → GUE__virus_species_4 → 0/1 → └── → GUE__emp_H3` proves both models expanded with children rendered; pexpect consumes in stream order, so the expects sit in paint order between the two existing model-marker expects. Downstream `*`/enter/click/down/enter legs byte-untouched.

## Verification

- `tests/tui/test_pilot_monitor.py::test_tree_navigation_contract` — 1 passed
- `tests/tui/test_pty_driver.py::test_monitor_tree_state_navigates_and_drills` — 1 passed (11.9s, within the ~15s member budget)
- Full `pytest tests/tui -q` — **1286 passed** (0:06:18)
- `ruff check` on all three touched files — clean; full `ty check` — clean
- Mutation check — `_TREE_DEFAULT_EXPANDED = False` fails both pins (2 failed), reverted, re-verified green

## Goldens

NO delta. `tests/tui/test_snapshots.py` 11 passed; sha256 byte-identical to the pre-change baseline:
- `tests/tui/__snapshots__/monitor_running.svg` — `d468d33791cb75877b6232c3bdd461fb832aacb76f513dd36e2c7e5f56017289`
- `tests/tui/__snapshots__/monitor_empty.svg` — `258ab609191b89ff6ffae7cbca91537bbb69a2445391c812dc5e845344e2d000`

No regeneration performed or needed.

## Deviations from Plan

None — the plan was written after the probes and executed exactly (the planning finding itself is documented above and in the PLAN.md truths).

## Standing Rules

- Atomic plain commits, NO trailers — both commits on `autorun`.
- `.venv/bin/python` only; zero GPU; zh untouched (zero strings.py changes, zero new operator copy); the maintainer's live sweep read-only (planning probes read `finetuned-smoke` through the monitor scan path only).
- `.planning/` NOT committed — PLAN.md/SUMMARY.md stay untracked for the orchestrator.

## Self-Check: PASSED

- `tui/screens/monitor.py`, `tests/tui/test_pilot_monitor.py`, `tests/tui/test_pty_driver.py` modified and committed (f3716e5, 4064b38 — both ancestors of HEAD).
- `.planning/quick/261020-asm-slot-5-tree-default-expansion-per-mainta/261020-asm-PLAN.md` present on disk (uncommitted by design).
