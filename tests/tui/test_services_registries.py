"""
Tier-1 service test for ``tui/services/registries.py`` (Phase 8, 08-03
tracer).

The tui → pipeline seam proof: the first services module imports the
REAL pipeline registry loader and returns the REAL committed registry
counts — no fakes on this path (the plan's acceptance criterion). Pinned
decisions:

- one-directional seam: the service imports ``registry_loader`` as a
  top-level module; the parent ``tests/conftest.py`` supplies the
  ``pipeline/`` sys.path root for this lane (``tests/tui/conftest.py``
  adds the repo root for the package-qualified ``tui`` import).
- machine independence (the ``tests/test_registry_loader.py``
  ``pin_custom_dir`` discipline, its Pitfall 3): the custom overlay dir
  is pinned to a fresh empty tmp dir, so the assertion pins the
  COMMITTED official registries — 62 models / 50 datasets — regardless
  of any local ``~/.config/dnallmmark/custom_{models,datasets}.json``
  a machine may carry. The overlay MERGE semantics are pinned by
  ``tests/test_registry_loader.py``; this test pins the seam plus the
  real data.

See also:
    ``tui/services/registries.py`` — the service under test.
    ``tests/test_registry_loader.py`` — the overlay merge contract.
"""

from tui.services.registries import load_registry_counts


def test_load_registry_counts_returns_committed_registry_counts(
        monkeypatch, tmp_path):
    """The seam returns the real committed counts: (62, 50).

    ``load_registry_counts()`` loads through
    ``pipeline/registry_loader`` (the overlay-merged view); with the
    custom overlay pinned empty, the merged view IS the committed
    official registry.
    """
    empty_overlay = tmp_path / "custom"
    empty_overlay.mkdir()
    monkeypatch.setenv("DNALLMMARK_CUSTOM_REGISTRY_DIR", str(empty_overlay))

    assert load_registry_counts() == (62, 50)
