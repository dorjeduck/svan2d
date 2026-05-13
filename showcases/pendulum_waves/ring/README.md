# Ring Pendulum Waves

Pendulums arranged in a circle, each swinging radially outward with slightly different frequencies. The wave patterns rotate and converge around the ring as the frequency differences create phase shifts.

## Features Demonstrated

- `interpolation_dict`: custom Point2D interpolation for bob positions
- `state_interpolation`: full state computation for arm elements
- `Color.interpolate`: smooth color gradient around the ring

## Run

```bash
python showcases/pendulum_waves/ring/main.py
```

## Config

Edit `config.toml` to change the number of pendulums, circle radius, arm length, swing angle, oscillation count, colors, and export settings.
