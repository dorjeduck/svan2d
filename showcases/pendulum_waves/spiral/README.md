# Spiral Pendulum Waves

Pendulums placed along an Archimedean spiral, swinging radially outward. Frequency increases along the spiral arm, and the `freq_inward` option can reverse this so the fastest pendulums are at the center.

## Features Demonstrated

- `interpolation_dict`: custom Point2D interpolation for bob positions
- `state_interpolation`: full state computation for arm elements
- Archimedean spiral layout with configurable turns and radii
- `Color.interpolate`: smooth color gradient along the spiral

## Run

```bash
python showcases/pendulum_waves/spiral/main.py
```

## Config

Edit `config.toml` to change the number of pendulums, spiral turns, inner/outer radius, frequency direction, colors, and export settings.
