---
schema_version: 1
open_count: 1
waived_count: 0
fixed_count: 0
total_count: 1
last_updated: 2026-10-08T14:33:35.112Z
---

# Broken Windows Ledger

> Cross-phase defect register. With `workflow.windows_enforce` enabled, `/gsd-ship` blocks while `open_count > 0`.
> Waive with `gsd-tools windows waive <id> "<reason>"` (reason required).
> Mark fixed with `gsd-tools windows fixed <id>`.

| id | phase | kind | file | line | description | status | reason | recorded_at | resolved_at |
|----|-------|------|------|------|-------------|--------|--------|-------------|-------------|
| 1 | 01 | stub | AUDIT.md | 132 | Secret-scan evidence section is an intentional placeholder filled by plan 01-03 task 3 (REL-05 gitleaks run) | open |  | 2026-10-08T14:33:35.112Z |  |

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
  }
]
````
