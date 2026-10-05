"""Tests for streaming Skia frames straight into ffmpeg.

The streamed video must be the one the PNG route makes, frame for frame.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

pytest.importorskip("skia")
if shutil.which("ffmpeg") is None:
    pytest.skip("ffmpeg not installed", allow_module_level=True)

from svan2d.converter.converter_type import ConverterType
from svan2d.core import Color
from svan2d.core.point2d import Point2D
from svan2d.primitive.state.circle import CircleState
from svan2d.velement import VElement
from svan2d.vscene import VScene, VSceneExporter


def _scene() -> VScene:
    # Half-transparent on a transparent canvas, so a premultiplied hand-over
    # would show up as different frames.
    start = CircleState(radius=20, pos=Point2D(-40, 0), fill_color=Color("#f80"), opacity=0.5)
    return VScene(width=128, height=96).add_element(
        VElement().keystate(start, at=0.0).keystate(
            CircleState(radius=40, pos=Point2D(40, 0), fill_color=Color("#08f"), opacity=0.5),
            at=1.0,
        )
    )


def _frames(video: str) -> list[str]:
    """Each decoded frame's checksum."""
    out = subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-i", video, "-f", "framemd5", "-"],
        capture_output=True, text=True, check=True,
    ).stdout
    return [line.rsplit(",", 1)[-1].strip() for line in out.splitlines() if not line.startswith("#")]


def _exporter(tmp_path: Path) -> VSceneExporter:
    return VSceneExporter(_scene(), output_dir=str(tmp_path), converter=ConverterType.SKIA)


@pytest.mark.integration
def test_streamed_video_matches_png_route(tmp_path):
    exporter = _exporter(tmp_path)
    streamed = exporter.to_mp4("streamed", total_frames=12, framerate=12)
    # Keeping the frame files takes the PNG route.
    via_png = exporter.to_mp4(
        "via_png", total_frames=12, framerate=12, cleanup_intermediate_files=False
    )
    assert (tmp_path / "via_png_frames").is_dir()
    assert not (tmp_path / "streamed_frames").exists()
    frames = _frames(streamed)
    assert len(frames) == 12
    assert frames == _frames(via_png)


@pytest.mark.integration
def test_streamed_time_range_makes_its_frames(tmp_path):
    video = _exporter(tmp_path).to_mp4(
        "part", total_frames=11, framerate=10, time_range=(0.5, 1.0)
    )
    assert len(_frames(video)) == 6  # frames at 0.5, 0.6, ... 1.0


@pytest.mark.integration
def test_streamed_video_writes_thumbnails(tmp_path):
    _exporter(tmp_path).to_mp4("thumbs", total_frames=9, framerate=9, num_thumbnails=3)
    written = sorted(p.name for p in (tmp_path / "thumbs_thumbnails").iterdir())
    assert written == ["thumbnail_0000.png", "thumbnail_0004.png", "thumbnail_0008.png"]
