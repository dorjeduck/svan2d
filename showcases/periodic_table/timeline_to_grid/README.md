# Periodic Table Timeline to Grid

Two-phase animation: elements first appear along a horizontal timeline axis ordered by discovery year, then fly to their periodic table grid positions. A PCHIP-interpolated camera zooms in on the first elements and smoothly zooms out as more appear along the timeline.

## Run

```bash
python showcases/periodic_table/timeline_to_grid/main.py
```

## Config

Edit `config.toml` to change colors, fonts, animation timing, and export settings.

## Dependencies

- scipy (PchipInterpolator for camera zoom)
