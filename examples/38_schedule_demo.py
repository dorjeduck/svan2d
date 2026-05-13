

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
from svan2d.utils.schedule import (
    OverlapMode,
    WeightedSchedule,
)
configure_logging(level="INFO")

# weights control relative duration of each slot.

n = 9
weights = {str(i): (n + 1 - i) for i in range(1, n + 1)}

# all even numbers start only when the previous stops
overlaps = {str(i): 0.0 for i in range(2, n + 1, 2)}

overlaps["3"] = 0.14

schedule = WeightedSchedule(
    weights,
    t_end=0.9,  # all numbers in place by 85% of the animation, then hold
    mode=OverlapMode.LEAD_IN,
    default_overlap=0.07,
    overlaps=overlaps,
)

schedule.print_slots()

def main():
    scene = VScene(width=256, height=256, background=Color("#000017"))
    renderer = TextRenderer()

    base_states = [
        TextState(
            text=label,
            font_family="Courier New",
            font_size=20,
            fill_color=Color("#FDBE02"),
        )
        for label in weights.keys()
    ]

    start_states = layout.line(
        base_states, center=Point2D(-100, 0), spacing=20, rotation=90
    )
    end_states = layout.line(
        base_states, center=Point2D(100, 0), spacing=20, rotation=90
    )

    for i, (label, _) in enumerate(weights.items()):
        t_start, t_end = schedule[label]
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
        filename="38_schedule_demo",
        total_frames=180,
        framerate=30,
        png_width_px=1024,
    )

if __name__ == "__main__":
    main()
