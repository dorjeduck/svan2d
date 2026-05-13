# Solar System Orrery

Animated solar system with planets orbiting the sun at their correct relative speeds.

## Run

```bash
python showcases/solar_system/orrery/main.py
```

## Scaling

Orbit distances and body sizes are scaled independently — each is internally proportional with no min/max clamping.

| Mode | Compression | Best for |
|------|-------------|----------|
| `"linear"` | None | Honest proportions |
| `"sqrt"` | Mild (power ½) | Balanced view |
| `"cbrt"` | Moderate (power ⅓) | Inner planets more visible |
| `"log"` | Aggressive (logarithmic) | Extreme range differences |

## Configuration

Edit `config.toml` to customize:

- **planets.show** — which planets to include
- **orbits.scaling** — how orbit distances are compressed
- **bodies.scaling** — how body sizes are compressed
- **bodies.max_radius_px** — pixel radius of the largest body (Sun)
- **animation.earth_orbits** — how many Earth years to simulate
- **sun** — color, glow opacity

## Output

Produces `output/solar_system_orrery.mp4` (1800 frames at 60fps = 30 seconds).
