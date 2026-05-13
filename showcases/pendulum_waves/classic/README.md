# Pendulum Waves

15 pendulums swing with slightly different frequencies, creating mesmerizing traveling wave and convergence patterns. Each pendulum completes a different integer number of oscillations over the animation, so they start and end in perfect alignment.

## Features Demonstrated

- `interpolation_dict`: custom Point2D interpolation for bob positions
- `state_interpolation`: full state computation for arm elements
- `Color.interpolate`: smooth color gradient across the pendulum row

## Run

```bash
python showcases/pendulum_waves/classic/main.py
```

## Config

Edit `config.toml` to change the number of pendulums, arm length, swing angle, oscillation count, colors, and export settings.
