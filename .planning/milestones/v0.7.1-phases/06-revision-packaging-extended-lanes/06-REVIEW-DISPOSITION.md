---
phase: 06-revision-packaging-extended-lanes
dispositioned_at: 2026-10-11T01:21:37Z
review_path: .planning/phases/06-revision-packaging-extended-lanes/06-REVIEW.md
review_commit: ab3540f
findings_total: 16
fixed: 14
info_open: 2
status: complete
---

# Phase 06: Review Disposition

Per-finding disposition for all 16 findings of `06-REVIEW.md` (commit
ab3540f). Fix commits are atomic, one per finding, format
`{type}(06-review): <desc>`, no co-author lines. Full evidence in
`06-REVIEW-FIX.md`.

| ID | Severity | Title (short) | Disposition | Commit |
|----|----------|---------------|-------------|--------|
| HI-01 | High | PROBE_INELIGIBLE omits `SPACE` | **fixed** | d894de4 |
| MED-01 | Medium | `--from-failures` cannot recover a `--peft` sweep | **fixed** | cb168cc |
| MED-02 | Medium | env_smoke datasets-cap label wrong (3.2.0 vs 5.1.0) | **fixed** | c2fa732 |
| MED-03 | Medium | documented provenance correction path aborts | **fixed** | 360a28e |
| MED-04 | Medium | alias-default / resume-marker collision gaps | **fixed** | 5be6627 |
| LOW-01 | Low | ONBOARDING metric enum omits `r2` | **fixed** | 5020553 |
| LOW-02 | Low | README `make data` output block ordering | **fixed** | 27f36c5 |
| LOW-03 | Low | RC sidecar fixed name, overwritten per model | **fixed** | e329c77 |
| LOW-04 | Low | `--models` typos silent in VEP driver | **fixed** | 9e07c98 |
| LOW-05 | Low | marker safety: END-without-BEGIN / multi-marker | **fixed** | 6247abb |
| LOW-06 | Low | "uniform preprocessing" unchecked | **fixed** | b4cb8c9 |
| LOW-07 | Low | `_primary_score` collision precedence | **fixed** | 7bb887e |
| LOW-08 | Low | zero-row fraction selection | **fixed** | bf2cd39 |
| LOW-09 | Low | doi_swap atomicity overclaim | **fixed** | 7bfa5df |
| INFO-01 | Info | fourth noqa'd blind except in VEP driver | **info-open** | — |
| INFO-02 | Info | dry-run cosmetic error line | **info-open** | — |

## Fixed — detail and rationale

### HI-01 (d894de4) — fixed
`SPACE` added beside `space` with per-row provenance comments (uppercase
row claimed by the native `space_models` member case-sensitively,
lowercase by the `extra` self-append — both verified read-only at the
v1.2.1 tag). The pinning test no longer relies on the hard-coded set
alone: it asserts both spellings against the registry AND derives a
case-closure invariant from the registry (case-variant key groups must be
all-in or all-out — substring dispatch routes them to the same special
loader), so future registry case-splits fail the test instead of silently
reopening the hole. A guard-simulation test runs the guard's exact
membership expression over both spellings.

### MED-01 (cb168cc) — fixed
Contract: failure entries carry `base_model` (registry name) beside the
alias `model`; `--from-failures` validates/joins on base names
(`base_model` when present, else a known-suffix strip — legacy manifests
recover); `main()` strips the re-run's `--peft` alias before filtering.
Alias sweep failure → `--from-failures --peft lora` re-enumerates exactly
those alias cells (pinned; this was the review's empirical reproduction,
now green).

### MED-02 (c2fa732) — fixed
`datasets<=3.2.0` → `datasets<=5.1.0` at all three sites; figure
re-verified against `git show v1.2.1:pyproject.toml`. Pinning test now
forbids the stale figure and asserts the corrected one. Reconciles the
observed 5.1.0 resolution from 06-01.

### MED-03 (360a28e) — fixed
ONE canonical contract picked: the `--kind provenance` slice preset
(7-column ingest, merge-only, unknown-row refusal, name lands under
`Dataset_name`). The emitter/schema/DATA.md instruction sites name the
working command; DATA.md regenerated via the emitter. The full documented
path (emit → edit a cell → ingest → no abort → re-emit carries the
correction) is pinned by a test over the real registry and was verified
empirically on scratch copies before pinning. The orchestrator's next
data-value update can run the round-trip exactly as quoted in
06-REVIEW-FIX.md.

### MED-04 (5be6627) — fixed
(a) probe×peft REFUSED at the argv boundary (named error; adapters-on-
frozen is a different experiment) + test. (b) curve → `{model}+curve`;
head → `{model}+head` for generic models only (special_models pair keeps
the base name — their with-head config IS their base config). Default
paths byte-identical (chain still ends at the bare base name; pinned).
Residual disclosed: `--peft` × curve/head WITHOUT `--train_fraction`
still resolves to the peft alias dir — the documented composition pairs
variants with fractions (frac nesting isolates those cells), and the
base-name collision the finding described is closed; refusing that
residual combination would block the legitimate adapter-learning-curve
lane, so it is left as documented composition behavior rather than a
guard.

### LOW-01 (5020553) — fixed
Mechanical doc fix: `r2` listed with the registry↔schema divergence note.

### LOW-02 (27f36c5) — fixed
Mechanical doc fix: expected-output block reordered to the Makefile's
actual chain order.

### LOW-03 (e329c77) — fixed (judgment: small and safe)
Per-model sidecar `{model}.rc.vcf` — auditable, no cross-model
overwrite; the false docstring claim replaced with the real rule.
Chosen over docstring-only because per-model naming is what makes the
sidecar usable as evidence, and nothing else consumes the name.

### LOW-04 (9e07c98) — fixed (mechanical per directive)
Fail-fast filter validation listing unknown names; known unselected
names keep their skip-as-data rows.

### LOW-05 (6247abb) — fixed (judgment: small and safe)
All four malformed marker states abort loudly; three new tests.

### LOW-06 (b4cb8c9) — fixed (judgment: small and safe)
Uniformity is now CHECKED before the appendix asserts it; abort names
the divergence.

### LOW-07 (7bb887e) — fixed (judgment: small and safe)
The frontier resolver now shares the exporter's exact collision rule
(last finite insertion-order key per slot); single-key behavior
identical; parity pinned by running both resolvers over colliding
metrics.

### LOW-08 (bf2cd39) — fixed (mechanical per directive)
Zero-row selection refused at the argv boundary from the registry's
Train counts; no-fraction default byte-identical; real-registry
regression assertion at the documented curve fractions.

### LOW-09 (7bfa5df) — fixed (mechanical per directive: wording)
Atomicity claim scoped to the pattern level, with the loud-rerun note.
Temp-file+rename rejected as churn for a two-line, maintainer-run
window.

## Info-open — rationale

### INFO-01 — the fourth noqa'd blind except in `script/zero_shot_vep.py:715`
**info-open.** The except is disclosed at the line (`# noqa: BLE001 —
row-level isolation`), prints to stderr, and records the failure as the
row's `excluded_reason` — exactly the skip-as-data design the 06-03 plan
documents; no behavior defect. The open item is a POLICY wording: D-08's
boundary statement (embedded in run_sweep's docstring as a Phase-3
decision record) says "no blind `except Exception` outside run_finetune's
three designed isolation sites", and the VEP row-isolation site makes a
fourth. Amending a recorded phase decision is a maintainer-level policy
change (scope the D-08 statement to "designed isolation sites" vs
narrowing the except's exception types over time), not a review-fix
patch — left open for deliberate disposition. Not a widened suppression:
the noqa predates this pass and none was added.

### INFO-02 — `--peft_dry_run` trailing cosmetic error line
**info-open.** Observed, disclosed, and accepted in 06-01-SUMMARY
("behavior is correct as-is"); the review itself does not count it as a
finding per review scope. The cheap cosmetic fix (skip the
completion-glob block under dry-run) remains noted for whenever the file
is next touched for substance — not applied standalone to avoid churning
a disclosed-and-accepted behavior in a fix pass.

## Final state after all fixes

- `make test`: 451 passed (431 baseline + 20 new), node lane 18/18.
- `make lint`: clean (no new/ widened suppressions).
- `make typecheck`: clean.
- Drift gate: `make data` byte-stable no-op; `dnallm-mark/data/` and
  `DATA.md` clean in `git status`.
- Constraints held: no `run_finetune` execution; `run_sweep` only via
  CPU-testable functions/`--dry-run`; `env_smoke` py_compile-only;
  DNALLM repo read-only; no tags; no installs; per-fix atomic commits
  without co-author lines.

---

_Dispositioned: 2026-10-11T01:21:37Z_
_Fixer: Claude (gsd-code-fixer)_
