# Svan2D PNG Converter Benchmark Results

**Generated:** 2026-01-23 22:12:40

**Frames rendered:** 50

## Performance Comparison

| Converter | Parallel | Total Time | Per Frame | CPU % | CPU Time | Memory |
|-----------|----------|------------|-----------|-------|----------|--------|
| cairosvg | - | 0.58s | 0.012s | 89.2% | 0.78s | 129.0MB |
| inkscape | - | 19.52s | 0.390s | 0.8% | 0.19s | 132.5MB |
| playwright | - | 43.30s | 0.866s | 2.0% | 1.03s | 137.8MB |
| playwright_http | - | 1.99s | 0.040s | 4.3% | 0.11s | 139.1MB |
| playwright_http | 4 | 0.84s | 0.017s | 7.7% | 0.10s | 139.3MB |

## Detailed Metrics

### cairosvg

- **Total Time:** 0.58s
- **Average Time per Frame:** 0.012s
- **Process CPU Usage:** 89.2%
- **User CPU Time:** 0.72s
- **System CPU Time:** 0.06s
- **Total CPU Time:** 0.78s
- **Memory Usage:** 129.0MB

### inkscape

- **Total Time:** 19.52s
- **Average Time per Frame:** 0.390s
- **Process CPU Usage:** 0.8%
- **User CPU Time:** 0.03s
- **System CPU Time:** 0.16s
- **Total CPU Time:** 0.19s
- **Memory Usage:** 132.5MB

### playwright

- **Total Time:** 43.30s
- **Average Time per Frame:** 0.866s
- **Process CPU Usage:** 2.0%
- **User CPU Time:** 0.65s
- **System CPU Time:** 0.38s
- **Total CPU Time:** 1.03s
- **Memory Usage:** 137.8MB

### playwright_http

- **Total Time:** 1.99s
- **Average Time per Frame:** 0.040s
- **Process CPU Usage:** 4.3%
- **User CPU Time:** 0.07s
- **System CPU Time:** 0.04s
- **Total CPU Time:** 0.11s
- **Memory Usage:** 139.1MB

### playwright_http (parallel=4)

- **Total Time:** 0.84s
- **Average Time per Frame:** 0.017s
- **Parallel Workers:** 4
- **Process CPU Usage:** 7.7%
- **User CPU Time:** 0.06s
- **System CPU Time:** 0.04s
- **Total CPU Time:** 0.10s
- **Memory Usage:** 139.3MB

