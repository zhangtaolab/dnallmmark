---
phase: 18-docs-authoring
reviewed: 2026-10-22T16:05:00Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - README.md
  - docs/multi-gpu.md
  - docs/ONBOARDING.md
  - docs/GETTING-STARTED.md
  - docs/TUI-DEMO.md
  - docs/TUI-GUIDE.md
  - docs/v1.3-test-report.html
  - docs/report-assets/README.md
  - tui/strings.py
findings:
  critical: 0
  warning: 3
  info: 2
  total: 5
status: issues_found
---

# Phase 18: Code Review Report

**Reviewed:** 2026-10-22T16:05:00Z
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

Docs+HTML phase reviewed adversarially against the five stated priorities: command-truth, number-provenance, report-HTML self-containment/honesty, stale residue, and the single `tui/strings.py` edit. No Critical issues. Three Warnings (one stale shipped-source fact left in `multi-gpu.md`, one broken ledger table in `docs/report-assets/README.md`, one internal contradiction now present inside `TUI-DEMO.md`) and two Infos.

Verified clean (spot-checked against real sources, not taken on faith):

- **Command-truth** — every documented flag grep-checked against the real argparse surfaces: `run_sweep_shard.py` (`--workers`, `--gpus`, `--models`, `--output-root`, `--dry-run`, `--mode {static,dispatch}` default static, `--merge`, `--include-checkpoints`, `--cleanup`, `--yes PHRASE`, `--rerun-failed`), `run_sweep.py` passthroughs (`--from-failures`, `--dataset_root`, `--registry-dir`, `--num_train_epochs`, `--seeds`, `--log_dir`), `make_subset_datasets.py` (`--dataset-root`, `--output-root`, `--registry-dir`, `--models`, `--tasks`, `--fraction`, `--seed`), `export_runs.py` (`--input-root`, `--dry-run`). No invented argv found; the `run_sweep_shard.py:399-411` `--mode` line citation is accurate.
- **Number-provenance** — 155 s ↔ `7759c2cc` and 272 s ↔ `4e74c92d` both confirmed at the cited 15-01/15-03-SUMMARY lines; no r1 run id appears anywhere in the report; row counts 105/11/117 and 598/74/74 (+ source 2110/234/2344, 11971/1497/1497) match `/root/autodl-tmp/phase15-evidence/subset-generation.log` byte-for-byte; verification scores 23/23, 28/28, 7/7, 41/41, 16/16 match all five frontmatters; 102-passed-in-1.42s, 44/44, 10-passed, 27-passed, and the 2236/3/6 baseline all match their cited artifacts; the Figure-1 mid-run claims (running, 6/12, queue 4, both workers in-flight on `plant-dnamamba-6mer × GUE__emp_H3` seeds 42/43) match `dispatch_state.midrun-sweep-r2.json`; internal arithmetic holds (155 s = 15:20:00→15:22:35; 272 s = 00:11:11→00:15:43; 6 done + 2 in-flight + 4 queued = 12; worker cells 4+8; 59+3=62; 20 requirements).
- **Report HTML** — zero external requests (no `<script>`, no `@import`, no `url(http…)`, no CDN/web-font references), zero absolute `/root` paths, all 7 `<img>` elements carry alt text, all 7 `<figure>` captions carry `Proves:` lines, badge vocabulary is the consistent four-status set, prose uses `&amp;` escaping and the pasted evidence blocks contain no unescaped angle brackets. The 3 TUI SVG captions state precisely what is real (real app instance via snapshot-harness seams, real archived dispatch state, live nvidia-smi) vs what is fixture (card cell grid, screen state/path rows) and carry ◌ PENDING-REVIEW badges; the 4 browser PNGs carry ✓ PASS with real-execution context. SVG contents match their captions (0%, 2/32607 MiB, 28 °C, 6/12, plant-dnamamba rows; 模型 2/62 · 数据集 2/50; 调度计划 line). No mock-labeled-as-execution found.
- **Stale residue** — "composes single sweeps" and static-sharding-only phrasing absent (grep zero hits); dispatch-first restructure in place with the static track retained as documented legacy; the smoke-record fence argv matches 15-01-SUMMARY verbatim.
- **tui/strings.py** — the diff is exactly one `_t()` edit (`ABOUT_MILESTONE_STAGE`: 开发中→已交付 / in development→delivered, pair consistent, no placeholders, no symbol/golden-pinned constant touched).
- The Zenodo `?token=` link in README (flagged by the injection scanner) is the pre-existing, documented intentional sharing link (maintainer decision D-08, `.gitleaks.toml` allowlist) and was not touched by this phase — not a finding.

## Warnings

### WR-01: multi-gpu.md still carries the pre-review 60 s stale-grace value the phase corrected everywhere else

**File:** `docs/multi-gpu.md:289-291`
**Issue:** The dispatch-mode "Watch" section states per-worker dispatch rows are "each stale-marked once its snapshot is ≥ 60 s old." The shipped source pins `DISPATCH_STALE_SECONDS = 3600.0` (`tui/services/dispatch_state.py:74`), and every other surface corrected in this phase states 3600 s — TUI-GUIDE.md ("the cell-scale grace (3600 s, `DISPATCH_STALE_SECONDS`)"), TUI-DEMO.md §11 ("`DISPATCH_STALE_SECONDS` = 3600 s"), and the report HTML ("stale-marked past the shipped 3600 s cell-scale grace", with 18-03's own rationale "shipped-source facts supersede the pre-review UI-SPEC values"). The 60 s figure is exactly the pre-review UI-SPEC value; the correction discipline was applied to three files and missed the fourth, leaving multi-gpu.md contradicting the code and its three sibling docs. This is the "stale residue post-correction" failure class this phase was chartered to eliminate.
**Fix:**
```markdown
# docs/multi-gpu.md, dispatch track §2 ("Watch" bullet), line ~291
- ... plus per-worker in-flight rows, each stale-marked once its
  snapshot's age crosses the cell-scale grace (`DISPATCH_STALE_SECONDS`
  = 3600 s, maintainer-tunable). The same screen carries ...
```

### WR-02: The report-assets honesty ledger table is split by a blank line — 5 of 7 assets render outside the table

**File:** `docs/report-assets/README.md:14-19`
**Issue:** A blank line at line 14 terminates the GFM table that starts at line 10 (`| Asset | Origin | Capture context | Review status |`), so the five rows that follow (`shot-scatter-tooltip.png`, `shot-bars.png`, `shot-bars-tooltip.png`, `run_config.svg`, `run_config_confirm.svg`) are no longer table rows — GitHub renders them as a plain-text paragraph of raw pipes. The per-asset provenance ledger — the artifact the report's honesty claims lean on, and the file whose entire purpose is "one row per asset" — loses its structure for 5 of the 7 embedded assets, including both remaining PENDING-REVIEW TUI captures whose capture-context disclosures are the most load-bearing.
**Fix:** Delete the blank line at line 14 so all seven asset rows form one continuous table under the single header/delimiter pair at lines 10-11.

### WR-03: TUI-DEMO now contradicts itself — the re-record section's collision guarantee is false under the Phase-16 semantics §11 documents

**File:** `docs/TUI-DEMO.md:235`
**Issue:** The pre-existing "Re-recording any GIF" bullet claims: "The **EHC-3 single-GPU guard** is what keeps a demo re-record from colliding with a production sweep: any gated launch refuses at stage 0 while another sweep is live … it can never stack onto your real run." Phase 18 added §11 to this same file stating the amended rule: "the old single-GPU serialization stage became multi-GPU capacity arithmetic — the launch refuses when the live registry's demand plus the requested workers exceeds the machine's effective GPU count" (mirrored in TUI-GUIDE.md's corrected EHC-3 paragraph). Under the amended semantics the old guarantee is false on the machine this repo documents (the 2× RTX 5090 validation box): a live sweep (demand 1) plus a demo re-record launch (workers=1) is 2 ≤ 2 GPUs, so the launch is allowed — and since an unset GPUs field defaults both launches onto GPU 0 (`0..workers-1`), they genuinely stack on the same GPU. The file now documents both the amended gate and a guarantee the amendment removed, which is precisely the internal-inconsistency class the TUI-GUIDE correction targeted.
**Fix:** Reword the bullet to the capacity form, e.g. "The launch gate's GPU-capacity arithmetic (EHC-3 as amended by Phase 16) keeps a demo re-record from colliding with a production sweep on a single-GPU-effective machine, and on multi-GPU machines only within spare capacity — size `workers`/`GPUs` so the re-record cannot land on a GPU a live sweep occupies."

## Info

### IN-01: README's example suite count is 493 tests behind the v1.3 baseline the report cites

**File:** `README.md:185`
**Issue:** The `make test` expected-output example says "1743 passed in ~4.5m" while the v1.3 recorded baseline this milestone's report cites is "2236 passed / 3 skipped / 6 environmental" (17-VERIFICATION.md:121). The line is explicitly hedged ("counts grow as the suite grows"), so it is not an error — but a reader comparing README to the v1.3 test report sees two different headline numbers for the same command.
**Fix:** Refresh the example line to the recorded v1.3 baseline (2236 passed / 3 skipped / 6 environmental, dated) or leave the count symbolic ("N passed") so it stops aging.

### IN-02: Absolute machine paths quoted in the multi-gpu.md subset evidence block

**File:** `docs/multi-gpu.md:354-359`
**Issue:** The subset-workflow "expected output" block quotes the executed log verbatim, including `/root/autodl-tmp/phase15-evidence/subset-generation.log` as the named source and `/root/autodl-tmp/Github/dnallmmark/pipeline/datasets-smoke` inside the quoted output. This is deliberate verbatim-evidence quoting with the source named, and the report HTML's zero-absolute-paths gate was scoped to the report only — but for a public-release hardening milestone the runbook embeds one private machine's layout in three places.
**Fix:** Optional: keep the two measured-output lines verbatim but elide the absolute paths (`… under <repo>/pipeline/datasets-smoke …` and `source: phase15-evidence/subset-generation.log`), or annotate them as machine-local evidence paths.

---

_Reviewed: 2026-10-22T16:05:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
