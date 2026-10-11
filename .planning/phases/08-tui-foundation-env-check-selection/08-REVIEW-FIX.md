---
phase: 08-tui-foundation-env-check-selection
fixed_at: 2026-10-11T17:39:41Z
review_path: .planning/phases/08-tui-foundation-env-check-selection/08-REVIEW.md
iteration: 2
findings_in_scope: 9
fixed: 9
skipped: 0
status: all_fixed
---

# Phase 8 (TUI foundation — env check + selection): Code Review Fix Report

**Fixed at:** 2026-10-11T17:39:41Z
**Source review:** .planning/phases/08-tui-foundation-env-check-selection/08-REVIEW.md
**Iteration:** 2 (cumulative — iteration 1's 8 fixes + iteration 2's WR-06)

**Summary:**
- Findings in scope (both iterations): 9 (3 CRITICAL + 6 WARNING; the 10
  Info findings IN-01..IN-10 are out of scope per the loop contract)
- Fixed: 9
- Skipped: 0

**Iteration-2 context:** the re-review (2026-10-11T17:24:43Z) confirmed
all 8 iteration-1 fixes hold and reported exactly ONE new Warning —
WR-06, a defect the WR-04 fix itself introduced: the async
`PresetMenuLoaded` push can open the `PresetModal` over the min-size
guard, and growing back then strands the guard at full size (the WR-01
consequence class via a path WR-01's fix cannot see). Fixed this pass,
reproduce-verified first — the same discipline as iteration 1.

## Fixed Issues — Iteration 2

### WR-06: The WR-04 async preset-modal push can open over the min-size guard — console permanently stranded (the WR-01 defect class via a new path)

**Files modified:** `tui/app.py`, `tui/screens/selection.py`,
`tests/tui/test_pilot_selection.py`
**Commit:** 3cc9fed
**Applied fix:** Reproduced first, two ways, both before touching the
source: (1) a standalone headless Pilot repro walking the review's exact
5-step sequence against the real `DnallmMarkTui` with a gated
`preset_menu` fake — p at 120x40 → shrink to 60x20 (guard in) → read
completes (stack `[env, selection, MinSizeScreen, PresetModal]`, modal
OVER the guard) → grow to 120x40 (`_min_size_screen = None`, no pop —
the guard is not the top screen) → dismiss (guard active at full size,
`_min_size_screen` None — permanent stranding, only `q` escapes); and
(2) the new in-suite regression test failing at exactly the named
defect (`isinstance(PresetModal(), MinSizeScreen)` is False — the modal
is the active screen while the guard should be). Then:

- `tui/app.py`: exposed the guard state as a read-only
  `below_minimum_grid` property on `DnallmMarkTui` (True while the
  min-size guard is up), and `action_help` now checks the property
  instead of the private `_min_size_screen` attribute (the review's
  suggested route — one public guard-state seam for every chrome push).
- `tui/screens/selection.py`:
  `on_selection_screen_preset_menu_loaded` drops the message while
  `self.app.below_minimum_grid` — the async push never lands over the
  guard, so the WR-01 restore pop always finds the guard as the top
  screen when the terminal grows back. The operator re-presses `p`
  after growing back, the same degraded behavior `action_help` already
  has. The screen reaches the app's own API type-safely via textual's
  own `getters.app(DnallmMarkTui)` descriptor declared under
  `TYPE_CHECKING` (the `MessagePump.app` pattern — no runtime import of
  the composition root, which would be circular; `ty` passes). The
  module's D-03 contract bullet documents the new rule: a worker result
  arriving while the guard is up is dropped.
- `tests/tui/test_pilot_selection.py`: new Pilot regression test
  `test_preset_modal_never_opens_over_the_min_size_guard` pins the full
  sequence — p at full size (worker in flight, no modal) → shrink
  (guard in) → read completes while the guard is up (message dropped:
  guard still the active screen, no `PresetModal` anywhere in the
  stack) → grow (the selection screen restores — never the stranded
  guard — and `_min_size_screen` is None) → `p` works again once above
  the minimum (the degraded-behavior recovery).

Post-fix the standalone repro shows the clean behavior end to end
(message dropped under the guard; guard pops on grow; selection screen
active; no stranding possible), and the regression test passes.

**Verification (iteration-2 gates, run in the isolated worktree
`.claude/worktrees/rf-08-2705702-1791739882` on branch
`gsd-reviewfix/08-2705702`, using the main checkout's venv via
`UV_PROJECT_ENVIRONMENT` — the worktree has no venv of its own; the
exact commit fast-forwarded to `autorun` is the one checked):**

- `make lint` (ruff, the full Makefile file list incl. all of `tui/`):
  **All checks passed**
- `make typecheck` (`ty check`): **All checks passed**
- `make test` (full pytest incl. the slow lane): **738 passed** — was
  737 at the re-review HEAD `d2ce620`; the +1 is the new WR-06
  regression test. JS lane (`node --test tests/js/*.test.js`):
  **18 pass, fail 0**
- `tests/tui` + `tests/test_env_smoke_bytes.py` lane: **180 passed** —
  was 179 at the re-review HEAD (same +1)

**Load-bearing invariants re-verified intact (iteration 2):**

- The change touches exactly `tui/app.py`,
  `tui/screens/selection.py`, `tests/tui/test_pilot_selection.py` —
  `tui/services/` untouched, zero textual imports there (grep clean;
  the import-lock test green in the suite).
- `pipeline/env_smoke.py`, `schemas/run_template.json`,
  `.github/workflows/ci.yml`, `pyproject.toml`, `uv.lock` — all
  byte-untouched by this change (`git diff --name-only` over them is
  empty).
- Chinese operator copy only in `tui/strings.py` — the fix adds no
  operator-facing copy at all (no CJK characters in any added line; the
  only additions are English comments/docstrings and code).

## Fixed Issues — Iteration 1

(re-verified holding by the iteration-2 re-review at HEAD `d2ce620`;
original iteration-1 report content below)

**Fix discipline:** All three criticals were reproduce-verified per the
review's headless Pilot notes BEFORE their fixes (each repro failed with
the exact defect the review named), then re-verified after; the warning
fixes carry the same pre-fail/post-pass discipline except WR-04 (see its
entry). Every fix is one atomic commit in `fix(08-NN)` form.

**Verification (iteration-1 gates, run in the isolated worktree
`.claude/worktrees/rf-08-2652307-1791736279` on branch
`gsd-reviewfix/08-2652307`, using the main checkout's venv interpreter —
the worktree has no venv of its own; the exact commits fast-forwarded to
`autorun` were the ones checked):**

- `make lint` scope (full Makefile file list, ruff): **All checks passed**
- `make typecheck` (`ty check`, resolved against the venv interpreter):
  **All checks passed**
- `make test` (full pytest incl. the slow lane): **737 passed**; JS lane
  (`node --test tests/js/*.test.js`): **fail 0**

**Load-bearing invariants re-verified intact (iteration 1):**

- `tui/services/**` zero textual imports — `tests/tui/test_import_lock.py`
  green; grep confirms the only "textual" occurrences in services are the
  invariant's own docstring mentions.
- `pipeline/env_smoke.py` and the PASS:/FAIL: byte contract — untouched
  (`git diff 098fc48..HEAD -- pipeline/env_smoke.py` is empty; the golden
  byte suite passed).
- `schemas/run_template.json` FROZEN — untouched; WR-03's grammar fix went
  into `tui/services/selection.py`'s `derive_presets` as required.
- `.github/workflows/ci.yml` byte-untouched; `pyproject.toml` untouched
  (`[tui]` group membership unchanged).
- Chinese operator copy only in `tui/strings.py` — the two new
  WR-04/CR-02 copy constants landed there; the per-module i18n gates
  passed.

### CR-01: Pressing `?` on the selection screen crashes the console (Rich MarkupError from the `[/]` keycap)

**Files modified:** `tui/app.py`, `tests/tui/test_pilot_selection.py`
**Commit:** 0b5405e
**Applied fix:** Reproduced first (new Pilot test opening `?` on the
selection screen failed with `MarkupError: auto closing tag ('[/]') has
nothing to close`). Help rows now render as `rich.text.Text` content
objects (never markup-parsed), and `_binding_row` filters `show=False`
and description-less bindings — the selection screen's hidden
`enter`/`escape` rows never list and no `None` label can render. The
existing env-screen help test stayed green (its binding set is
unaffected).

### CR-02: Template export / preset save to an unwritable or invalid path crashes the console (unhandled OSError)

**Files modified:** `tui/strings.py`, `tui/screens/selection.py`,
`tests/tui/test_pilot_selection.py`
**Commit:** 7956c2d
**Applied fix:** Reproduced first (a marked selection exporting to
`/dev/null/x.json` failed with the unhandled `FileExistsError` killing
the app; the save path reproduced with `PermissionError`).
`_submit_export`/`_submit_tiers` now catch `OSError` alongside
`ValueError` and surface it as in-modal problems (new
`SEL_TEMPLATE_WRITE_FAILED`), and `_do_save` degrades to a warning toast
(new `SEL_PRESET_SAVE_FAILED`). A sync backend test pins the real
export failure mode as `OSError` (the exact class the screen catches)
against `/dev/null/x.json`.

### CR-03: Matrix screen crashes on mount (CellDoesNotExist) in the registry-degraded state it is supposed to survive

**Files modified:** `tui/screens/matrix.py`, `tui/screens/selection.py`,
`tests/tui/test_pilot_matrix.py`
**Commit:** 76aa1cd
**Applied fix:** Reproduced first (a models-registry-degraded snapshot
pushed via `v` failed with `CellDoesNotExist: No cell exists at
Coordinate(row=0, column=1)` on mount). The models-load-failure state now
composes the documented `SEL_REGISTRY_LOAD_FAILED` copy instead of the
grid (the n_audit-absent pattern); `_current_task_key` validates the
coordinate before conversion (`is_valid_coordinate` —
`coordinate_to_cell_key` raises for invalid coordinates, it never
returns None); the cursor is only set when model rows exist; and
`action_show_key` is a no-op on the empty states (adjacent hardening:
the enter path previously queried the absent `#matrix-table` on the
n_audit-absent empty state — the same crash family, and the new
degraded state would have carried it too; the new test pins enter as a
no-op). The dead `cell_key is None` guards in the selection screen's
`action_toggle_mark`/`action_show_detail` are replaced with the same
`is_valid_coordinate` check.

### WR-01: Min-size guard pops the wrong screen — console permanently stuck on MinSizeScreen at full size

**Files modified:** `tui/app.py`, `tests/tui/test_pilot_env_check.py`
**Commit:** 9cc1879
**Applied fix:** Reproduced first (shrink 60x20 → `?` → grow 120x40
left `MinSizeScreen` active at full size — the pre-fix test failed
because `?` pushed HelpModal over the guard). `action_help` is now
suppressed while the guard is up (no chrome over it), and the restore
branch pops only when the guard IS the active screen — so a modal
beneath the guard (a drill-down opened before the shrink) still survives
the round trip. The new test also pins that `?` works again once above
the minimum.

### WR-02: Env-check refresh race — a cancelled worker's last CheckItemDone can overwrite the fresh run's result

**Files modified:** `tui/screens/env_check.py`,
`tests/tui/test_pilot_env_check.py`
**Commit:** 932703f
**Applied fix:** Reproduced deterministically first (a gated stale run
released after the fresh run completed flipped the fresh pass row to the
stale fail — `['✗', …] != ['✓', …]`). All three worker messages
(`CheckItemChecking`/`CheckItemDone`/`CheckRunComplete`) now carry the
run id captured at worker start; every handler drops messages whose id
no longer matches `self._run_id` (incremented on each refresh); and a
final cancellation poll before `persist` keeps a cancelled run from
clobbering the fresh run's persisted state (the same race on the state
file). The repro test pins the full interleave: fresh run completes →
stale message lands last → row, summary, and last-check line all
intact, exactly one persist.

### WR-03: Tier-grammar mismatch — derive_presets rejects task-omitting tier-1 specs that run_sweep and the templates service both accept

**Files modified:** `tui/services/selection.py`,
`tests/tui/test_services_selection.py`
**Commit:** 7a4ca2b
**Applied fix:** Reproduced first (a task-omitting tier-1 pair made the
whole priorities file "damaged" — empty presets + load error). The
tier-1 validation now accepts `task is None` (the run_sweep
`--priority-file` grammar's model-every-task spec, the same shape
`tiers_to_template` accepts) and the derivation contributes the model
only; a non-string `task` remains a damaged-file problem (the damaged
list gained explicit non-string model/task cases). The schema
(`schemas/run_template.json`) is untouched — this is the priorities-file
grammar, not the frozen template contract. The committed-priorities
derivation test still passes unchanged.

### WR-04: preset_menu runs two full registry reads + the priorities/customs files synchronously on the event loop

**Files modified:** `tui/screens/selection.py`,
`tests/tui/test_pilot_selection.py`, `tests/tui/test_pilot_matrix.py`
**Commit:** 2b5f27a
**Applied fix:** `action_apply_preset` called
`self._service.preset_menu()` directly in the key handler — against the
module's own D-03 worker contract. The menu now loads in an exclusive
`@work(exclusive=True, thread=True)` worker (the same default-group
pattern as `_load_data`, mutually exclusive so reads never overlap) and
crosses to the loop via a new `PresetMenuLoaded` message; the handler
pushes `PresetModal`. A gated Pilot test pins the T-08-07 property: the
`m` table toggle keeps processing while the menu read blocks (the event
loop is free), and the modal opens only after the read completes. The
four existing `p`-press test sites gained the standard
`app.workers.wait_for_complete()` await. Verification note: unlike the
other findings this fix was verified post-fix behaviorally (the gated
responsiveness test + every preset flow green), not via a pre-fix
failing run — the pre-fix defect is the synchronous call itself, which
the review confirmed. Same-class adjacent reads named by the review
(`custom_names()` in the save flow, the modal submit import/export file
I/O) remain on the event loop — single-file reads, deliberately left
out of this surgical fix; flagging them for a future pass (recorded by
the iteration-2 re-review as IN-09).

### WR-05: Machine-dependent tests — four registries tests and the 62/50 backend assertions omit the custom-overlay pin the module's own docstring mandates

**Files modified:** `tests/tui/test_services_registries.py`,
`tests/tui/test_pilot_selection.py`
**Commit:** d2ce620
**Applied fix:** The module's own three-line pin
(`monkeypatch.setenv("DNALLMMARK_CUSTOM_REGISTRY_DIR", <fresh empty tmp
dir>)`) now covers the five named tests:
`test_model_entries_carry_raw_values_with_empty_string_absents`,
`test_dataset_entries_carry_raw_values`,
`test_size_m_is_the_numeric_card_field_as_float`,
`test_every_registry_dataset_key_maps_to_a_definite_presence`, and the
Pilot `test_backend_loads_the_committed_registries_and_presence`. The
defect and the fix were both demonstrated empirically: with a live
one-entry custom overlay, the unpinned merged counts are 63/51 and the
definite-presence statuses include `unknown` (the old assertion fails);
with the same overlay live, the pinned tests pass at 62/50. One
adjacent same-class assertion the review's list did not enumerate was
pinned in the same commit: `test_backend_registry_failure_degrades_to_
the_error_state`'s healthy-side `== 50` (directly adjacent, same
defect class — left unpinned it would fail on the same machines).

---

_Fixed: 2026-10-11T17:39:41Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 2_
