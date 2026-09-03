"""Advance widths for text that has to be positioned before it is rendered.

Anything that types itself in character by character cannot be centre-anchored:
a centred string grows outward from its own middle and slides sideways as it
fills, which reads as a fragment materialising rather than as someone typing.
The cure is to anchor it at its left edge and put that edge where the *finished*
line will start — which means knowing the finished line's width up front.

There is no way to ask the rasterizer, so the width is computed from the font
itself: the sum of the glyph advances, plus the letter-spacing the SVG will add.
The font file is found through fontconfig, the same mechanism the browser uses to
resolve a family name, so the two agree by construction.
"""

from __future__ import annotations

import subprocess
from functools import lru_cache
from pathlib import Path

from fontTools.ttLib import TTFont


@lru_cache(maxsize=None)
def _font_file(font_family: str, font_weight: str) -> Path:
    """Ask fontconfig for the file backing a family name.

    fc-match always answers — it falls back to some installed font rather than
    failing — so the answer is checked against the family that was asked for. A
    silent fallback would give advances for the wrong typeface and put every
    label a few pixels off with nothing to show why.
    """
    pattern = f"{font_family}:weight={font_weight}"
    try:
        out = subprocess.run(
            ["fc-match", "-f", "%{file}\t%{family}", pattern],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except FileNotFoundError as exc:
        raise RuntimeError(
            "fc-match not found — fontconfig is needed to resolve font files for "
            "text measurement"
        ) from exc

    path_str, _, families = out.partition("\t")
    if font_family.lower() not in families.lower():
        raise RuntimeError(
            f"font '{font_family}' is not installed — fontconfig fell back to "
            f"'{families.strip()}'. Install it, or the rendered text will not "
            f"match the measured width."
        )
    return Path(path_str)


@lru_cache(maxsize=None)
def _advances(font_family: str, font_weight: str) -> tuple[dict[int, int], int, int]:
    font = TTFont(_font_file(font_family, font_weight), fontNumber=0)
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    widths = {ch: hmtx[cmap[ch]][0] for ch in cmap if cmap[ch] in hmtx.metrics}
    fallback = hmtx[".notdef"][0] if ".notdef" in hmtx.metrics else 0
    return widths, font["head"].unitsPerEm, fallback


def text_width(
    text: str,
    font_family: str,
    font_size: float,
    letter_spacing: float = 0.0,
    font_weight: str = "normal",
) -> float:
    """Rendered advance width of `text`, in pixels.

    Letter-spacing is counted once per character rather than once per gap: SVG
    adds it after every glyph, the last one included, and that trailing space is
    part of the advance width the renderer centres on. Measuring the gaps only
    would leave a centred line off by half a space.
    """
    widths, upm, fallback = _advances(font_family, font_weight)
    units = sum(widths.get(ord(ch), fallback) for ch in text)
    return units / upm * font_size + letter_spacing * len(text)
