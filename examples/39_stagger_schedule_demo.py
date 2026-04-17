from svan2d import (
    Color,
    configure_logging,
    ConverterType,
    easing,
    layout,
    Point2D,
    StaggerDirection,
    StaggerSchedule,
    TextRenderer,
    TextState,
    VElement,
    VScene,
    VSceneExporter,
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
                [start_states[i], start_states[i], end_states[i], end_states[i]],
                at=[0.0, t_start, t_end, 1.0],
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
