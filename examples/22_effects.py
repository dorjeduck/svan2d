from dataclasses import replace

from svan2d import (
    CheckerboardPattern,
    CircleState,
    Color,
    configure_logging,
    ConverterType,
    DropShadowFilter,
    GradientStop,
    LinearGradient,
    Point2D,
    SquareState,
    VElement,
    VScene,
    VSceneExporter,
)

configure_logging(level="INFO")

START_COLOR_1 = Color("#FDBE02")
END_COLOR_1 = Color("#AA0000")

START_COLOR_2 = Color("#00AAAA")
END_COLOR_2 = Color("#0000FF")

# Create the scene
scene = VScene(width=256, height=256, background=Color("#000017"))

linear_grad_1 = LinearGradient(
    Point2D(0, -50),
    Point2D(0, 50),
    stops=(
        GradientStop(0.0, START_COLOR_1),
        GradientStop(1.0, END_COLOR_1),
    ),
)

linear_grad_2 = replace(
    linear_grad_1,
    stops=(
        GradientStop(0.0, START_COLOR_2),
        GradientStop(1.0, END_COLOR_2),
    ),
)

shadow_filter_1 = DropShadowFilter(dx=3, dy=3, std_deviation=3, color=START_COLOR_1)
shadow_filter_2 = replace(shadow_filter_1, color=END_COLOR_1)

checker_pattern_1 = CheckerboardPattern(
    square_size=5, color1=Color("#34495e"), color2=Color("#ffffff")
)

checker_pattern_2 = replace(checker_pattern_1, square_size=25, color1=Color("#ff0000"))

start_states = [
    SquareState(size=40, pos=Point2D(-70, -70), fill_gradient=linear_grad_1),
    SquareState(size=40, pos=Point2D(-70, 0), fill_pattern=checker_pattern_1),
    SquareState(
        size=40, pos=Point2D(-70, 70), fill_color=START_COLOR_1, filter=shadow_filter_1
    ),
]


end_states = [
    CircleState(radius=20, pos=Point2D(70, -70), fill_gradient=linear_grad_2),
    CircleState(radius=20, pos=Point2D(70, 0), fill_pattern=checker_pattern_2),
    CircleState(
        radius=20, pos=Point2D(70, 70), fill_color=END_COLOR_1, filter=shadow_filter_2
    ),
]

elements = [VElement().keystates([s1, s2]) for s1, s2 in zip(start_states, end_states)]

# Add all elements to the scene
scene = scene.add_elements(elements)

# Create the exporter
exporter = VSceneExporter(
    scene=scene,
    converter=ConverterType.PLAYWRIGHT,
    output_dir="output/",
)

# Export to mp4
exporter.to_mp4(
    filename="29_effects",
    total_frames=60,
    framerate=30,
    png_width_px=1024,
    num_thumbnails=100,
)
