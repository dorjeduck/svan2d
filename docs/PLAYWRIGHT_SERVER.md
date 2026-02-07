# Playwright Render Server

HTTP service for high-quality SVG-to-PNG/PDF conversion using headless Chromium.

## Installation

```bash
pip install svan2d[playwright-server]
playwright install chromium
```

## Quick Start

```bash
# Start server
svan2d playwright-server start

# Use in code
from svan2d.vscene.vscene_exporter import VSceneExporter
from svan2d.converter.converter_type import ConverterType

exporter = VSceneExporter(scene, converter=ConverterType.PLAYWRIGHT_HTTP)
exporter.to_mp4(filename="animation", total_frames=90)
```

## CLI Commands

```bash
svan2d playwright-server start [--max-pages 8]
svan2d playwright-server stop
svan2d playwright-server status
svan2d playwright-server restart
svan2d playwright-server logs [-n 100]
```

## Configuration

```toml
[playwright_server]
host = "localhost"
port = 4000
max_pages = 4        # Browser pages for parallel rendering
auto_start = false   # Auto-start when needed
log_level = "INFO"
```

## Parallel Rendering

```python
exporter.to_mp4(
    filename="animation",
    total_frames=240,
    parallel_workers=8,  # Match max_pages
)
```

| RAM | Cores | max_pages | parallel_workers |
|-----|-------|-----------|------------------|
| 8GB | 4 | 4 | 4 |
| 16GB | 8 | 8 | 8 |
| 32GB | 16 | 12-16 | 12-16 |

## API

```bash
# Health check
curl http://localhost:4000/health

# Render
curl -X POST http://localhost:4000/render \
  -H "Content-Type: application/json" \
  -d '{"svg": "<svg>...</svg>", "type": "png", "width": 100, "height": 100}' \
  --output output.png
```

## When to Use

- **Playwright HTTP**: Service architecture, multi-app, lightweight main process
- **Playwright Local**: Simple scripts, one-off renders
- **CairoSVG**: Speed, simpler setup

## Troubleshooting

```bash
# Check port
lsof -i :4000

# Test health
curl http://localhost:4000/health

# View logs
svan2d playwright-server logs
```
