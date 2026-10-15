---
phase: quick-261015-pex
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - scripts/demo/record_tui_demo.py
  - scripts/demo/record.sh
  - Makefile
  - .gitignore
  - docs/TUI-DEMO.md
  - docs/demo/RECORDED.md
  - docs/demo/casts/
  - docs/demo/gifs/
  - README.md
  - docs/TUI-GUIDE.md
  - .planning/STATE.md
  - .planning/WINDOWS.md
autonomous: true
requirements: [PEX-1, PEX-2, PEX-3, PEX-4, PEX-5]
user_setup: []

estimate:
  tokens: 110000
  raw_tokens: 55000
  tasks: 3
  confidence: low

must_haves:
  truths:
    - "PEX-1 (real-task footage): docs/TUI-DEMO.md demonstrates the maintainer's full operator journey with REAL footage recorded on this box — env check with a live kernel re-run (r), model/dataset marks + preset apply/save + the 59x50 presence matrix (slot 2), a REAL ModelScope model download (slot 2 d) and dataset download (slot 3 d) with live percent + transfer-rate display (EHC-4), run config with live dry-run preview (p), the y-confirm launch gate (EHC-2) PLUS a real stage-0 single-GPU serialization-guard refusal captured by attempting a second launch while the first is live (EHC-3), REAL training of plant-dnabert-6mer x iDNA_ABF__5mC (seeds 42,43) monitored on slot 5 (entry folding, checkpoint progress, t log tail, f failures modal), the kill via q -> exit modal -> k, the from-failures rerun driven to completion, the L language toggle live (default en -> zh), the wizard (slot 3 w dataset wizard; slot 2 w model wizard), and custom-entry management (e toggle with restore, disabled suffix, wizard prefill)"
    - "PEX-2 (bilingual pairs): every walkthrough section ships TWO GIFs — the en recording (boots in the default English) and the zh recording (reached by pressing L on camera); the language is restored to the boot language before each recording ends"
    - "PEX-3 (real-training hygiene): all demo sweeps run with output root ./finetuned-demo (gitignored via a new finetuned-demo/ entry) — the real pipeline/finetuned/ tree is never written; each recording boots the TUI with a FRESH per-scene DNALLMMARK_TUI_STATE_DIR so queue/run-spec/env-cache/language state is deterministic across scenes; the real config root stays live so customs are visible, and any state the demo toggles there (custom enabled flag) is restored on camera"
    - "PEX-4 (deterministic regeneration): one command — scripts/demo/record.sh SCENE LANG — re-records any single GIF end-to-end (asciinema rec wrapping the pexpect driver -> agg render), the driver's scene timelines are declarative key/wait/anchor tables derived from tui/strings.py constants, and docs/TUI-DEMO.md's re-record section documents that re-recording re-runs the bounded small training while the EHC-3 single-GPU guard keeps it from colliding with any production sweep"
    - "PEX-5 (gates): make lint + make typecheck green including the new driver; full make test at exactly the box baseline 7 failed / 1795 passed, zero new tests added; tui/ source files byte-untouched (git diff over tui/ empty); UI bugs discovered during recording are logged in .planning/WINDOWS.md and NOT fixed; all commits plain (no attribution trailers of any kind); branch autorun pushed at the end; .planning/STATE.md gains the quick-task row"
  artifacts:
    - scripts/demo/record_tui_demo.py
    - scripts/demo/record.sh
    - docs/TUI-DEMO.md
    - docs/demo/RECORDED.md
    - docs/demo/casts/{scene}-{en,zh}.cast
    - docs/demo/gifs/{scene}-{en,zh}.gif
    - Makefile
    - .gitignore
    - README.md
    - docs/TUI-GUIDE.md
  key_links:
    - "scripts/demo/record.sh -> asciinema rec --overwrite --idle-time-limit 3 -c 'uv run --group dev --with pexpect==4.9.0 python scripts/demo/record_tui_demo.py --scene S --lang L' docs/demo/casts/S-L.cast -> agg --theme monokai --speed N S-L.cast S-L.gif -> relative paths embedded in docs/TUI-DEMO.md sections all resolve on disk"
    - "record_tui_demo.py -> pexpect.spawn of 'uv run --group tui --group gpu python -m tui' at pinned dimensions (100x30) with a fresh per-scene DNALLMMARK_TUI_STATE_DIR, relay loop writes child.before + child.match bytes verbatim to stdout (what asciinema records) while stepping the scene timeline"
    - "README.md Operator Console section + docs index, and docs/TUI-GUIDE.md intro -> docs/TUI-DEMO.md"
---

<objective>
Create docs/TUI-DEMO.md — the maintainer-directed demo document ("demo 里面需要跑真实的任务，演示所有的功能", 2026-10-15) — plus everything needed to produce and regenerate its footage: a deterministic pexpect scene driver, real asciinema+agg recordings of ALL ten journey steps in BOTH languages (en default + zh via L), and inbound links from README.md and docs/TUI-GUIDE.md.

Purpose: the TUI milestone closes with public, reproducible proof that every console feature works on real tasks — real ModelScope downloads, a real (bounded, pre-authorized) plant-dnabert-6mer x iDNA_ABF__5mC training through the y-gate, live monitoring, kill, and from-failures rerun.
Output: scripts/demo/ driver + wrapper, docs/demo/ casts + GIFs + RECORDED.md ledger, docs/TUI-DEMO.md, link edits, STATE.md row, pushed plain commits.

Recording chain (maintainer-ratified 2026-10-15, vhs abandoned): asciinema 3.2.1 rec wraps a deterministic driver; agg renders the GIF. No browser anywhere.
</objective>

<execution_context>
@~/.claude/gsd-core/workflows/execute-plan.md
@~/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md

@docs/TUI-GUIDE.md
@docs/multi-gpu.md

# Key machine facts (verified live 2026-10-15, this box)
- asciinema 3.2.1 + agg on PATH (linuxbrew), end-to-end smoke passed.
- pipeline/models/plant-dnabert-6mer and pipeline/datasets/iDNA_ABF_datasets exist on disk.
- make tui expands to: uv run --group tui --group gpu python -m tui (Makefile target, line ~206).
- The full key map authority: docs/TUI-GUIDE.md screen sections (slots 1-6, gate stages, EHC-1..4 behaviors).
- WINDOWS ledger: .planning/WINDOWS.md. Baseline: 7 failed / 1795 passed.
- pexpect 4.9.0 present ambiently in .venv (via a manual ipython install) but NOT in uv.lock — never rely on ambient state; the driver pulls it on demand via uv run --with pexpect==4.9.0 (the textual-dev precedent, pyproject comment ~line 60). PyPI legitimacy verified at plan time: maintained by Thomas Kluyver / Noah Spurrier / Jeff Quast, 4.9.0 is the current stable release, ISC license, stable hashes on the project page.
</context>

<tasks>

<task type="auto">
  <name>Task 1: Deterministic pexpect scene driver + lint wiring + demo gitignore</name>
  <files>scripts/demo/record_tui_demo.py, scripts/demo/record.sh, Makefile, .gitignore</files>
  <action>
Create scripts/demo/record_tui_demo.py — the deterministic TUI demo driver. Contract:

1. CLI: --scene NAME --lang {en,zh} --dry-run --list-scenes, plus --tui-cmd and --speed overrides. pexpect is imported LAZILY inside the spawn path only, so --dry-run and --list-scenes run under plain uv run --group dev with no pexpect, no GPU, no network.
2. The TUI is spawned as a real pty child via pexpect.spawn("uv", ["run", "--group", "tui", "--group", "gpu", "python", "-m", "tui"], dimensions=(30, 100), env including a FRESH per-recording DNALLMMARK_TUI_STATE_DIR (mktemp -d) and TERM set; the real config root stays live so the maintainer's custom entries render (per PEX-3).
3. Relay loop: advance a declarative scene timeline — a list of steps, each either a key/send string, an anchor (pexpect.expect on a language-aware stable string derived from tui/strings.py constants; read strings.py and pick anchors at implementation time, do not guess), or a timed wait (generous hard timeout with early-exit on completion anchor for downloads/training). Every consumed byte (child.before + child.match) is written verbatim to sys.stdout.buffer with flush — that stdout IS what asciinema records. Send esc before every navigation digit or global key so no focused input ever swallows it (a focused input consumes digits and L — the L toggle requires an unfocused screen).
4. Language contract (--lang zh): after boot, detect the boot language by anchor; if booted en, press L on camera (the toggle itself is demo footage); before the scene ends, press L again if the language differs from the boot language, leaving the box in its boot state.
5. The ten scenes (kebab-case names, timelines as data): env-check (fresh state dir means the 8 kernels run live on boot; also press r and wait for the done pass; enter drill-down on one row then esc); selection-presets (slot 2: space marks on plant-dnabert-6mer and neighbors, / filter with a registry-grammar term then esc, p preset picker apply, s save a preset named demo-walkthrough, v presence matrix then esc); model-download (slot 2: cursor to the chosen missing ADAPTED model — chosen at record time by live presence scan over the registry x disk x pipeline/dnallm_compat.json, smallest eligible; d; wait for the live percent + rate cell to reach the finished flip); dataset-download (slot 3: v missing-only view, cursor to the chosen smallest missing dataset, d, watch queue-row percent + progress bar + EHC-4 rate to done flip, enter drill-down on the finished row, esc); run-config-preview (slot 4: m picker flip, space-mark plant-dnabert-6mer and iDNA_ABF__5mC via the filter, edit seeds to 42,43, type ./finetune-demo — typo-guard: ./finetuned-demo — into the output-root input, p preview modal showing the verbatim argv, esc); launch-monitor-kill (slot 4: enter -> gate -> confirm modal shows the cell count -> y launches (EHC-2: enter stays inert — press enter FIRST to show nothing happens, then y) -> auto-switch to slot 5 -> press 4 then enter to capture the REAL stage-0 EHC-3 refusal naming the running root, esc, 5 -> watch the entries table folding (seed 1 completes, seed 2 running with checkpoint steps/max + bar), t log-tail modal then esc, f failures modal then esc, q -> exit modal -> k kills the sweep and quits); rerun-from-failures (fresh boot: 5, a attach pipeline/finetuned-demo (confirm the accepted path form at rehearsal), f failures modal, r -> y confirm (enter shown inert first), watch the failed seed rerun to the folded done state); language-toggle (slot 1 or 2, press L, capture the full-screen zh re-render, navigate one screen to show bars/footer switched); wizard (slot 3 w dataset wizard: advance several steps with real field edits per the wizard keys enter/b, esc-cancel without landing; slot 2 w model wizard: open, one step, esc); custom-entries (slot 2: cursor to a real custom row, e disables — capture the disabled suffix — then e again to RESTORE, w on the custom row shows the prefilled edit form, esc).
6. --dry-run prints each scene's timeline (steps, anchors, waits) and exits 0 without spawning anything. Include a module docstring stating: UI changes require re-deriving anchors from tui/strings.py; the driver NEVER edits tui/ source.

Create scripts/demo/record.sh — the one-command regeneration wrapper: for SCENE LANG it runs asciinema rec --overwrite --idle-time-limit 3 with -c set to the exact uv run --group dev --with pexpect==4.9.0 python scripts/demo/record_tui_demo.py invocation, writing docs/demo/casts/SCENE-LANG.cast, then agg --theme monokai --speed SPEED (default 1.5; record.sh accepts a per-call speed for the long training scenes) rendering docs/demo/gifs/SCENE-LANG.gif, and appends/refreshes the row in docs/demo/RECORDED.md (scene, lang, real target keys chosen, cast+gif sizes, date). Create docs/demo/ and docs/demo/casts/, docs/demo/gifs/ now.

Makefile: extend make lint the established way — mirror the QUICK_L6H_SCRIPTS / PHASE12_MODULES existence-guard idiom (~lines 167-181) with a QUICK_PEX_DEMO var for scripts/demo/record_tui_demo.py, appended to the lint recipe. ty needs no change: [tool.ty.src] already includes scripts/.

.gitignore: add finetuned-demo/ (pattern beside the existing finetuned-smoke/ line) so the demo output root can never be committed.

Ruff + ty must pass over the driver with zero noqa suppressions beyond what the surrounding codebase idiom uses.
  </action>
  <verify>
    <automated>make lint && make typecheck && uv run --group dev python scripts/demo/record_tui_demo.py --list-scenes && uv run --group dev python scripts/demo/record_tui_demo.py --scene launch-monitor-kill --lang en --dry-run && git diff --stat -- tui/ | wc -l | grep -qx 0; echo EXIT=$?</automated>
  </verify>
  <done>Driver + wrapper committed (plain message, no trailers); make lint and make typecheck green including the new file; --list-scenes prints all ten scenes; --dry-run prints the launch-monitor-kill timeline without spawning; tui/ untouched; .gitignore covers finetuned-demo/.</done>
</task>

<task type="auto">
  <name>Task 2: Rehearse, record all scenes en+zh with real downloads and real training, render GIFs</name>
  <files>docs/demo/casts/, docs/demo/gifs/, docs/demo/RECORDED.md, .planning/WINDOWS.md</files>
  <precondition>asciinema 3.2.1 + agg on PATH; pipeline/models/plant-dnabert-6mer and pipeline/datasets/iDNA_ABF_datasets present; no live sweep on the box (the EHC-3 guard would refuse the demo launch — check the monitor/nvidia-smi first); ModelScope reachable; the six critical env kernels green on slot 1.</precondition>
  <action>
Record REAL footage, per PEX-1/PEX-2/PEX-3. Sequence:

1. REHEARSAL FIRST, unrecorded: run the driver directly (no asciinema) for launch-monitor-kill once end-to-end. Confirm with live eyes: the y-gate launches; seed 42 of plant-dnabert-6mer x iDNA_ABF__5mC completes and seed 43 starts (epoch default; the Phase-7 bounded smoke was ~77s/seed); the stage-0 second-launch refusal fires; q->k kills. Then rehearse rerun-from-failures on the killed root: confirm 5 -> a attach accepts pipeline/finetuned-demo and the f modal lists the killed cell so r has work — the failures source over a SIGTERM-killed group is the one uncertain link (MUTABLE: decide from this live observation). If the killed root yields NO failure entries, fall back honestly: attach a real root under pipeline/finetuned that carries historical failures (live scan) for the rerun footage, and record the killed-cell behavior as a WINDOWS note instead of staging anything fake. Tune wait timings/anchors from what you observe; fix the driver, never the TUI.
2. Choose the real download targets by LIVE presence scan (never hardcode at plan distance): model-download = smallest missing ADAPTED model (registry x disk x dnallm_compat.json verdict); dataset-download = smallest missing dataset. If NO adapted model is missing on this box, record the slot-2 surface honestly (already-downloaded toast, manual-placement states) and let dataset-download carry the live-speed footage — RECORDED.md states which shape was taken and why.
3. Record every scene x {en, zh} via scripts/demo/record.sh (20 recordings expected; 18 if model-download took the no-target shape). Watch each recording's live run — a scene whose anchor times out is a driver-timing fix, rerun that scene. Bounded GPU is pre-authorized for exactly this small training (2 languages x [seed-42 full + seed-43 partial kill] + 2 languages x rerun-to-completion ~= 6-8 minutes GPU total); full sweeps remain dual-gated and untouched.
4. UI bugs observed during recording: append to .planning/WINDOWS.md, do NOT fix (gate). Timing/GIF hygiene: --idle-time-limit 3 on rec; use a higher agg --speed (2-2.5) only for launch-monitor-kill and rerun-from-failures; target each GIF > 40KB (non-blank) and the whole docs/demo/ set under ~60MB — if over, re-render the heaviest GIFs at higher speed before committing.
5. docs/demo/RECORDED.md: the scene x lang table with the real target keys, chosen fallbacks, sizes, and the recording date — this ledger is the doc's honesty record.
  </action>
  <verify>
    <automated>N=$(grep -cE '^\| ' docs/demo/RECORDED.md); test "$(find docs/demo/gifs -name '*.gif' | wc -l)" -eq "$N" && test "$(find docs/demo/casts -name '*.cast' | wc -l)" -eq "$N" && test -z "$(find docs/demo/gifs -name '*.gif' -size -40k)" && grep -ql 'plant-dnabert-6mer' docs/demo/casts/run-config-preview-en.cast docs/demo/casts/run-config-preview-zh.cast docs/demo/casts/launch-monitor-kill-en.cast && grep -ql 'finetuned-demo' docs/demo/casts/run-config-preview-en.cast docs/demo/casts/run-config-preview-zh.cast && test "$(grep -l '<ZH_TOPBAR_TOKEN>' docs/demo/casts/*-zh.cast | wc -l)" -eq "$(ls docs/demo/casts/*-zh.cast | wc -l)" && du -sh docs/demo && git diff --stat -- tui/ | wc -l | grep -qx 0; echo EXIT=$?</automated>
  </verify>
  <done>All scene x lang GIFs + casts exist with non-trivial sizes; RECORDED.md rows match the file counts; the real training key plant-dnabert-6mer and the demo root finetuned-demo appear in the gate-scene casts; every zh cast contains the zh top-bar anchor (substitute the exact strings.py zh token for <ZH_TOPBAR_TOKEN> at execution); docs/demo under ~60MB; real pipeline/finetuned/ untouched; tui/ source untouched; any UI bugs logged in .planning/WINDOWS.md; recordings committed plain.</done>
</task>

<task type="auto">
  <name>Task 3: Write docs/TUI-DEMO.md, link it in, final gates, STATE row, push</name>
  <files>docs/TUI-DEMO.md, README.md, docs/TUI-GUIDE.md, .planning/STATE.md, .planning/quick/261015-pex-tui-demo-doc-docs-tui-demo-md-real-task-/261015-pex-SUMMARY.md</files>
  <action>
Write docs/TUI-DEMO.md (English body, repo doc conventions; every claim must match what the footage actually shows — RECORDED.md is the source of truth for real targets):

1. Intro: what this document is, the operator-journey map, and HOW the footage was made (real tasks on a real box; asciinema+agg chain; no browser). One line on the trust story: the numbers, gates, and guardrails visible in the GIFs are the production behaviors (EHC-1..4), not mockups.
2. Ten journey sections in order — env check; selection, presets, presence; model download; dataset download and the queue; run config and the live preview; the launch gate, y-confirm, and the single-GPU guard; live monitoring and the kill; the from-failures rerun; the language toggle; wizard and custom entries. EACH section embeds BOTH GIFs via relative paths (demo/gifs/scene-en.gif and demo/gifs/scene-zh.gif), then: what the feature does, the keys used (concise inline table; deep links to the matching docs/TUI-GUIDE.md section for the full map), and a "what actually happened" walkthrough narrative naming the real model/dataset keys, seeds, the ./finetuned-demo output root, and honest notes for anything that degraded during recording.
3. Re-recording section: prerequisites (asciinema + agg via linuxbrew), the scripts/demo/record.sh SCENE LANG one-liner per scene, the anchor-refresh rule (tui/strings.py is the anchor authority after UI changes — the driver never edits tui/), the note that re-recording re-runs the bounded small training and that the EHC-3 single-GPU guard keeps demo re-records from colliding with production sweeps, the download-scene caveat (presence is now present — pick the next missing target or remove the demo-downloaded dir before re-recording, operator's choice), and the size/speed guidance.
4. Links: README.md — add a sentence in the Operator Console (TUI) section (~line 383, beside the TUI-GUIDE runbook link) pointing at docs/TUI-DEMO.md for the recorded full-feature walkthrough, and a docs/TUI-DEMO.md bullet in the documents index (~line 574, after TUI-GUIDE.md). docs/TUI-GUIDE.md — extend the intro see-also sentence (line 3) with the demo doc (note the file's generated-by header: this is a one-line addition in the established sentence pattern; flag it in the SUMMARY so the next doc-writer regen keeps it).
5. Final gates, in order: make lint && make typecheck; full make test at EXACTLY the 7 failed / 1795 passed baseline (zero new tests were added by this task); confirm tui/ byte-untouched; confirm every GIF path referenced in TUI-DEMO.md exists on disk; commits plain (git log --format=%B over this task's commits contains no Co-Authored-By or attribution trailers — standing maintainer rule); write 261015-pex-SUMMARY.md (house quick-task style; include the rehearsal outcome for the killed-root failures question and any WINDOWS rows added); append the 261015-pex row to .planning/STATE.md Quick Tasks Completed table; push autorun.
  </action>
  <verify>
    <automated>make lint && make typecheck && grep -c '](demo/gifs/' docs/TUI-DEMO.md && for p in $(grep -oP '\]\(demo/[^)]+?\)' docs/TUI-DEMO.md | sed 's/^](//;s/)$//'); do test -f "docs/$p" || echo "MISSING docs/$p"; done && grep -q 'TUI-DEMO' README.md && grep -q 'TUI-DEMO' docs/TUI-GUIDE.md && ! git log --format=%B -5 | grep -qi 'co-authored-by\|generated-with\|attribution' && git diff --stat -- tui/ | wc -l | grep -qx 0; echo EXIT=$?; make test 2>&1 | tail -3</automated>
  </verify>
  <done>docs/TUI-DEMO.md exists with ten sections, each embedding en+zh GIFs whose paths all resolve; README (operator-console section + docs index) and TUI-GUIDE link to it; make lint + make typecheck green; full make test at exactly 7F/1795P baseline; tui/ untouched; all commits trailer-free; SUMMARY + STATE.md row written; autorun pushed. After this task, run the two remaining verify lines explicitly: the full make test tail must show 7 failed / 1795 passed before declaring done.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| PyPI -> venv | uv run --with pexpect==4.9.0 fetches pexpect on demand for the driver |
| ModelScope -> pipeline/ roots | Real downloads land in the real pipeline/models/ and pipeline/datasets/ roots (existing integration, exercised not extended) |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-pex-01 | Tampering (supply chain) | uv --with pexpect fetch in scripts/demo/record.sh | medium | mitigate | Exact pin ==4.9.0; legitimacy verified at plan time (PyPI: maintained by Kluyver/Spurrier/Quast, current stable release, ISC, hashes published); never a committed dependency group, so CI and uv.lock are untouched |
| T-pex-02 | Tampering | demo downloads write into real pipeline/ roots | low | accept | Existing maintainer-directed ModelScope channel (2026-10-14 ruling); targets limited to the smallest missing entries chosen by live presence scan; RECORDED.md documents exactly what landed |
| T-pex-03 | Repudiation | GIFs presented as feature proof | low | mitigate | RECORDED.md ledger + walkthrough narratives name the real keys/seeds/roots; any degraded moment is documented, never staged |
| T-pex-SC | Tampering | pip installs (uv --with) | high | mitigate | Only the T-pex-01 pin; no other installs anywhere in this task; no [ASSUMED]/[SUS] packages left unverified, so no blocking checkpoint is required |
</threat_model>

<verification>
- Task 1: make lint + make typecheck include the driver; --list-scenes and --dry-run exit 0; tui/ diff empty.
- Task 2: GIF/cast counts equal RECORDED.md rows; no blank GIFs; plant-dnabert-6mer + finetuned-demo anchors present in gate-scene casts; zh anchor present in every zh cast; docs/demo under ~60MB.
- Task 3: every doc-embedded GIF path exists; README + TUI-GUIDE inbound links present; make test exactly 7 failed / 1795 passed; trailer-free commits; STATE.md row; autorun pushed.
</verification>

<success_criteria>
- docs/TUI-DEMO.md demonstrates every feature on the maintainer's journey list with real footage, bilingual per section.
- The demo training wrote only to the gitignored ./finetuned-demo root; real trees untouched.
- Anyone can regenerate any GIF with one scripts/demo/record.sh command; anchors trace to tui/strings.py.
- All five gates green: ruff+ty, 7F-zero-new baseline, tui/ untouched, plain commits, pushed.
</success_criteria>

<output>
Create .planning/quick/261015-pex-tui-demo-doc-docs-tui-demo-md-real-task-/261015-pex-SUMMARY.md when done
</output>
