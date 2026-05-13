# Double Ring Pendulum Waves

Two concentric rings of pendulums swing radially outward with independently configured frequencies. The inner and outer rings are offset so their pendulums interleave, creating layered wave interference patterns.

## Features Demonstrated

- `interpolation_dict`: custom Point2D interpolation for bob positions
- `state_interpolation`: full state computation for arm elements
- `Color.interpolate`: independent color gradients per ring

## Run

```bash
python showcases/pendulum_waves/double_ring/main.py
```

## Config

Edit `config.toml` to change per-ring settings (count, radius, arm length, colors) and shared export settings.
