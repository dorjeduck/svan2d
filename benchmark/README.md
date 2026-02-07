# PNG Converter Benchmark

Compares CairoSVG, Inkscape, Playwright (local), and Playwright HTTP Server.

## Quick Start

```bash
python benchmark/run_benchmark.py              # 50 frames (default)
python benchmark/run_benchmark.py -n 100       # 100 frames
python benchmark/run_benchmark.py --no-cleanup # Keep generated files
```

Generates console output + `BENCHMARK_RESULTS.md` with detailed metrics.

## Svan2D PNG Converter Benchmark Results

**Generated:** 2026-01-31

**Frames rendered:** 50

## Performance Comparison

| Converter | Parallel | Total Time | Per Frame | CPU % | CPU Time | Memory |
|-----------|----------|------------|-----------|-------|----------|--------|
| cairosvg | - | 0.57s | 0.011s | 89.4% | 0.75s | 127.7MB |
| inkscape | - | 19.11s | 0.382s | 0.8% | 0.19s | 132.2MB |
| playwright | - | 43.64s | 0.873s | 2.1% | 1.06s | 137.3MB |
| playwright_http | - | 2.48s | 0.050s | 3.4% | 0.11s | 116.5MB |
| playwright_http | 4 | 0.85s | 0.017s | 7.8% | 0.10s | 116.7MB |

## Converter Trade-offs

| Converter | Speed | Quality | Process CPU | Setup |
|-----------|-------|---------|-------------|-------|
| **CairoSVG** | Fastest | Good (font limits) | High | `pip install cairosvg` |
| **Playwright HTTP** | Very Fast | Best | Low | `pip install svan2d[playwright-server]` |
| **Inkscape** | Slow | Good | Low | Download from inkscape.org |
| **Playwright** | Slowest | Best | Moderate | `pip install playwright` |

**Recommendation:** Use **Playwright HTTP** for the best combination of speed and quality. With parallel rendering, it approaches CairoSVG speeds while delivering browser-accurate rendering.

## Options

```bash
-n FRAMES       # Number of frames (default: 50)
--no-cleanup    # Keep generated PNG files
-o OUTPUT       # Custom markdown output file (default: BENCHMARK_RESULTS.md)
```

## Notes

- Benchmark auto-skips converters that aren't installed
- Edit `create_test_scene()` in `run_benchmark.py` to test with custom graphics
- Playwright HTTP requires server running: `svan2d playwright-server start`
