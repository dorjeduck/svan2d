from svan2d import (
    CameraState,
    CircleState,
    Color,
    ConverterType,
    Point2D,
    SquareState,
    VElement,
    VScene,
    VSceneExporter,
    configure_logging,
    easing,
)

configure_logging(level="INFO")

OUTER_COLOR = Color("#FDBE02")
CENTER_COLOR = Color("#AA0000")


def main():
    scene = (
        VScene(width=600, height=600, background=Color("#000017"))
        .camera_keystate(CameraState(scale=6.0), at=0.0)  # Start zoomed in
        .camera_transition(easing_dict={"scale": easing.out_quad})
        .camera_keystate(CameraState(scale=1.0), at=0.4)  # Zoom out
        .camera_keystate(CameraState(scale=1.0), at=0.6)  # Hold
        .camera_transition(  # Zoom back
            easing_dict={
                "scale": easing.in_out,
                "pos": easing.in_out,
            }
        )
        .camera_keystate(
            CameraState(scale=2.5, pos=Point2D(80, -80)),
            at=0.9,
        )
        .camera_keystate(
            CameraState(scale=2.5, pos=Point2D(80, -80)),
            at=1.0,
        )
    )

    # Create circles in a grid pattern
    elements = []
    for i in range(-2, 3):
        for j in range(-2, 3):
            dist = (i**2 + j**2) ** 0.5
            t = dist / (2 * 2**0.5)
            s1 = CircleState(
                radius=30,
                pos=Point2D(i * 80, j * 80),
                fill_color=CENTER_COLOR.interpolate(OUTER_COLOR, t),
            )

            s2 = SquareState(
                size=60,
                pos=Point2D(i * 80, j * 80),
                fill_color=CENTER_COLOR.interpolate(OUTER_COLOR, t),
            )

            elements.append(VElement().keystates([s1, s2]))

    # Multi-step zoom with camera_keystate()

    scene = scene.add_elements(elements)

    # Export
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.PLAYWRIGHT_HTTP,
        output_dir="output/",
    )

    exporter.to_mp4(
        filename="33_camera_zoom_keystates",
        total_frames=120,
        framerate=30,
        png_width_px=1024,
        num_thumbnails=100,
    )


if __name__ == "__main__":
    main()
