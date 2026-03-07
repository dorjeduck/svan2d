from svan2d import (
    Color,
    configure_logging,
    ConverterType,
    easing,
    layout,
    Point2D,
    TextRenderer,
    TextState,
    VElement,
    VElementGroup,
    VElementGroupState,
    VScene,
    VSceneExporter,
)

configure_logging(level="INFO")

START_COLOR = Color("#FDBE02")
END_COLOR = Color("#AA0000")


def main():

    # Create the scene
    scene = VScene(width=256, height=256, background=Color("#000017"))

    # Create text states for each number with consistent styling
    states = [
        TextState(
            text=str(num),
            font_family="Courier New",
            font_size=20,
        )
        for num in range(1, 10)
    ]

    x_shifts = [-100, 60]

    all_states = [
        layout.line(states, center=Point2D(x_shift, 0), spacing=20, rotation=90)
        for x_shift in x_shifts
    ]

    # Create a text renderer for all numbers
    renderer = TextRenderer()

    # overriding the default easing for the x field for each element
    elements = [
        VElement(renderer=renderer)
        .attributes(
            easing_dict={"pos": easing.linear},
            keystates_dict={"fill_color": [START_COLOR, END_COLOR]},
        )
        .keystates(states)
        for states in zip(*all_states)
    ]

    g_start_state = VElementGroupState()
    g1_end_state = VElementGroupState(rotation=75, transform_origin_x=x_shifts[1] / 2)
    g2_end_state = VElementGroupState(rotation=-75, transform_origin_x=x_shifts[1] / 2)

    g1 = (
        VElementGroup(elements=elements[:4])
        .keystate(g_start_state, at=0)
        .keystate(g_start_state, at=0.5)
        .keystate(g1_end_state, at=1)
    )
    g2 = (
        VElementGroup(elements=elements[5:])
        .keystate(g_start_state, at=0)
        .keystate(g_start_state, at=0.5)
        .keystate(g2_end_state, at=1)
    )
    scene = scene.add_elements([g1, g2])

    # adding the middle element as it is not part of any group
    scene = scene.add_element(elements[4])

    # Create the exporter
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.PLAYWRIGHT_HTTP,
        output_dir="output/",
    )

    # Export to MP4 file
    exporter.to_mp4(
        filename="15_group_dynamics",
        total_frames=90,
        framerate=30,
        png_width_px=1024,
    )


if __name__ == "__main__":
    main()
