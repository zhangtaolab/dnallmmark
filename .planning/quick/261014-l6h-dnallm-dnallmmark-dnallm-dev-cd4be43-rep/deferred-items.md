# Deferred Items — 261014-l6h

## MAINTAINER SMOKE INTEL (read before launching the 2x2): plant-dnamamba-6mer card remote code vs transformers 5.17

The downloaded card (`pipeline/models/plant-dnamamba-6mer/`) ships
custom code (`configuration_mamba.py` + `modeling_mamba.py` wired via
`config.json`'s `auto_map`). On the gpu-group's pinned transformers
5.17.0, loading with `trust_remote_code=True` (which dnallm's
`load_model_and_tokenizer` uses throughout — model.py:1050/1074) FAILS:

```
ImportError: cannot import name 'MambaCache' from 'transformers.cache_utils'
  (…/transformers_modules/plant_hyphen_dnamamba_hyphen_6mer/…/modeling_mamba.py:27)
```

- The REQUIRED l6h probes are green: AutoConfig (MambaConfig,
  model_type mamba) and AutoTokenizer (EsmTokenizer, vocab 4107) both
  load from the local dir; the NATIVE pure-PyTorch path
  (`AutoModelForCausalLM.from_pretrained` WITHOUT trust_remote_code)
  also loads cleanly — 93.7M params, matching the registry's 94M.
- Consequence for the smoke: the `plant-dnamamba-6mer x 2 datasets`
  cells may ImportError at model load inside dnallm's remote-code path.
  Candidate mitigations for a follow-up decision (NOT taken here —
  pipeline behavior is out of l6h scope): strip the `auto_map` from the
  landed config.json (the native transformers `MambaForCausalLM` reads
  the same config natively — proven above), or patch the card's import
  locally, or pin transformers lower for this model.
- The same 5.17 rename likely affects every auto_map-carrying card
  (plant-dnagpt/plant-dnagemma families do NOT carry auto_map; verify
  per-model before wider sweeps).

## Environmental full-suite failure discovered this task (out of scope, NOT introduced by l6h)

`tests/tui/test_services_run_config.py::test_storage_overview_defaults_mirror_real_consumers`
fails on THIS GB10 machine with:

```
assert by_key["log_dir"].exists is False, (
    "pipeline/logs does not exist on a fresh checkout — the honest "
    "glyph for the default log dir")
E       AssertionError: ... assert True is False   (StorageRow .../pipeline/logs exists=True)
```

- **Root cause (proven mechanically this session):** the gitignored
  `pipeline/logs/` directory exists on this machine — leftovers from the
  Phase-7 GB10 smoke (`dnallm.log`, Oct 11) and a later local run
  (`plant-dnabert-6mer_error_log.txt`, Oct 13). The f4w-authored test
  hard-assumes the fresh-checkout state (`pipeline/logs` absent), so it
  can never pass on a machine that has run the pipeline. Proof: with
  `pipeline/logs` moved aside the test passes (1 passed in 0.04s); the
  directory was restored byte-for-byte immediately after.
- **Why the f4w SUMMARY did not see it:** the quick-task full-suite
  evidence ran on the PREVIOUS machine (the 4x5090 AutoDL box, /root —
  hence its 4 root-user chmod persist-failure sims failing there); the
  machine was replaced 2026-10-14 (~15:05 CST) and the GB10 box carries
  its own run-artifact state.
- **Disposition (the c2l/dcl environmental precedent):** documented, not
  fixed here — a fix would touch an unrelated f4w test file (forbidden
  scope widening). Candidate fix for a future quick task: make the
  fresh-checkout glyph assertion hermetic (monkeypatch the overview base
  or skip/derive the expectation from the live dir).
- **Baseline accounting at l6h close:** pytest 1697 passed / 7 failed =
  6 documented baseline (5 test_schemas + 1 test_determinism, the
  post-9e803ca stale pins) + this 1 environmental; the 4 root-user chmod
  persist-sims are GREEN on this non-root machine (environmentally
  green, per c2l's own note); node lane 26/26; the known snapshot flake
  did not strike.
