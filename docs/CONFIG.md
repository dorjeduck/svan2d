# Configuration

TOML-based configuration for project-wide defaults.

## Quick Start

Create `svan2d.toml` in your project directory:

```toml
[scene]
width = 1920
height = 1080

[state.visual]
fill_color = "#FDBE02"

[logging]
level = "DEBUG"
```

## File Locations (priority order)

1. `./svan2d.toml` (project)
2. `~/.config/svan2d/config.toml` (user)
3. `~/.svan2d.toml` (home)
4. Built-in defaults

## Configuration Sections

### `[scene]`

```toml
[scene]
width = 800
height = 800
background_color = "none"
origin_mode = "center"  # or "top-left"
```

### `[state]`

```toml
[state]
x = 0.0
y = 0.0
scale = 1.0
opacity = 1.0
rotation = 0.0
```

### `[state.visual]`

```toml
[state.visual]
fill_color = "none"
stroke_color = "none"
stroke_width = 1.0
num_vertices = 128
```

### `[morphing]`

```toml
[morphing]
vertex_loop_mapper = "clustering"  # clustering, hungarian, greedy, discrete, simple

[morphing.clustering]
balance_clusters = true
max_iterations = 50
random_seed = 42
```

| Strategy | Use Case |
|----------|----------|
| `clustering` | Balanced morphing (default) |
| `hungarian` | Optimal distance (requires scipy) |
| `greedy` | Fast, simple |
| `discrete` | Some move, some appear/disappear |
| `simple` | All disappear, all appear |

### `[playwright_server]`

```toml
[playwright_server]
host = "localhost"
port = 4000
auto_start = false
```

See [PLAYWRIGHT_SERVER.md](PLAYWRIGHT_SERVER.md).

### `[logging]`

```toml
[logging]
level = "INFO"  # DEBUG, INFO, WARNING, ERROR
```

## Color Formats

```toml
color = "#FF0000"     # Hex
color = [255, 0, 0]   # RGB array
color = "red"         # Name
color = "none"        # Transparent
```

## Programmatic Access

```python
from svan2d.config import get_config, load_config, reset_config

config = get_config()
width = config.get('scene.width')
load_config('custom.toml')
reset_config()
```

## Priority

Code values > loaded config > project config > user config > defaults

## See Also

- [HOLE_MATCHING.md](HOLE_MATCHING.md) - Morphing strategies
- [PLAYWRIGHT_SERVER.md](PLAYWRIGHT_SERVER.md) - Render server
