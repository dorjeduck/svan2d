# Grid Pendulum Waves

Pendulums arranged in a 2D grid with frequency varying by both row and column. The two frequency gradients create 2D wave interference patterns as pendulums shift in and out of phase across both axes.

## Features Demonstrated

- `interpolation_dict`: custom Point2D interpolation for bob positions
- `state_interpolation`: full state computation for arm elements
- 2D frequency gradient creating interference patterns
- `Color.interpolate`: smooth color gradient across the grid

## Run

```bash
python showcases/pendulum_waves/grid/main.py
```

## Config

Edit `config.toml` to change grid dimensions, row/column frequency steps, arm length, swing angle, colors, and export settings.
