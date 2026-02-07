# Development Server

Live browser preview with hot-reload.

## Installation

```bash
pip install svan2d[devserver]
```

## Quick Start

```bash
svan2d serve my_animation.py
```

Opens `http://localhost:8000` with auto-reload on file save.

## Animation File

```python
# my_animation.py
from svan2d.vscene import VScene
from svan2d.velement import VElement
from svan2d.component.state import CircleState

scene = VScene(width=400, height=400)
scene = scene.add_element(VElement().keystates([start, end]))
```

Auto-detection finds any `VScene` instance. For multiple scenes, use `@animation`:

```python
from svan2d.server.dev import animation

@animation
def main():
    return VScene(...)
```

## CLI Options

```bash
svan2d serve <file.py> [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--port`, `-p` | 8000 | Server port |
| `--frames`, `-n` | 20 | Preview frames |
| `--fps`, `-f` | 10 | Playback FPS |
| `--no-browser` | | Don't auto-open |

```bash
svan2d serve my_animation.py --frames 60 --fps 30
```

## Configuration

```toml
[devserver]
port = 8000
default_frames = 20
default_fps = 10
auto_open_browser = true
```

## Export

Browser UI includes export buttons for MP4, GIF, and HTML.

## Features

- Hot-reload on save (200ms debounce)
- Errors displayed in browser
- WebSocket-based updates
- Play/pause controls
