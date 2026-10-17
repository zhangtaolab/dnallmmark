"""
services — the textual-free service layer (Phase 8 foundation, 08-02).

Contract — the foundation invariant every later Phase 8-12 plan builds on:

- ZERO textual imports in ANY module under ``tui/services/``, directly or
  transitively. Presentation belongs to ``tui/screens/``; services are pure
  orchestration + I/O that tier-1 headless tests exercise without a display
  (D-03: GPU-touching kernels are launched by screens inside
  ``@work(thread=True)`` workers, never here). The tripwire is
  ``tests/tui/test_import_lock.py`` (08-03), following the Phase 7
  absence-lock discipline.
- Imports are one-directional into the pipeline seams only: ``env_smoke``
  (structured CheckResult kernels, D-02 — imported, never re-implemented,
  never subprocess-parsed), ``registry_loader`` (overlay-merged registries),
  ``artifact_loader`` (tolerant JSON reads, D-19), plus ``platformdirs``
  for the XDG state/config split (D-04) and the stdlib. Nothing else.
- XDG persistence split (D-04): env-check results → ``user_state_dir``;
  user presets/templates/settings → ``user_config_dir``. Atomic writes
  (tmp + ``os.replace``). Test injection via whole-dir env overrides
  (``DNALLMMARK_TUI_STATE_DIR`` / ``DNALLMMARK_TUI_CONFIG_DIR`` — the Phase 7
  ``DNALLMMARK_CUSTOM_REGISTRY_DIR`` precedent).
- TUI orchestrates, never computes (binding constraint 5): presence columns
  read committed artifacts (``n_audit.json``), presets derive from
  ``pipeline/sweep_priorities.json``, registries load through
  ``registry_loader`` — no benchmark semantics are re-implemented here.

Zero dependencies beyond the stdlib, the ``[tui]`` group's platformdirs, and
the pipeline modules above — so every CPU lane (dev/CI) can import this
layer; textual itself is only needed by screens and the tier-2 Pilot lane
(binding constraint 2: CI stays GPU-free and display-free).
"""

# Deliberately import-free: the services package gains its first modules in
# 08-03+ (settings, registries, env_check, ...); importing tui.services must
# stay side-effect-free.
