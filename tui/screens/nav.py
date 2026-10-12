"""
nav — the navigation-shell bars (Phase 9, 09-03, D-13/D-15).

The presentational chrome of the shell: the 1-row top menu bar (six
digit-prefixed slots with the ratified verbatim resource-noun names,
active slot marked with the diamond prefix + bold + accent — the
glyph+color+weight triple channel) and the 1-row bottom submenu bar
(left segment: the active screen's command keycaps in
binding-declaration order, clipped at the available width with a
trailing ellipsis; right segment: the constant help/quit pair).

Contract (locked decisions):

- PRESENTATIONAL ONLY (D-15): the per-screen ``BINDINGS`` declarations
  remain the single key-map authority — this module consumes
  ``binding_row`` output and strings constants; a hardcoded bar label
  that disagrees with BINDINGS is a defect. No second binding registry
  exists here.
- D-16: each bar occupies exactly one chrome row (replacing Header +
  Footer on the base screens); the bars count against the 80x24 content
  budget. Below the minimum grid the existing min-size guard hides
  everything — zero guard-code changes (the bars are ordinary widgets
  inside the base screens).
- The bars are static chrome derived from ``BINDINGS`` + the fixed
  ``NAV_SLOTS`` list — no load state, no data fetch.
- The top-bar slot vocabulary is fixed and fits 80 columns (digit +
  verbatim label, single-space separators, the placeholder suffix
  attached without a space) — the overflow policy for any future slot
  is the bottom bar's clip rule.
- ZERO binding declarations here: digits are declared per base screen
  (plain bindings, never priority — Pattern 2); this module renders, the
  composition root routes.

I18N-01: zero Chinese literals in this module — slot names, the
placeholder suffix, and every label render through ``tui/strings.py``
constants. Comments stay English-only (the screens-tier grep scans the
whole file).
"""

from typing import NamedTuple

from rich.text import Text
from textual.binding import BindingType
from textual.containers import Horizontal
from textual.widgets import Static

from tui.strings import (
    NAV_LABEL_ABOUT,
    NAV_LABEL_DATA,
    NAV_LABEL_ENV,
    NAV_LABEL_MONITOR,
    NAV_LABEL_RUN_CONFIG,
    NAV_LABEL_SELECTION,
    NAV_PLACEHOLDER_SUFFIX,
)

# Keycap styles (theme tokens — the Footer treatment migrates verbatim:
# key char accent, label muted).
_KEYCAP_KEY_STYLE = "$accent"
_KEYCAP_LABEL_STYLE = "$text-muted"


class NavSlot(NamedTuple):
    """One top-menu slot: digit, verbatim label, routing, placeholder."""

    index: int
    label: str
    #: The routing target ("env_check" | "selection" | "about"); None
    #: marks a placeholder slot delivered by a later phase.
    target: "str | None"
    #: The delivering phase for placeholder slots (the toast's {n}).
    phase: "int | None"


#: The six D-13 slots in bar order — the fixed vocabulary. Slot names are
#: the RATIFIED verbatim resource nouns; slots 3/4/5 are placeholders
#: delivered by Phases 10/11/12 (data manager / run config / monitor).
NAV_SLOTS: "tuple[NavSlot, ...]" = (
    NavSlot(1, NAV_LABEL_ENV, "env_check", None),
    NavSlot(2, NAV_LABEL_SELECTION, "selection", None),
    NavSlot(3, NAV_LABEL_DATA, None, 10),
    NavSlot(4, NAV_LABEL_RUN_CONFIG, None, 11),
    NavSlot(5, NAV_LABEL_MONITOR, None, 12),
    NavSlot(6, NAV_LABEL_ABOUT, "about", None),
)

NAV_SLOT_BY_INDEX = {slot.index: slot for slot in NAV_SLOTS}


def binding_row(binding: BindingType) -> "tuple[str, str] | None":
    """One binding declaration -> its (display key, label) row.

    The single key-map projection both the help modal and the bottom
    bar's left segment consume (moved from ``tui/app.py`` so screens-tier
    modules can import it without a circular import — the composition
    root re-imports it from here). Handles both BINDINGS forms:
    ``Binding`` objects (key_display shown when set) and the tuple
    shorthands; hidden bindings (``show=False``) and description-less
    bindings never render — the same set the Footer rendered.

    SKELETON (RED): returns no rows; the projection lands with GREEN.
    """
    return None


def keycaps_text(pairs, budget=None) -> Text:
    """Render (key, label) pairs as ``[k]label`` keycaps, clipped.

    Keycaps join with single spaces in the given order; when ``budget``
    is set and the next keycap would exceed it, a trailing ellipsis
    renders and everything after drops (the D-15 clip policy — binding
    declarations are in importance order, so the clip drops the
    least-primary keycaps first). The key char renders accent, the label
    muted (the migrated Footer treatment).

    Args:
        pairs: iterable of (display key, label) pairs.
        budget: the maximum cell width (None = no clipping).

    Returns:
        Text: the assembled keycap line.
    """
    return Text()


class TopMenuBar(Horizontal):
    """The D-13 top menu bar: six slots, digit-prefixed, active marked.

    Composed by the base screens; the active slot is read from the
    screen's ``NAV_SLOT`` class attribute at mount (each screen owns its
    own bar instance — screens are switched, not restyled).
    """

    def on_mount(self) -> None:
        """Mount the six slot Statics (GREEN lands the rendering)."""


class BottomBar(Horizontal):
    """The D-15 bottom submenu bar: left keycaps + constant right pair."""

    def on_mount(self) -> None:
        """Mount the two segments (GREEN lands the rendering)."""
