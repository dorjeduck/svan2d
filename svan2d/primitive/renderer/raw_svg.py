from typing import TYPE_CHECKING

from .base import Renderer

if TYPE_CHECKING:
    from ..state.raw_svg import RawSvgState

import drawsvg as dw


class RawSvgRenderer(Renderer):
    """
    Renderer that renders raw SVG data.

    Holds a one-slot cache of the last ``dw.Raw`` wrapper keyed on the
    identity of ``state.svg_data``. ``dw.Raw`` is immutable (just stores the
    string and writes it out verbatim), so sharing a wrapper across frames
    and drawings is safe and avoids allocating a new Raw per frame when the
    SVG payload hasn't changed — the common case for static SVG assets.
    """

    def __init__(self) -> None:
        self._cached_svg_data_id: int | None = None
        self._cached_raw: dw.Raw | None = None

    def _render_core(
        self, state: "RawSvgState", drawing: dw.Drawing | None = None
    ) -> dw.Raw:
        sd_id = id(state.svg_data)
        if sd_id == self._cached_svg_data_id and self._cached_raw is not None:
            return self._cached_raw
        raw = dw.Raw(state.svg_data)
        self._cached_svg_data_id = sd_id
        self._cached_raw = raw
        return raw
