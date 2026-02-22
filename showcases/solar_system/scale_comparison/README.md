# Planet Scale Comparison

Two-phase animation comparing the true sizes of all 8 planets and the Sun.

**Phase 1:** Planets start at equal sizes, then animate to their true relative radii — revealing the dramatic difference between rocky and gas giant planets.

**Phase 2:** The Sun slides in from above while planets shrink and move down, showing just how massive the Sun is compared to even Jupiter.

## Run

```bash
python showcases/solar_system/scale_comparison/main.py
```

## Configuration

Edit `config.toml` to customize:

- **planets.size.max_radius_px** — Jupiter's pixel radius in phase 1
- **sun.radius_px** — Sun's pixel radius in phase 2 (planets scale proportionally)
- **sun.padding_top / gap_to_planets** — vertical layout of the final state
- **animation.phase1_start/end, phase2_start/end** — timing (0–1)
- **planets.labels** — font, size, color, vertical offset

## Output

Produces `output/planet_scale_comparison.mp4` (450 frames at 30fps = 15 seconds).
