# 100m Sprint Race Replay

Side-view lane animations replaying the top 3 finishers from 5 Olympic 100m finals (2008 Beijing through 2024 Paris), stacked vertically for direct visual comparison.

## How It Works

- **Split-time data** for each runner is embedded directly in `data_prep.py`
- **PCHIP interpolation** maps real split times to smooth distance-over-time curves
- **Normalized timeline** — all 5 races animate over the same duration (the slowest final time), so faster finishers visibly reach the finish line sooner
- **VSceneComposite** stacks 5 race scenes vertically into a single output

## Running

```bash
# From the project root
python showcases/sprint_100m/race/main.py
```

Output: `output/sprint_100m.mp4`

## Files

| File | Purpose |
|------|---------|
| `main.py` | Scene composition & MP4 export |
| `data_prep.py` | Embedded split data + PCHIP interpolation |
| `runner_elements.py` | Animated runner circles + name labels |
| `track_elements.py` | Lane backgrounds, distance markers, finish line, title, clock |
| `config.toml` | All styling constants and export settings |

## Data Sources

Split times sourced from World Athletics and Olympic broadcast timing data for the men's 100m finals at Beijing 2008, London 2012, Rio 2016, Tokyo 2020, and Paris 2024.
