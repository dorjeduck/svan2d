# Playwright Render Server

The Playwright Render Server is an optional HTTP service that provides high-quality SVG-to-PNG/PDF conversion using Playwright's headless Chromium browser.

## Overview

While Svan2D includes several built-in converters (CairoSVG, Inkscape, local Playwright), the HTTP-based Playwright server offers:

- **Best rendering quality**: Uses real Chromium browser for pixel-perfect output
- **Lightweight Python process**: Offloads heavy rendering work to separate server process
- **Background operation**: Runs as a daemon, doesn't block your Python process
- **Cross-platform**: Works on Linux, macOS, and Windows
- **Optional auto-start**: Can automatically start when needed
- **Easy management**: Simple CLI commands for control

**Performance Note:** The HTTP server provides similar wall-clock rendering times to local Playwright, but significantly reduces CPU usage in your main Python process (typically 85-95% reduction). This makes it ideal for service architectures, multi-app environments, or when you need your main process to remain responsive. For detailed performance analysis, see **[BENCHMARK.md](BENCHMARK.md)**.

## Installation

### 1. Install Server Dependencies

```bash
pip install svan2d[playwright-server]
```

This installs:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `playwright` - Browser automation
- `psutil` - Process management
- `click` - CLI framework

### 2. Install Chromium Browser

```bash
playwright install chromium
```

This downloads the Chromium browser used for rendering.

## Quick Start

### Manual Server Management (Default)

```bash
# Start the server
svan2d playwright-server start

# Check status
svan2d playwright-server status

# Stop the server
svan2d playwright-server stop
```

Then use it in your code:

```python
from svan2d.vscene import VScene
from svan2d.vscene.vscene_exporter import VSceneExporter
from svan2d.converter.converter_type import ConverterType

scene = VScene(width=800, height=800)
# ... add elements ...

exporter = VSceneExporter(scene, converter=ConverterType.PLAYWRIGHT_HTTP)
exporter.to_mp4(
    filename="animation",
    total_frames=90,
    parallel_workers=4,  # Use parallel rendering
)
```

### Auto-Start Mode (Optional)

Enable auto-start in your `svan2d.toml`:

```toml
[playwright_server]
auto_start = true
```

Now the server starts automatically when needed:

```python
# No need to manually start the server!
exporter.export("output.png", converter="playwright_http")
```

## CLI Commands

### Start Server

```bash
svan2d playwright-server start
```

Starts the server in the background. Output:
```
✓ Playwright server started successfully
  Host: localhost
  Port: 4000
  Max pages: 4
  PID file: ~/.svan2d/playwright-server.pid
  Log file: ~/.svan2d/playwright-server.log
```

**With custom page pool size:**
```bash
svan2d playwright-server start --max-pages 8
# or
svan2d playwright-server start -p 8
```

The `max_pages` setting controls how many browser pages are kept in the pool for parallel rendering.

### Stop Server

```bash
svan2d playwright-server stop
```

Gracefully stops the running server.

### Check Status

```bash
svan2d playwright-server status
```

Shows detailed status:
```
✓ Playwright server is running
  PID: 12345
  Uptime: 3600.5s
  Memory: 45.2 MB
  Host: localhost
  Port: 4000
```

### Restart Server

```bash
svan2d playwright-server restart
```

Stops then starts the server (useful after config changes).

**With new max_pages setting:**
```bash
svan2d playwright-server restart --max-pages 8
```

### View Logs

```bash
svan2d playwright-server logs           # Last 50 lines
svan2d playwright-server logs -n 100    # Last 100 lines
```

## Configuration

Configure the server in `svan2d.toml`:

```toml
[playwright_server]
host = "localhost"       # Server host (default: localhost)
port = 4000             # Server port (default: 4000)
max_pages = 4           # Browser pages in pool for parallel rendering (default: 4)
auto_start = false      # Auto-start if not running (default: false)
log_level = "INFO"      # Log level: DEBUG, INFO, WARNING, ERROR
```

The `max_pages` setting can also be overridden via CLI: `--max-pages 8`

## Advanced Usage

### Programmatic Control

```python
from svan2d.server.playwright.process_manager import ProcessManager

# Create manager
manager = ProcessManager(host="localhost", port=4000)

# Start server
if not manager.is_running():
    manager.start()

# Get detailed status
status = manager.status()
print(f"Server running: {status['running']}")
print(f"Uptime: {status['uptime_seconds']}s")
print(f"Memory: {status['memory_mb']} MB")

# Stop server
manager.stop()
```

### Custom Host/Port

```python
from svan2d.converter.playwright_http_svg_converter import PlaywrightHttpSvgConverter

# Connect to custom server
converter = PlaywrightHttpSvgConverter(host="localhost", port=5000)
```

Or via config:

```toml
[playwright_server]
host = "0.0.0.0"  # Listen on all interfaces
port = 5000       # Custom port
```

### Explicit Auto-Start Control

```python
# Force auto-start regardless of config
converter = PlaywrightHttpSvgConverter(auto_start=True)

# Disable auto-start regardless of config
converter = PlaywrightHttpSvgConverter(auto_start=False)
```

## Running as System Service

### Linux (systemd)

Create `/etc/systemd/system/svan2d-playwright-server.service`:

```ini
[Unit]
Description=Svan2D Playwright Render Server
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser
ExecStart=/usr/bin/python -m uvicorn svan2d.server.playwright.render_server:app --host localhost --port 4000
Restart=always
RestartSec=5
Environment=PATH=/home/youruser/.local/bin:/usr/bin

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable svan2d-playwright-server
sudo systemctl start svan2d-playwright-server
sudo systemctl status svan2d-playwright-server
```

### macOS (launchd)

Create `~/Library/LaunchAgents/com.svan2d.playwright-server.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.svan2d.playwright-server</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>-m</string>
        <string>uvicorn</string>
        <string>svan2d.server.playwright.render_server:app</string>
        <string>--host</string>
        <string>localhost</string>
        <string>--port</string>
        <string>4000</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/svan2d-playwright-server.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/svan2d-playwright-server.err</string>
</dict>
</plist>
```

Load service:

```bash
launchctl load ~/Library/LaunchAgents/com.svan2d.playwright-server.plist
launchctl start com.svan2d.playwright-server
```

### Windows (NSSM - Non-Sucking Service Manager)

1. Download NSSM from https://nssm.cc/
2. Install as service:

```cmd
nssm install Svan2DPlaywrightServer "C:\Python311\python.exe" "-m uvicorn svan2d.server.playwright.render_server:app --host localhost --port 4000"
nssm set Svan2DPlaywrightServer AppDirectory "C:\Users\YourUser"
nssm start Svan2DPlaywrightServer
```

## Troubleshooting

### Server Won't Start

**Check if port is in use:**
```bash
# Linux/macOS
lsof -i :4000

# Windows
netstat -ano | findstr :4000
```

**Check logs:**
```bash
svan2d playwright-server logs
```

**Try running directly:**
```bash
python -m uvicorn svan2d.server.playwright.render_server:app --host localhost --port 4000
```

### Connection Refused

**Verify server is running:**
```bash
svan2d playwright-server status
```

**Test health endpoint:**
```bash
curl http://localhost:4000/health
```

Should return: `{"status":"ok","service":"playwright-render-server"}`

### Rendering Fails

**Check Chromium is installed:**
```bash
playwright install chromium
```

**Verify permissions:**
- Linux: May need `--no-sandbox` flag (already included)
- Docker: Requires additional dependencies

**Check server logs:**
```bash
svan2d playwright-server logs -n 200
```

### Auto-Start Not Working

**Verify config:**
```python
from svan2d.config import get_config
config = get_config()
print(config.get("playwright_server.auto_start"))  # Should be True
```

**Check for errors:**
Enable debug logging in `svan2d.toml`:

```toml
[logging]
level = "DEBUG"
```

### High Memory Usage

Chromium instances can use significant memory. The server closes browsers after each render, but if you're doing high-volume rendering, consider:

1. **Restart periodically:**
   ```bash
   svan2d playwright-server restart
   ```

2. **Monitor memory:**
   ```bash
   svan2d playwright-server status
   ```

3. **Run in Docker** with memory limits

## Docker Deployment

Example `Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Svan2D with playwright-server
RUN pip install svan2d[playwright-server]

# Install Chromium
RUN playwright install chromium --with-deps

# Expose port
EXPOSE 4000

# Run server
CMD ["uvicorn", "svan2d.server.playwright.render_server:app", "--host", "0.0.0.0", "--port", "4000"]
```

Build and run:

```bash
docker build -t svan2d-playwright-server .
docker run -p 4000:4000 svan2d-playwright-server
```

## API Reference

### Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "ok",
  "service": "playwright-render-server",
  "pool": {
    "pages_created": 4,
    "max_pages": 4,
    "pages_available": 4
  }
}
```

The `pool` object shows:
- `pages_created`: Number of browser pages currently in the pool
- `max_pages`: Maximum pages allowed (set via `--max-pages`)
- `pages_available`: Pages currently idle (0 = all pages busy rendering)

### Render SVG

**Endpoint:** `POST /render`

**Request:**
```json
{
  "svg": "<svg>...</svg>",
  "type": "png",
  "width": 1920,
  "height": 1080
}
```

**Parameters:**
- `svg` (string, required): SVG content to render
- `type` (string, required): Output format - `"png"` or `"pdf"`
- `width` (integer, required): Output width in pixels
- `height` (integer, required): Output height in pixels

**Response:** Binary PNG or PDF data

**Example with curl:**
```bash
curl -X POST http://localhost:4000/render \
  -H "Content-Type: application/json" \
  -d '{
    "svg": "<svg width=\"100\" height=\"100\"><circle cx=\"50\" cy=\"50\" r=\"40\" fill=\"red\"/></svg>",
    "type": "png",
    "width": 100,
    "height": 100
  }' \
  --output output.png
```

## Parallel Rendering

The server maintains a pool of browser pages that can process multiple render requests concurrently. Combined with client-side parallel workers, this significantly speeds up batch exports.

### How It Works

Export happens in two phases:
1. **Phase 1 (Sequential)**: Generate SVG content for all frames (state interpolation)
2. **Phase 2 (Parallel)**: Convert SVGs to PNGs using multiple concurrent HTTP requests

### Usage

```python
exporter = VSceneExporter(
    scene=scene,
    converter=ConverterType.PLAYWRIGHT_HTTP,
    output_dir="output/",
)

exporter.to_mp4(
    filename="animation",
    total_frames=240,
    parallel_workers=8,  # Send 8 concurrent requests to server
)
```

### Recommended Settings

| Hardware | max_pages | parallel_workers |
|----------|-----------|------------------|
| 8GB RAM, 4 cores | 4 | 4 |
| 16GB RAM, 8 cores (e.g., M2) | 8 | 8 |
| 32GB RAM, 16 cores | 12-16 | 12-16 |

**Rule of thumb:**
- Set `max_pages` ≈ number of CPU cores
- Set `parallel_workers` = `max_pages`
- Each page uses ~100-150MB RAM

### Monitoring

Check page pool utilization during rendering:

```bash
curl http://localhost:4000/health
```

Response includes pool stats:
```json
{
  "status": "ok",
  "service": "playwright-render-server",
  "pool": {
    "pages_created": 8,
    "max_pages": 8,
    "pages_available": 0
  }
}
```

When `pages_available` drops to 0 during export, all pages are being utilized.

### Benchmark Results

Typical speedups with parallel rendering (100 elements, 90 frames):

| Configuration | Time | Speedup |
|---------------|------|---------|
| Sequential (parallel_workers=0) | 13.7s | 1.0x |
| Parallel (parallel_workers=4) | 8.8s | 1.56x |

For complex scenes where Phase 1 dominates, speedups may be lower since only Phase 2 benefits from parallelization.

## Performance Tips

1. **Keep server running**: Starting/stopping frequently adds overhead
2. **Use auto-start for dev**: Convenient for development workflows
3. **Manual start for production**: More control and predictability
4. **Monitor logs**: Watch for errors or warnings
5. **Batch renders**: If doing many renders, keep server alive between them
6. **Match parallel_workers to max_pages**: No benefit from more workers than pages
7. **Monitor with /health endpoint**: Check page pool utilization during renders

## Comparison with Other Converters

| Feature | Playwright HTTP | Playwright Local | CairoSVG | Inkscape |
|---------|----------------|------------------|----------|----------|
| Quality | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Wall-Clock Speed | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| Process CPU Load | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Setup | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| Fonts | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Background | ✅ | ❌ | ❌ | ❌ |
| Multi-App | ✅ | ❌ | ❌ | ❌ |

**Use Playwright HTTP when:**
- Building service/microservice architectures
- Multiple applications need rendering
- You need your main process to stay lightweight (85-95% less CPU)
- Running long-lived applications that need to stay responsive
- Distributed systems (render on different machine)

**Use Playwright Local when:**
- Simple single-script batch rendering
- One-off render jobs
- Want minimal complexity (no server management)
- Can't run background services

**Use other converters when:**
- You want simpler setup (CairoSVG)
- You need maximum speed (CairoSVG)
- Lower quality is acceptable

## See Also

- [BENCHMARK.md](BENCHMARK.md) - Performance comparison benchmark
- [CONFIG.md](CONFIG.md) - Configuration reference
- [Examples](examples/) - Code examples
- [Playwright Documentation](https://playwright.dev/python/) - Playwright Python docs
