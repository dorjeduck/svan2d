"""Pure encoding functions for MP4 and GIF export."""

from pathlib import Path


def encode_mp4(frames_dir: Path, output_path: Path, fps: int) -> None:
    """Encode MP4 from PNG frames using ffmpeg.

    Args:
        frames_dir: Directory containing frame_NNNN.png files.
        output_path: Output MP4 file path.
        fps: Frames per second.
    """
    import subprocess

    cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(fps),
        "-i",
        str(frames_dir / "frame_%04d.png"),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(output_path),
    ]

    subprocess.run(cmd, check=True, capture_output=True)


def encode_gif(
    frames_dir: Path, output_path: Path, total_frames: int, fps: int
) -> None:
    """Encode GIF from PNG frames using Pillow.

    Args:
        frames_dir: Directory containing frame_NNNN.png files.
        output_path: Output GIF file path.
        total_frames: Total number of frames to read.
        fps: Frames per second (determines frame duration).
    """
    try:
        from PIL import Image
    except ImportError:
        raise RuntimeError("Pillow required for GIF export")

    frames = []
    for i in range(total_frames):
        frame_path = frames_dir / f"frame_{i:04d}.png"
        if frame_path.exists():
            frames.append(Image.open(frame_path))

    duration_ms = int(1000 / fps)
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=0,
        optimize=True,
    )
