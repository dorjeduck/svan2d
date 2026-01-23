"""
Benchmark: Point2D creation strategies

Compares:
1. Frozen Point2D (current) - new object each time
2. Mutable pooled points - reuse objects from pool
3. NumPy arrays - batch operations

Usage:
    python benchmark_point2d_pool.py [num_points] [num_frames]

    Defaults: 10000 points, 100 frames

Example (simulating 60fps, 128 vertices, 20 elements, 10 seconds):
    python benchmark_point2d_pool.py 153600 600
"""

import gc
import sys
import time
from dataclasses import dataclass
from typing import Callable

# Optional numpy support
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


# =============================================================================
# APPROACH 1: Frozen Point2D (current implementation)
# =============================================================================

@dataclass(slots=True, frozen=True)
class FrozenPoint2D:
    x: float = 0.0
    y: float = 0.0


def benchmark_frozen(num_points: int, num_frames: int) -> list:
    """Simulate animation: create new frozen points each frame."""
    results = []
    for frame in range(num_frames):
        t = frame / num_frames
        frame_points = []
        for i in range(num_points):
            # Simulate lerp: create new point
            x = i * (1 - t) + (i + 1) * t
            y = i * (1 - t) + (i - 1) * t
            frame_points.append(FrozenPoint2D(x, y))
        results.append(frame_points[-1])  # Keep one to prevent full optimization
    return results


# =============================================================================
# APPROACH 2: Mutable Point2D with Pool
# =============================================================================

@dataclass(slots=True)
class MutablePoint2D:
    x: float = 0.0
    y: float = 0.0


class Point2DPool:
    __slots__ = ("pool", "size", "index")

    def __init__(self, size: int):
        self.pool = [MutablePoint2D(0.0, 0.0) for _ in range(size)]
        self.size = size
        self.index = 0

    def reset(self):
        """Call at start of each frame."""
        self.index = 0

    def get(self, x: float, y: float) -> MutablePoint2D:
        """Get a point from pool, growing if needed."""
        i = self.index
        if i >= self.size:
            # Grow pool
            old_size = self.size
            self.pool.extend(MutablePoint2D(0.0, 0.0) for _ in range(old_size))
            self.size = old_size * 2

        self.index = i + 1
        point = self.pool[i]
        point.x = x
        point.y = y
        return point


def benchmark_pooled(num_points: int, num_frames: int) -> list:
    """Simulate animation: reuse points from pool each frame."""
    pool = Point2DPool(num_points)
    results = []
    for frame in range(num_frames):
        pool.reset()
        t = frame / num_frames
        frame_points = []
        for i in range(num_points):
            x = i * (1 - t) + (i + 1) * t
            y = i * (1 - t) + (i - 1) * t
            frame_points.append(pool.get(x, y))
        results.append((frame_points[-1].x, frame_points[-1].y))
    return results


# =============================================================================
# APPROACH 3: NumPy Arrays (batch operations)
# =============================================================================

def benchmark_numpy(num_points: int, num_frames: int) -> list:
    """Simulate animation: use numpy arrays for batch operations."""
    if not HAS_NUMPY:
        return []

    # Pre-allocate arrays (reused each frame)
    xs = np.zeros(num_points, dtype=np.float64)
    ys = np.zeros(num_points, dtype=np.float64)
    indices = np.arange(num_points, dtype=np.float64)

    results = []
    for frame in range(num_frames):
        t = frame / num_frames
        # Vectorized lerp
        np.multiply(indices, 1 - t, out=xs)
        np.add(xs, (indices + 1) * t, out=xs)
        np.multiply(indices, 1 - t, out=ys)
        np.add(ys, (indices - 1) * t, out=ys)
        results.append((xs[-1], ys[-1]))
    return results


# =============================================================================
# BENCHMARK RUNNER
# =============================================================================

def run_benchmark(
    name: str,
    func: Callable,
    num_points: int,
    num_frames: int,
    warmup_runs: int = 2,
    timed_runs: int = 5,
) -> dict:
    """Run benchmark with warmup and multiple timed runs."""

    # Warmup
    for _ in range(warmup_runs):
        gc.collect()
        func(num_points, num_frames)

    # Timed runs
    times = []
    gc_counts = []

    for _ in range(timed_runs):
        gc.collect()
        gc_before = gc.get_count()

        start = time.perf_counter()
        result = func(num_points, num_frames)
        end = time.perf_counter()

        gc_after = gc.get_count()

        times.append(end - start)
        gc_counts.append(sum(gc_after) - sum(gc_before))

    return {
        "name": name,
        "min_time": min(times),
        "max_time": max(times),
        "avg_time": sum(times) / len(times),
        "avg_gc_delta": sum(gc_counts) / len(gc_counts),
        "total_points": num_points * num_frames,
        "points_per_sec": (num_points * num_frames) / (sum(times) / len(times)),
    }


def format_result(result: dict, baseline_time: float = None) -> str:
    """Format benchmark result for display."""
    lines = [
        f"\n{'=' * 50}",
        f"  {result['name']}",
        f"{'=' * 50}",
        f"  Time (avg):     {result['avg_time']*1000:>10.2f} ms",
        f"  Time (min/max): {result['min_time']*1000:>10.2f} / {result['max_time']*1000:.2f} ms",
        f"  Points/sec:     {result['points_per_sec']:>10,.0f}",
        f"  GC delta (avg): {result['avg_gc_delta']:>10.1f}",
    ]

    if baseline_time and baseline_time != result['avg_time']:
        speedup = baseline_time / result['avg_time']
        lines.append(f"  Speedup:        {speedup:>10.2f}x vs frozen")

    return "\n".join(lines)


def main():
    # Parse arguments
    num_points = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
    num_frames = int(sys.argv[2]) if len(sys.argv) > 2 else 100

    total_creations = num_points * num_frames

    print("\n" + "=" * 60)
    print("  POINT2D POOLING BENCHMARK")
    print("=" * 60)
    print(f"  Points per frame:  {num_points:,}")
    print(f"  Number of frames:  {num_frames:,}")
    print(f"  Total point ops:   {total_creations:,}")
    print("=" * 60)

    # Run benchmarks
    results = []

    print("\nRunning Frozen Point2D benchmark...")
    frozen_result = run_benchmark("Frozen Point2D (current)", benchmark_frozen, num_points, num_frames)
    results.append(frozen_result)

    print("Running Pooled MutablePoint2D benchmark...")
    pooled_result = run_benchmark("Pooled MutablePoint2D", benchmark_pooled, num_points, num_frames)
    results.append(pooled_result)

    if HAS_NUMPY:
        print("Running NumPy arrays benchmark...")
        numpy_result = run_benchmark("NumPy Arrays", benchmark_numpy, num_points, num_frames)
        results.append(numpy_result)
    else:
        print("(NumPy not available, skipping array benchmark)")

    # Print results
    baseline_time = frozen_result['avg_time']
    for result in results:
        print(format_result(result, baseline_time))

    # Summary
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)

    pooled_speedup = baseline_time / pooled_result['avg_time']
    print(f"  Pooled vs Frozen: {pooled_speedup:.2f}x speedup")

    if HAS_NUMPY:
        numpy_speedup = baseline_time / numpy_result['avg_time']
        print(f"  NumPy vs Frozen:  {numpy_speedup:.2f}x speedup")

    # Time saved per 10-second animation at 60fps
    animation_frames = 600
    animation_points = num_points
    frozen_time_per_anim = (frozen_result['avg_time'] / num_frames) * animation_frames
    pooled_time_per_anim = (pooled_result['avg_time'] / num_frames) * animation_frames
    time_saved = frozen_time_per_anim - pooled_time_per_anim

    print(f"\n  For {animation_frames}-frame animation with {num_points:,} points/frame:")
    print(f"    Frozen:  {frozen_time_per_anim*1000:>8.1f} ms")
    print(f"    Pooled:  {pooled_time_per_anim*1000:>8.1f} ms")
    print(f"    Saved:   {time_saved*1000:>8.1f} ms ({time_saved/frozen_time_per_anim*100:.1f}%)")

    print("\n")


if __name__ == "__main__":
    main()
