# Phase 08 Deferred Items (out-of-scope discoveries)

Log for issues discovered during execution that are pre-existing or unrelated
to the current plan's changes — recorded, not fixed (executor scope boundary).

| Date | Found in | Item | Status |
|------|----------|------|--------|
| 2026-10-11 | 08-02 Task 2 | `uv run --group gpu python -c "pass"` (and any lane including the gpu group) uninstalls+reinstalls `nvidia-cusparselt-cu13 0.8.0` on EVERY invocation, even back-to-back identical commands — a uv 0.13.0 inexact-sync re-link of the large cu130-index wheel. Pre-existing gpu-lane behavior, unrelated to the [tui] group (reproduced with `--group gpu` alone, no tui involved; the 08-02 uv.lock diff touched no torch/nvidia entries). Cosmetic (venv churn, ~2ms), no functional impact observed. Candidate for a uv upgrade check later. | open |
