---
phase: quick-261020-asm
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - tui/screens/monitor.py
  - tests/tui/test_pilot_monitor.py
  - tests/tui/test_pty_driver.py
autonomous: true
requirements: ["TREE-variant-E-all-expanded-entry", "TREE-nav-contract-unchanged", "TREE-collapse-survives-cadence", "PTY-both-models-task-rows-visible", "GOLDENS-no-delta-verify"]
user_setup: []

estimate:
  tokens: 24000
  raw_tokens: 17000
  tasks: 3
  confidence: high

must_haves:
  truths:
    - "The maintainer's ruling (2026-10-20 07:12, tree-variant E): the slot-5 tree ENTERS with every MODEL node expanded — every task row visible on mount, on a structural (gate-law) rebuild, and on every card that appears mid-session. PLANNING FINDING (probe-pinned, pilot + real-pty over the enriched two-model fixture): pe0's build path ALREADY carries this default — `_build_card_tree` adds every model node with `expand=expanded.get(model, True)` and a fresh `_tree_expand` cache is empty, so the ruled behavior holds on HEAD in both lanes (the pty render shows `▼ plant-dnabert-6mer` with both task rows and `▼ plant-dnamamba-6mer` with its task row). The defect the maintainer reported ('只显示了一个模型的两个任务') does not reproduce against HEAD's build path; the deliverable is therefore (a) making the variant-E default EXPLICIT and load-bearing in the code (a named constant + the ruling recorded in the module contract, so the default is deliberate rather than incidental) and (b) pinning it in both lanes so a future regression trips — the ruling's acceptance shape, not a behavior re-write"
    - "The locked pe0 nav contract is UNCHANGED and must stay green: ← collapse-or-parent, → expand-or-into, Enter model=toggle/task=drill, `*` expand-all/collapse-all toggle, ↑↓ clamped (no card crossing), Tab switches tabs, click=select-only. `*` from the all-open entry collapses EVERYTHING (the toggle reads the live tree state, never the entry default) and the collapsed-away cursor salvages onto its model node — already pinned by test_tree_navigation_contract; this plan adds ONLY entry-state assertions ahead of the existing key-driven legs and a cadence check inside the existing `*` window, never a re-design"
    - "Operator collapse choices SURVIVE the 2s cadence steady ticks: the gate law already guarantees a steady tick performs zero tree writes (the per-card tree structure signature gates the rebuild; label-only changes take the `set_label` in-place pass), and the screen-side `_tree_expand` cache preserves operator choices across genuine structural rebuilds — full re-expand on rebuild is ACCEPTABLE per the ruling's keep-it-simple clause but the existing cache is strictly better, so it stays. The cadence-survival leg is pinned: `*` collapse-all, then a real `screen._tick_frontier()` settle, then still all-collapsed with no task node visible"
    - "The pty lane pins the maintainer's EXACT observation: after [w] to tree, BOTH models' task rows are visible in the pane. Marker design (raw-byte probe-pinned): the tree guide forms render inside single SGR runs — `├── ` and `└── ` exist only as TASK-child rows (model rows carry `▼ `/`▶ `), and the fixture's task keys are ordered GUE__emp_H3 < GUE__virus_species_4 with the residue model's single task the shared GUE__emp_H3 — so the ordered paint sequence 0/2 → `├── ` → GUE__emp_H3 → `└── ` → GUE__virus_species_4 → 0/1 → `└── ` → GUE__emp_H3 proves every model node expanded with its children rendered (a collapsed entry renders model headers only and the sequence times out)"
    - "Goldens: NO delta expected (monitor_running / monitor_empty render matrix-mode states over static fakes — the tree never enters a golden); verified by sha256 before/after; NO regeneration"
    - "zh untouched: zero strings.py changes, zero new operator copy — the ruling changes rendering defaults, not copy"
    - "Standing rules hold: atomic plain commits with NO trailers on autorun, `.venv/bin/python` only (never uv), zero GPU, the maintainer's live sweep (finetuned-smoke) read-only (the planning probes read it via the monitor scan path only), full `pytest tests/tui -q` green, ruff + ty clean"
  artifacts:
    - "tui/screens/monitor.py: the 261020-asm ruling paragraph in the module contract block (after the pe0 paragraph) + the `_TREE_DEFAULT_EXPANDED = True` constant beside the other tree-state constants, used as the `expand=` default in `_build_card_tree` (zero behavior change — the literal True becomes the named contract) + the `_build_card_tree` docstring line citing the ruling"
    - "tests/tui/test_pilot_monitor.py: test_tree_navigation_contract EXTENDED at two points only — (1) at entry, right after the entering-tree cursor pin: every `tree.root.children` node `is_expanded` and `_visible_tree_nodes(tree) == 6` (both models + all four task nodes — the multi-model default-expanded pin); (2) inside the existing `*` collapse-all window, before the expand-all tail: one real `screen._tick_frontier()` + `_settle` then still all-collapsed and no task node visible (the cadence-survival pin)"
    - "tests/tui/test_pty_driver.py: test_monitor_tree_state_navigates_and_drills EXTENDED between the two existing model-node marker expects — the ordered task-row sequence (`├── ` / task key / `└── ` / task key / `0/1` / `└── ` / `GUE__emp_H3`) with 261020-asm comments; the downstream `*`/enter/click/down/enter legs byte-untouched (the added expects consume only already-arriving frame bytes, in paint order)"
  key_links:
    - "default site <- tui/screens/monitor.py `_build_card_tree` (:3436 `expand=expanded.get(model, True)`) — THE one build path shared by the pre-mount construction leg (`_card_widget`) and the in-place structural rebuild leg (`_render_card_tree`), so the named default covers mount, rebuild, and mid-session new cards in one site; `_tree_expand` (the operator-choice cache, synced by the NodeExpanded/NodeCollapsed handlers) holds only models the operator touched — every other model takes the default"
    - "gate law <- the per-card tree structure signature (`_tree_sigs`) + the cards signature's mode leg keep steady ticks at zero tree writes, so operator expansion state survives the cadence by construction; `on_mount` clears the caches (the remount resets to all-expanded) — unchanged"
    - "pty marker law <- pexpect consumes the stream in order, so the task-row expects must sit BETWEEN the existing `_TREE_LIVE_MODEL_MARKER` (row 6's `0/2`) and `_TREE_RESIDUE_MARKER` (row 9's `0/1`) expects exactly in paint order; the trailing 1.0s absence drain and every downstream leg keep their current byte windows"

tasks:
  - id: "1"
    title: "monitor.py — the variant-E default made explicit"
    type: auto
    tdd: false
    files: ["tui/screens/monitor.py"]
    steps:
      - "Add the 261020-asm ruling paragraph to the module contract block (after the pe0 paragraph): the tree enters all-expanded on mount/rebuild/new cards, the nav contract unchanged, `*` from all-open collapses, collapse choices survive the cadence, operator choices persist across structural rebuilds via the existing cache"
      - "Add `_TREE_DEFAULT_EXPANDED = True` with a ruling-citing comment beside the tree-state constants; use it in `_build_card_tree`'s `expand=expanded.get(model, _TREE_DEFAULT_EXPANDED)`; cite the ruling in the `_build_card_tree` docstring"
    verification:
      - "`.venv/bin/python -m pytest tests/tui/test_pilot_monitor.py -q` green (no behavior change)"
      - "`.venv/bin/ruff check tui/screens/monitor.py` + `.venv/bin/ty check tui/screens/monitor.py` clean"
    done: "the default is a named, documented contract; zero behavior delta"

  - id: "2"
    title: "pilot pins — multi-model entry expansion + cadence survival"
    type: auto
    tdd: false
    files: ["tests/tui/test_pilot_monitor.py"]
    steps:
      - "In test_tree_navigation_contract, after the entering-tree cursor-pin assert: assert every model node `is_expanded` and the visible node count is 6 (both models' task children visible — the maintainer observation, pilot lane)"
      - "Inside the `*` collapse-all window (after the collapse asserts, before the expand-all tail): `screen._tick_frontier()` + `await _settle(pilot, app)`, then re-assert all model nodes collapsed and no task node visible"
    verification:
      - "`.venv/bin/python -m pytest tests/tui/test_pilot_monitor.py::test_tree_navigation_contract -q` green"
    done: "the two ruled behaviors are pinned in the pilot lane; existing legs untouched"

  - id: "3"
    title: "pty pin — both models' task rows visible after [w]"
    type: auto
    tdd: false
    files: ["tests/tui/test_pty_driver.py"]
    steps:
      - "In test_monitor_tree_state_navigates_and_drills, between the two model-node marker expects, insert the ordered task-row marker sequence (├── / GUE__emp_H3 / └── / GUE__virus_species_4 / 0/1 / └── / GUE__emp_H3) with 261020-asm comments; downstream legs untouched"
    verification:
      - "`.venv/bin/python -m pytest tests/tui/test_pty_driver.py::test_monitor_tree_state_navigates_and_drills -q` green (budget ~15s member)"
      - "Goldens: `.venv/bin/python -m pytest tests/tui/test_snapshots.py -q` green + sha256 of monitor_running.svg / monitor_empty.svg unchanged from baseline"
    done: "the maintainer's exact observation is pinned end-to-end through the real console"

  - id: "4"
    title: "full gates + goldens + commits"
    type: auto
    tdd: false
    files: []
    steps:
      - "Full `.venv/bin/python -m pytest tests/tui -q` green; `.venv/bin/ruff check tests/tui/test_pilot_monitor.py tests/tui/test_pty_driver.py tui/screens/monitor.py` clean; `.venv/bin/ty check` clean (or the touched-files scope the Makefile uses)"
      - "Verify golden shas unchanged; NO regeneration"
      - "Two atomic plain commits on autorun (no trailers): feat(quick-261020-asm) monitor.py, test(quick-261020-asm) the pins"
    verification:
      - "git log shows the two commits; working tree clean of code changes"
    done: "all gates green, commits landed"

verification:
  overall: "The ruled variant-E behavior is explicit in code and pinned in both lanes; the locked nav contract stays green; goldens byte-identical; zh untouched; zero GPU"
  success_criteria:
    - "pytest tests/tui -q fully green"
    - "ruff + ty clean on the touched files"
    - "monitor_running.svg / monitor_empty.svg sha256 unchanged (d468d337… / 258ab609…)"
    - "Two atomic commits on autorun, no trailers, no .planning files committed"

output_spec:
  summary_path: ".planning/quick/261020-asm-slot-5-tree-default-expansion-per-mainta/261020-asm-SUMMARY.md"
  summary_requirements:
    - "commits + hashes"
    - "test tails: pilot tree member, pty tree member, full tests/tui"
    - "the planning finding (behavior already held on HEAD; probes cited) as a recorded deviation-from-diagnosis note"
    - "golden sha status"
