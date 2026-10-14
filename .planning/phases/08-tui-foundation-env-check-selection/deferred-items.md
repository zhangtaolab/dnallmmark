# Phase 08 Deferred Items (out-of-scope discoveries)

Log for issues discovered during execution that are pre-existing or unrelated
to the current plan's changes — recorded, not fixed (executor scope boundary).

| Date | Found in | Item | Status |
|------|----------|------|--------|
| 2026-10-11 | 08-02 Task 2 | `uv run --group gpu python -c "pass"` (and any lane including the gpu group) uninstalls+reinstalls `nvidia-cusparselt-cu13 0.8.0` on EVERY invocation, even back-to-back identical commands — a uv 0.13.0 inexact-sync re-link of the large cu130-index wheel. Pre-existing gpu-lane behavior, unrelated to the [tui] group (reproduced with `--group gpu` alone, no tui involved; the 08-02 uv.lock diff touched no torch/nvidia entries). Cosmetic (venv churn, ~2ms), no functional impact observed. Candidate for a uv upgrade check later. | open |
| 2026-10-14 | 08-08 Task 1 | Screen-side DIRECT card reads over the projected entries remain unguarded on user-action paths outside the plan's named seams: the wizard modal's observed vocabularies (`tui/screens/selection.py` `_build_wizard_modal`, `entry["card"].get("species")`/`.get(Tokenizer)`), `_manual_landing_path`'s `(entry.get("card") or {}).get("Model_path")` (a truthy non-dict card defeats the `or {}`), and `RowDetailModal`'s `self._card.items()` (enter on a degraded row). All are reached only by explicit user action ON a non-dict-card row (w/d/enter), not by the load/projection path the plan's truths and regression tests cover; Task 3's never-exit floor covers the worker paths. Same T-08-09 family — record for a later hardening pass. | open |
