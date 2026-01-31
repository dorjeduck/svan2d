# Svan2D PNG Converter Benchmark Results

**Generated:** 2026-01-31 08:51:53

**Frames rendered:** 50

## Performance Comparison

| Converter | Parallel | Total Time | Per Frame | CPU % | CPU Time | Memory |
|-----------|----------|------------|-----------|-------|----------|--------|
| cairosvg | - | 0.57s | 0.011s | 89.4% | 0.75s | 127.7MB |
| inkscape | - | 19.11s | 0.382s | 0.8% | 0.19s | 132.2MB |
| playwright | - | 43.64s | 0.873s | 2.1% | 1.06s | 137.3MB |
| playwright_http | - | 2.48s | 0.050s | 3.4% | 0.11s | 116.5MB |
| playwright_http | 4 | 0.85s | 0.017s | 7.8% | 0.10s | 116.7MB |

## Detailed Metrics

### cairosvg

- **Total Time:** 0.57s
- **Average Time per Frame:** 0.011s
- **Process CPU Usage:** 89.4%
- **User CPU Time:** 0.70s
- **System CPU Time:** 0.05s
- **Total CPU Time:** 0.75s
- **Memory Usage:** 127.7MB

### inkscape

- **Total Time:** 19.11s
- **Average Time per Frame:** 0.382s
- **Process CPU Usage:** 0.8%
- **User CPU Time:** 0.03s
- **System CPU Time:** 0.16s
- **Total CPU Time:** 0.19s
- **Memory Usage:** 132.2MB

### playwright

- **Total Time:** 43.64s
- **Average Time per Frame:** 0.873s
- **Process CPU Usage:** 2.1%
- **User CPU Time:** 0.67s
- **System CPU Time:** 0.39s
- **Total CPU Time:** 1.06s
- **Memory Usage:** 137.3MB

### playwright_http

- **Total Time:** 2.48s
- **Average Time per Frame:** 0.050s
- **Process CPU Usage:** 3.4%
- **User CPU Time:** 0.07s
- **System CPU Time:** 0.04s
- **Total CPU Time:** 0.11s
- **Memory Usage:** 116.5MB

### playwright_http (parallel=4)

- **Total Time:** 0.85s
- **Average Time per Frame:** 0.017s
- **Parallel Workers:** 4
- **Process CPU Usage:** 7.8%
- **User CPU Time:** 0.06s
- **System CPU Time:** 0.04s
- **Total CPU Time:** 0.10s
- **Memory Usage:** 116.7MB

