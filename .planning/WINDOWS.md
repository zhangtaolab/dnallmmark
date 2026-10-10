---
schema_version: 1
open_count: 9
waived_count: 0
fixed_count: 0
total_count: 9
last_updated: 2026-10-10T05:22:49.317Z
---

# Broken Windows Ledger

> Cross-phase defect register. With `workflow.windows_enforce` enabled, `/gsd-ship` blocks while `open_count > 0`.
> Waive with `gsd-tools windows waive <id> "<reason>"` (reason required).
> Mark fixed with `gsd-tools windows fixed <id>`.

| id | phase | kind | file | line | description | status | reason | recorded_at | resolved_at |
|----|-------|------|------|------|-------------|--------|--------|-------------|-------------|
| 1 | 01 | stub | AUDIT.md | 132 | Secret-scan evidence section is an intentional placeholder filled by plan 01-03 task 3 (REL-05 gitleaks run) | open |  | 2026-10-08T14:33:35.112Z |  |
| 2 | 4 | stub | pipeline/models_info.json |  | Chaoba card: series/architecture/context_len/species/type/huggingface/modelscope are empty-string (no locatable upstream page) — 04-04 | open |  | 2026-10-10T03:13:03.112Z |  |
| 3 | 4 | stub | pipeline/models_info.json |  | Chaoba_all_species card: series/architecture/context_len/species/type/huggingface/modelscope are empty-string (no locatable upstream page) — 04-04 | open |  | 2026-10-10T03:13:03.177Z |  |
| 4 | 4 | stub | pipeline/models_info.json |  | Chaoba_denseMamba card: series/architecture/context_len/species/type/huggingface/modelscope are empty-string (no locatable upstream page) — 04-04 | open |  | 2026-10-10T03:13:03.243Z |  |
| 5 | 4 | stub | pipeline/models_info.json |  | denseSSM_plant_genome card: series/architecture/context_len/species/type/huggingface/modelscope are empty-string (no locatable upstream page) — 04-04 | open |  | 2026-10-10T03:13:03.337Z |  |
| 6 | 4 | stub | pipeline/models_info.json |  | mamba2_370M card: series/architecture/context_len/species/type/huggingface/modelscope are empty-string (no locatable upstream page) — 04-04 | open |  | 2026-10-10T03:13:03.403Z |  |
| 7 | 4 | stub | pipeline/models_info.json |  | mamba2_plant_genome card: series/architecture/context_len/species/type/huggingface/modelscope are empty-string (no locatable upstream page) — 04-04 | open |  | 2026-10-10T03:13:03.490Z |  |
| 8 | 4 | stub | pipeline/models_info.json |  | prokbert card: series/architecture/context_len/species/type/huggingface/modelscope are empty-string (no locatable upstream page) — 04-04 | open |  | 2026-10-10T03:13:03.577Z |  |
| 9 | 4 | deviation | tests/test_export_runs.py | 466 | D-15 evaluate cross-check covers the scipy-backed evaluate metrics (pearsonr/spearmanr) only — evaluate's accuracy/f1/mcc modules import scikit-learn, which is outside the sanctioned scipy+evaluate dependency pair; extending coverage needs a maintainer-approved scikit-learn addition | open |  | 2026-10-10T05:22:49.317Z |  |

````json
[
  {
    "id": 1,
    "kind": "stub",
    "phase": "01",
    "file": "AUDIT.md",
    "line": 132,
    "description": "Secret-scan evidence section is an intentional placeholder filled by plan 01-03 task 3 (REL-05 gitleaks run)",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-08T14:33:35.112Z",
    "resolved_at": null,
    "milestone": "v0.7.1"
  },
  {
    "id": 2,
    "kind": "stub",
    "phase": "4",
    "file": "pipeline/models_info.json",
    "line": null,
    "description": "Chaoba card: series/architecture/context_len/species/type/huggingface/modelscope are empty-string (no locatable upstream page) — 04-04",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-10T03:13:03.112Z",
    "resolved_at": null,
    "milestone": "v0.7.1"
  },
  {
    "id": 3,
    "kind": "stub",
    "phase": "4",
    "file": "pipeline/models_info.json",
    "line": null,
    "description": "Chaoba_all_species card: series/architecture/context_len/species/type/huggingface/modelscope are empty-string (no locatable upstream page) — 04-04",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-10T03:13:03.177Z",
    "resolved_at": null,
    "milestone": "v0.7.1"
  },
  {
    "id": 4,
    "kind": "stub",
    "phase": "4",
    "file": "pipeline/models_info.json",
    "line": null,
    "description": "Chaoba_denseMamba card: series/architecture/context_len/species/type/huggingface/modelscope are empty-string (no locatable upstream page) — 04-04",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-10T03:13:03.243Z",
    "resolved_at": null,
    "milestone": "v0.7.1"
  },
  {
    "id": 5,
    "kind": "stub",
    "phase": "4",
    "file": "pipeline/models_info.json",
    "line": null,
    "description": "denseSSM_plant_genome card: series/architecture/context_len/species/type/huggingface/modelscope are empty-string (no locatable upstream page) — 04-04",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-10T03:13:03.337Z",
    "resolved_at": null,
    "milestone": "v0.7.1"
  },
  {
    "id": 6,
    "kind": "stub",
    "phase": "4",
    "file": "pipeline/models_info.json",
    "line": null,
    "description": "mamba2_370M card: series/architecture/context_len/species/type/huggingface/modelscope are empty-string (no locatable upstream page) — 04-04",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-10T03:13:03.403Z",
    "resolved_at": null,
    "milestone": "v0.7.1"
  },
  {
    "id": 7,
    "kind": "stub",
    "phase": "4",
    "file": "pipeline/models_info.json",
    "line": null,
    "description": "mamba2_plant_genome card: series/architecture/context_len/species/type/huggingface/modelscope are empty-string (no locatable upstream page) — 04-04",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-10T03:13:03.490Z",
    "resolved_at": null,
    "milestone": "v0.7.1"
  },
  {
    "id": 8,
    "kind": "stub",
    "phase": "4",
    "file": "pipeline/models_info.json",
    "line": null,
    "description": "prokbert card: series/architecture/context_len/species/type/huggingface/modelscope are empty-string (no locatable upstream page) — 04-04",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-10T03:13:03.577Z",
    "resolved_at": null,
    "milestone": "v0.7.1"
  },
  {
    "id": 9,
    "kind": "deviation",
    "phase": "4",
    "file": "tests/test_export_runs.py",
    "line": 466,
    "description": "D-15 evaluate cross-check covers the scipy-backed evaluate metrics (pearsonr/spearmanr) only — evaluate's accuracy/f1/mcc modules import scikit-learn, which is outside the sanctioned scipy+evaluate dependency pair; extending coverage needs a maintainer-approved scikit-learn addition",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-10T05:22:49.317Z",
    "resolved_at": null,
    "milestone": "v0.7.1"
  }
]
````
