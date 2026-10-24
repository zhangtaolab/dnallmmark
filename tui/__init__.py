"""
tui — the DNALLM-Mark operator console (Phase 8 foundation, 08-02).

A thin read-plan-launch-observe shell over the existing pipeline seams: the
package NEVER re-implements benchmark semantics — it renders state and drives
existing implementations (binding constraint 5: TUI orchestrates, never
computes).

Package layout — the one-directional import boundary (the non-retrofittable
decision of Phase 8):

- ``tui/app.py``       composition root: the ONLY place that subclasses a
                       Textual ``App``; wires screens and services, carries
                       zero business logic.
- ``tui/screens/``     Textual presentation. Imports textual freely (the
                       only tier allowed to); owns zero business logic —
                       everything algorithmically testable lives in
                       services. Populated from 08-03.
- ``tui/services/``    ZERO textual imports, ever — the contract lives in
                       ``tui/services/__init__.py``; locked by
                       ``tests/tui/test_import_lock.py`` (08-03, the Phase 7
                       absence-lock discipline).
- ``tui/strings.py``   the single home for operator-facing copy (I18N-01).
- ``tui/styles.tcss``  Textual CSS — theme tokens only.
- ``tui/__main__.py``  the ``python -m tui`` entry point: REPO_ROOT and
                       ``REPO_ROOT/pipeline`` sys.path bootstrap derived from
                       ``__file__``, never the CWD.

Dependency directions (one-way, never reversed):

- tui → pipeline: services import ``env_smoke`` (structured CheckResult
  kernels, D-02 — never subprocess stdout parsing, never re-written checks),
  ``registry_loader`` (overlay-merged registries), ``artifact_loader``
  (tolerant JSON reads, D-19) as top-level modules — ``pipeline/`` is a
  sys.path root, not a package (the ``__main__`` bootstrap and
  ``tests/*/conftest.py`` provide the insert).
- tui → textual: legal ONLY outside ``tui/services/``.

Phase 8 provenance: the ``[tui]`` dependency group (textual>=8.2,<9 +
platformdirs, D-01 / binding constraint 10), ``make tui``, and this skeleton
land in 08-02; the first screen/service slice (the tracer through screen,
service, and the pipeline seam) lands in 08-03 on this root.
"""

# Deliberately import-free: importing ``tui`` must stay side-effect-free and
# cheap (tests import tui.* modules individually; the console entry point is
# tui/__main__.py).
