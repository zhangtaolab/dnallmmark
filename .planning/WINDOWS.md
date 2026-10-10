---
schema_version: 1
open_count: 13
waived_count: 0
fixed_count: 1
total_count: 14
last_updated: 2026-10-10T18:29:17.849Z
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
| 10 | 05 | unrun-verify | .github/workflows/ci.yml |  | First real GitHub-runner execution of ci.yml happens on the maintainer's next push (badge green + <15-min/job + branch-protection setup queued in 05-USER-SETUP.md) | open |  | 2026-10-10T10:04:38.260Z |  |
| 11 | 05 | unrun-verify | dnallm-mark/js/main.js |  | 05-02 Task 3 human-check (visual localhost confirmation of weighted default view, raw-rank toggle, stamped footer) deferred to the phase-level UAT gate — behavioral seams pinned by tests/js/main-view-toggle.test.js | open |  | 2026-10-10T10:52:34.776Z |  |
| 12 | 5 | unrun-verify | pipeline/run_finetune.py |  | 05-03: --subset_file seam + pipeline/eval_subsets.json consumption execute only at E2' (GPU, maintainer dual-gated); CPU-side stub/contract tests + real-artifact validation proof pin the behavior — first real GPU consumption pending launch | open |  | 2026-10-10T11:22:28.566Z |  |
| 13 | 05 | deviation | pipeline/sweep_priorities.json |  | 05-04 Task 4 blocking-human gate (tier-2 arena curation, D-17/OQ4): tier 2 shipped EMPTY at Task 2 awaiting maintainer decision — resolved 2026-10-10, maintainer selected per-arena one representative (animal GENERanno-eukaryote-0.5b-base / plant PlantCAD2-Small-l24-d0768 / microbe Omni-DNA-700M), landed in 6598e45 | fixed |  | 2026-10-10T12:27:48.027Z | 2026-10-10T12:27:53.830Z |
| 14 | 06 | deviation | pipeline/env_smoke.py |  | matmul expected constant corrected 64.0->512.0 (Rule 1, found by first executed smoke) | open |  | 2026-10-10T18:29:17.849Z |  |

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
  },
  {
    "id": 10,
    "kind": "unrun-verify",
    "phase": "05",
    "file": ".github/workflows/ci.yml",
    "line": null,
    "description": "First real GitHub-runner execution of ci.yml happens on the maintainer's next push (badge green + <15-min/job + branch-protection setup queued in 05-USER-SETUP.md)",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-10T10:04:38.260Z",
    "resolved_at": null,
    "milestone": "v0.7.1"
  },
  {
    "id": 11,
    "kind": "unrun-verify",
    "phase": "05",
    "file": "dnallm-mark/js/main.js",
    "line": null,
    "description": "05-02 Task 3 human-check (visual localhost confirmation of weighted default view, raw-rank toggle, stamped footer) deferred to the phase-level UAT gate — behavioral seams pinned by tests/js/main-view-toggle.test.js",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-10T10:52:34.776Z",
    "resolved_at": null,
    "milestone": "v0.7.1"
  },
  {
    "id": 12,
    "kind": "unrun-verify",
    "phase": "5",
    "file": "pipeline/run_finetune.py",
    "line": null,
    "description": "05-03: --subset_file seam + pipeline/eval_subsets.json consumption execute only at E2' (GPU, maintainer dual-gated); CPU-side stub/contract tests + real-artifact validation proof pin the behavior — first real GPU consumption pending launch",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-10T11:22:28.566Z",
    "resolved_at": null,
    "milestone": "v0.7.1"
  },
  {
    "id": 13,
    "kind": "deviation",
    "phase": "05",
    "file": "pipeline/sweep_priorities.json",
    "line": null,
    "description": "05-04 Task 4 blocking-human gate (tier-2 arena curation, D-17/OQ4): tier 2 shipped EMPTY at Task 2 awaiting maintainer decision — resolved 2026-10-10, maintainer selected per-arena one representative (animal GENERanno-eukaryote-0.5b-base / plant PlantCAD2-Small-l24-d0768 / microbe Omni-DNA-700M), landed in 6598e45",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-10-10T12:27:48.027Z",
    "resolved_at": "2026-10-10T12:27:53.830Z",
    "milestone": "v0.7.1"
  },
  {
    "id": 14,
    "kind": "deviation",
    "phase": "06",
    "file": "pipeline/env_smoke.py",
    "line": null,
    "description": "matmul expected constant corrected 64.0->512.0 (Rule 1, found by first executed smoke)",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-10T18:29:17.849Z",
    "resolved_at": null,
    "milestone": "v0.7.1"
  }
]
````
