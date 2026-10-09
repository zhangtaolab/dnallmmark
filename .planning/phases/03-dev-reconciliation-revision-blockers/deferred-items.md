# Phase 03 Deferred Items

Out-of-scope discoveries logged during execution (per executor scope boundary).

| Logged | Plan | Item | Routed to |
|---|---|---|---|
| 2026-10-10 | 03-01 | README.md "Run Pipeline" section (post-edit ~L210) still states the pipeline "will also generate a summarized performance result ... named `{model_name}_performance.json`" — true of the deprecated `dnallmmark_pipeline.py`, NOT of `run_finetune.py` (no performance-JSON exporter; RESEARCH State-of-the-Art). Rewording front-runs the REV-03 exporter work, so left as-is here. | Phase 4 (REV-03 exporter) should update this sentence when the exporter lands |
