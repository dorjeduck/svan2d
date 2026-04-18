

from svan2d.transition import easing
from svan2d import layout
from svan2d.core import (
    Color,
    Point2D,
    configure_logging,
)
from svan2d.converter import ConverterType
from svan2d.velement import VElement
from svan2d.vscene import (
    VScene,
    VSceneExporter,
)
from svan2d.primitive.state import TextState
from svan2d.primitive.renderer import TextRenderer
from svan2d.utils.stagger_schedule import (
    StaggerDirection,
    StaggerSchedule,
)
configure_logging(level="INFO")

n = 9

schedule = StaggerSchedule(
    n,
    t_start=0.1,
    t_end=0.9,
    overlap=0.4,
    direction=StaggerDirection.FROM_CENTER,
)

schedule.print_slots()

def main():
    scene = VScene(width=256, height=256, background=Color("#000017"))
    renderer = TextRenderer()

    base_states = [
        TextState(
            text=str(i + 1),
            font_family="Courier New",
            font_size=20,
            fill_color=Color("#FDBE02"),
        )
        for i in range(n)
    ]

    start_states = layout.line(
        base_states, center=Point2D(-100, 0), spacing=20, rotation=90
    )
    end_states = layout.line(
        base_states, center=Point2D(100, 0), spacing=20, rotation=90
    )

    for i in range(n):
        t_start, t_end = schedule[i]
        scene = scene.add_element(
            VElement(renderer)
            .attributes(easing_dict={"pos": easing.linear})
            .keystates(
                [start_states[i], end_states[i]],
                between=[t_start, t_end],
                extend=True,
            )
        )

    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.PLAYWRIGHT_HTTP,
        output_dir="output/",
    )
    exporter.to_mp4(
        filename="39_stagger_schedule_demo",
        total_frames=180,
        framerate=30,
        png_width_px=1024,
    )

if __name__ == "__main__":
    main()
