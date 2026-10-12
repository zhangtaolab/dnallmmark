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
from textual.binding import Binding, BindingType
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

# The keycap key char carries the live theme's accent (resolved from
# ``app.current_theme`` at mount — a rich Text span CANNOT use a Textual
# ``$token`` on the Static render path, probe-pinned on 8.2.8; the value
# IS the theme's, never a hardcoded hex) and the label renders dim (the
# migrated Footer treatment: key accent + label muted, both NO_COLOR-
# legible — brackets and glyph structure carry the meaning).
_ELLIPSIS_STYLE = "dim"


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
    shorthands ``(key, action[, description])`` (the 2-tuple carries no
    footer label — no row for it). Hidden bindings (``show=False``) and
    description-less bindings never render — the same set the Footer
    rendered (a hidden binding listed in a bar would advertise a key the
    footer deliberately hid).
    """
    if isinstance(binding, Binding):
        if not binding.show or not binding.description:
            return None  # hidden bindings never bar-render (Footer contract)
        return (binding.key_display or binding.key, binding.description)
    if len(binding) >= 3 and binding[2]:
        return (binding[0], binding[2])
    return None


def keycaps_text(pairs, budget=None,
                 key_style: str = "bold", label_style: str = "dim") -> Text:
    """Render (key, label) pairs as ``[k]label`` keycaps, clipped.

    Keycaps join with single spaces in the given order; when ``budget``
    is set and the next keycap would exceed it, a trailing ellipsis
    renders and everything after drops (the D-15 clip policy — binding
    declarations are in importance order, so the clip drops the
    least-primary keycaps first). The key char renders with
    ``key_style``, the label with ``label_style`` (the migrated Footer
    treatment: accent key, muted label).

    Args:
        pairs: iterable of (display key, label) pairs.
        budget: the maximum cell width (None = no clipping).
        key_style: the rich style for the key char.
        label_style: the rich style for the label (and the ellipsis).

    Returns:
        Text: the assembled keycap line.
    """
    parts: list[Text] = []
    used = 0
    for key, label in pairs:
        keycap = Text.assemble(
            Text("["),
            Text(key, style=key_style),
            Text("]"),
            Text(label, style=label_style),
        )
        cost = keycap.cell_len + (1 if parts else 0)  # separator space
        if budget is not None and used + cost > budget:
            parts.append(Text("…", style=_ELLIPSIS_STYLE))
            break
        if parts:
            parts.append(Text(" "))
            used += 1
        parts.append(keycap)
        used += keycap.cell_len
    return Text.assemble(*parts) if parts else Text("")


class TopMenuBar(Horizontal):
    """The D-13 top menu bar: six slots, digit-prefixed, active marked.

    Composed by the base screens; the active slot is read from the
    screen's ``NAV_SLOT`` class attribute at mount (each screen owns its
    own bar instance — screens are switched, not restyled). Slot content
    is ``{digit}{label}`` with the placeholder suffix attached directly
    — the format that keeps the whole fixed vocabulary inside 80 columns.
    """

    def on_mount(self) -> None:
        """Mount the six slot Statics from NAV_SLOTS + the active slot."""
        active = getattr(self.screen, "NAV_SLOT", None)
        for position, slot in enumerate(NAV_SLOTS):
            segments: list[Text] = []
            if position:
                segments.append(Text(" "))  # single-space separator
            classes = "nav-slot"
            text = f"{slot.index}{slot.label}"
            if slot.index == active:
                segments.append(Text("◆ "))  # glyph channel first
                classes += " nav-slot-active"  # + bold/accent channels
            elif slot.phase is not None:
                text += NAV_PLACEHOLDER_SUFFIX
                classes += " nav-slot-placeholder"
            segments.append(Text(text))
            self.mount(Static(Text.assemble(*segments), classes=classes))


class KeycapsStatic(Static):
    """The bottom bar's left segment: keycaps clipped to its width.

    Re-clips on every resize (the terminal width is the budget); content
    is re-derived from the pairs and styles fixed at construction.
    """

    def __init__(self, pairs, key_style: str = "bold",
                 label_style: str = "dim", **kwargs) -> None:
        super().__init__("", **kwargs)
        self._pairs = tuple(pairs)
        self._key_style = key_style
        self._label_style = label_style

    def on_resize(self) -> None:
        """Re-clip to the new width (the D-15 clip policy)."""
        self.update(keycaps_text(
            self._pairs, budget=self.size.width,
            key_style=self._key_style, label_style=self._label_style,
        ))


class BottomBar(Horizontal):
    """The D-15 bottom submenu bar: left keycaps + constant right pair.

    The left segment consumes ``binding_row`` over the ACTIVE SCREEN's
    BINDINGS in declaration order (the same source the help modal uses);
    the right segment is the app-level pair (help first, then quit — the
    D-15 constant ordering). The key style is the live theme's accent,
    resolved once at mount.
    """

    def on_mount(self) -> None:
        """Mount the two segments from the screen's + app's bindings."""
        key_style = f"bold {self.app.current_theme.accent}"
        left_pairs = [
            row for row
            in map(binding_row, getattr(self.screen, "BINDINGS", []))
            if row is not None
        ]
        right_pairs = [
            row for row in map(binding_row, self.app.BINDINGS)
            if row is not None
        ]
        # the constant right-segment ordering: help keycap before quit
        right_pairs.sort(key=lambda pair: 0 if pair[0] == "?" else 1)
        self.mount(KeycapsStatic(
            left_pairs, key_style=key_style, id="nav-left-keycaps"))
        self.mount(Static(
            keycaps_text(right_pairs, key_style=key_style),
            id="nav-right-keycaps"))
