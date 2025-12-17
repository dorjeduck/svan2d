"""
Comprehensive showcase of all svan2d layout functions
Demonstrates each layout's unique characteristics with animated transitions
"""

from svan2d.component import TextRenderer, TextState
from svan2d.converter.converter_type import ConverterType
from svan2d import layout
from svan2d.core.logger import configure_logging
from svan2d.velement import VElement
from svan2d.transition import segments
from svan2d.vscene import VScene
from svan2d.vscene.vscene_exporter import VSceneExporter
from dataclasses import replace
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D

configure_logging(level="INFO")

# NOTE: This example is temporarily broken - animation module being redesigned


def main():
    # Create the scene
    scene = VScene(width=256, height=256, background=Color("#000017"))

    # Create text states for numbers 1-20 with consistent styling
    base_states = [
        TextState(
            text=f"{num:02}",
            font_family="Courier New",
            font_size=10,
            fill_color=Color("#FDBE02"),
        )
        for num in range(1, 21)
    ]

    base_name_state = TextState(
        text="",
        font_family="Courier New",
        font_size=14,
        fill_color=Color("#AA0000"),
        pos=Point2D(0, 110),
    )

    # Define all layout transitions
    layout_states = []
    layout_name_states = []

    # 1. Start: Grid layout
    layout_states.append(layout.grid(base_states, cols=5, spacing_h=20, spacing_v=20))
    layout_name_states.append(replace(base_name_state, text="Grid Layout"))

    # 2. Circle layout
    layout_states.append(
        layout.circle(base_states, radius=100, alignment=layout.ElementAlignment.LAYOUT)
    )
    layout_name_states.append(replace(base_name_state, text="Circle Layout"))

    # 3. Spiral layout
    layout_states.append(
        layout.spiral(
            base_states,
            start_radius=20,
            radius_step=5,
            angle_step=40,
            alignment=layout.ElementAlignment.LAYOUT,
        )
    )
    layout_name_states.append(replace(base_name_state, text="Spiral Layout"))

    # 4. Line layout (horizontal)
    layout_states.append(
        layout.line(
            base_states,
            spacing=13,
            rotation=40,
            alignment=layout.ElementAlignment.LAYOUT,
        )
    )
    layout_name_states.append(replace(base_name_state, text="Line Layout"))

    # 5. Wave layout
    layout_states.append(
        layout.wave(
            base_states,
            amplitude=25,
            wavelength=80,
            spacing=12,
            alignment=layout.ElementAlignment.LAYOUT,
        )
    )
    layout_name_states.append(replace(base_name_state, text="Wave Layout"))

    # 6. Ellipse layout
    layout_states.append(
        layout.ellipse(
            base_states,
            rx=110,
            ry=70,
            alignment=layout.ElementAlignment.LAYOUT,
        )
    )
    layout_name_states.append(replace(base_name_state, text="Ellipse Layout"))

    # 7. Polygon layout (hexagon)
    layout_states.append(
        layout.polygon(
            base_states,
            sides=5,
            radius=100,
            alignment=layout.ElementAlignment.LAYOUT,
        )
    )
    layout_name_states.append(replace(base_name_state, text="Polygon Layout"))

    # 8. Bezier curve layout
    layout_states.append(
        layout.bezier(
            base_states,
            control_points=[
                Point2D(-110, -80),
                Point2D(-60, 80),
                Point2D(60, -80),
                Point2D(110, 80),
            ],
            alignment=layout.ElementAlignment.LAYOUT,
        )
    )
    layout_name_states.append(replace(base_name_state, text="Bezier Layout"))

    # 9. Random scatter layout
    layout_states.append(
        layout.scatter(
            base_states,
            x_range=(-115, 115),
            y_range=(-115, 115),
            seed=42,
            alignment=layout.ElementAlignment.LAYOUT,
        )
    )
    layout_name_states.append(replace(base_name_state, text="Scatter Layout"))

    # 10. Path Points layout
    layout_states.append(
        layout.path_points(
            base_states,
            points=[
                Point2D(-110, -100),
                Point2D(-60, 0),
                Point2D(0, 60),
                Point2D(60, 0),
                Point2D(110, 100),
            ],
            smooth=True,
            alignment=layout.ElementAlignment.LAYOUT,
        )
    )
    layout_name_states.append(replace(base_name_state, text="Path Points Layout"))

    # 11. Radial grid layout
    layout_states.append(
        layout.radial_grid(
            base_states,
            rings=4,
            segments=5,
            ring_spacing=25,
            inner_radius=15,
            alignment=layout.ElementAlignment.LAYOUT,
        )
    )
    layout_name_states.append(replace(base_name_state, text="Radial Grid Layout"))

    # 12. Back to grid (closing the loop)
    layout_states.append(layout.grid(base_states, cols=5, spacing_h=20, spacing_v=20))
    layout_name_states.append(replace(base_name_state, text="Grid Layout"))

    # Create a text renderer
    renderer = TextRenderer()

    num_states = len(layout_states)

    hold_duration = 1 / (3 * num_states)
    fade_duration = 1 / (9 * num_states)

    elements = [
        VElement(renderer=renderer).segment(
            segments.hold(states, segments.linspace(len(states)), hold_duration)
        )
        for states in zip(*layout_states)
    ]

    # Add all elements to the scene
    scene.add_elements(elements)

    texts = VElement(renderer=renderer).segment(
        segments.fade_inout(
            layout_name_states,
            segments.linspace(num_states),
            hold_duration,
            fade_duration,
        )
    )

    scene.add_element(texts)

    # Create the exporter
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.PLAYWRIGHT,
        output_dir="output/",
    )

    # Export to MP4 file
    exporter.to_mp4(
        filename="21_layout_showcase.mp4",
        total_frames=len(layout_states) * 60,
        framerate=30,
        png_width_px=1024,
        num_thumbnails=100,
    )


if __name__ == "__main__":
    main()
