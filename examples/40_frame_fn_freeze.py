"""Staggered settle times — each element flips its own `is_final` flag.

Five circles each drive their position via `frame_fn`. Their settle times
are spread across the timeline; once a circle stops moving it returns a
state with `is_final=True`. From that moment VScene treats the rendered
fragment as immutable — later frames pay nothing for the settled circles
while the still-moving ones continue to recompute.

Useful pattern when a procedural callable is the natural way to drive an
element (physics, random walks, easing curves outside the keystate model)
and the user knows when it stops varying.
"""

import math
from dataclasses import replace

from svan2d.core import Color, Point2D, configure_logging
from svan2d.converter import ConverterType
from svan2d.primitive.renderer import CircleRenderer
from svan2d.primitive.state import CircleState
from svan2d.velement import VElement
from svan2d.vscene import VScene, VSceneExporter

configure_logging(level="INFO")


def make_drifter(start_y: float, settle_t: float) -> tuple[VElement, CircleState]:
    base = CircleState(
        pos=Point2D(-100, start_y),
        radius=10,
        fill_color=Color("#FDBE02"),
    )
    target_x = 100.0

    def drift(state: CircleState, t: float) -> CircleState:
        if t >= settle_t:
            return replace(state, pos=Point2D(target_x, start_y), is_final=True)
        local_t = t / settle_t
        # ease-out cubic for visible deceleration before settle
        eased = 1.0 - (1.0 - local_t) ** 3
        x = -100 + (target_x - -100) * eased
        return replace(state, pos=Point2D(x, start_y))

    elem = VElement().renderer(CircleRenderer()).frame_fn(drift, base_state=base)
    return elem, base


def main():
    scene = VScene(width=320, height=320, background=Color("#000017"))

    settle_times = [0.2, 0.35, 0.5, 0.7, 0.9]
    y_positions = [-100, -50, 0, 50, 100]

    elements = [
        make_drifter(start_y=y, settle_t=st)[0]
        for y, st in zip(y_positions, settle_times)
    ]

    scene = scene.add_elements(elements)

    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.PLAYWRIGHT_HTTP,
        output_dir="output/",
    )

    exporter.to_mp4(
        filename="40_frame_fn_freeze",
        total_frames=90,
        framerate=30,
        png_width_px=1024,
    )


if __name__ == "__main__":
    main()
