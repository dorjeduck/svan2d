import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING

from .base import Renderer

if TYPE_CHECKING:
    from ..state.raw_svg import RawSvgState

import drawsvg as dw


# Tags whose glyph/pixel orientation must stay upright: a plain Y-flip would
# mirror them. Geometry tags (path, line, polygon, circle, …) must flip.
_ORIENTATION_TAGS = ("text", "image")


def _counter_flip_orientation(svg_data: str) -> str:
    """Wrap every <text>/<image> in a local reflection so it reads upright
    after the element-level ``scale(1,-1)`` (applied by the base renderer for
    ``y_up`` states) has flipped the whole fragment.

    The fragment is assumed authored in a Y-up frame. The outer flip puts each
    node at the right screen position but mirrored; reflecting the node about
    its own anchor (text: its ``y``; image: its vertical centre) undoes the
    mirroring without moving it. Only the element tree is walked — path ``d``
    data is never parsed.
    """
    # Fragments have no single root; wrap so ElementTree can parse, then emit
    # the children back out. Assumes an un-namespaced SVG fragment (the form
    # svan2d/drawsvg produce), so tags stay unprefixed.
    root = ET.fromstring(f"<root>{svg_data}</root>")
    _wrap_orientation_children(root)
    return "".join(ET.tostring(child, encoding="unicode") for child in root)


def _wrap_orientation_children(parent: ET.Element) -> None:
    new_children: list[ET.Element] = []
    for child in list(parent):
        _wrap_orientation_children(child)
        if child.tag in _ORIENTATION_TAGS:
            y = float(child.get("y", 0) or 0)
            if child.tag == "image":
                # Reflect about the image's vertical centre so its box stays put.
                h = float(child.get("height", 0) or 0)
                axis = y + h / 2.0
            else:
                # Reflect about the text baseline.
                axis = y
            g = ET.Element("g")
            g.set("transform", f"translate(0,{2 * axis}) scale(1,-1)")
            g.append(child)
            new_children.append(g)
        else:
            new_children.append(child)
    for c in list(parent):
        parent.remove(c)
    for c in new_children:
        parent.append(c)


class RawSvgRenderer(Renderer):
    """
    Renderer that renders raw SVG data.

    Holds a one-slot cache of the last ``dw.Raw`` wrapper keyed on the
    identity of ``state.svg_data`` (and the ``y_up`` flag, which rewrites the
    payload). ``dw.Raw`` is immutable (just stores the string and writes it out
    verbatim), so sharing a wrapper across frames and drawings is safe and
    avoids allocating a new Raw per frame when the SVG payload hasn't changed —
    the common case for static SVG assets.

    When ``state.y_up`` is set, the base renderer reflects the whole fragment
    with ``scale(1,-1)`` (so its geometry shares the Y-up world frame); this
    renderer additionally counter-flips <text>/<image> nodes so they stay
    upright.
    """

    def __init__(self) -> None:
        self._cached_key: tuple[int, bool] | None = None
        self._cached_raw: dw.Raw | None = None

    def _render_core(
        self, state: "RawSvgState", drawing: dw.Drawing | None = None
    ) -> dw.Raw:
        key = (id(state.svg_data), bool(state.y_up))
        if key == self._cached_key and self._cached_raw is not None:
            return self._cached_raw
        svg_data = (
            _counter_flip_orientation(state.svg_data)
            if state.y_up
            else state.svg_data
        )
        raw = dw.Raw(svg_data)
        self._cached_key = key
        self._cached_raw = raw
        return raw
