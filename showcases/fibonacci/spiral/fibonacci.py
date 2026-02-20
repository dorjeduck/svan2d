"""Fibonacci sequence, golden rectangle layout, and spiral geometry.

Pure math — no svan2d dependency. Computes fibonacci numbers, square
positions in the golden rectangle tiling, the SVG spiral path through
quarter-circle arcs, and parametric arc geometry for tip tracking.
"""

import math


def fibonacci_numbers(n: int) -> list[int]:
    """Generate first n Fibonacci numbers starting from 1, 1."""
    fibs = [1, 1]
    for _ in range(2, n):
        fibs.append(fibs[-1] + fibs[-2])
    return fibs[:n]


def compute_square_layout(
    fibs: list[int],
) -> tuple[list[dict], tuple[float, float, float, float]]:
    """Compute positions and sizes for Fibonacci squares.

    Each square is placed adjacent to the growing bounding rectangle,
    cycling through directions: right, up, left, down. Sizes are raw
    fibonacci numbers; the camera handles framing.

    Returns:
        (squares, bbox) where each square is a dict with
        size/left/top/right/bottom, and bbox is (left, top, right, bottom).
    """
    directions = [(1, 0), (0, -1), (-1, 0), (0, 1)]

    squares = []

    s0 = fibs[0]
    squares.append(
        {
            "size": s0,
            "left": 0,
            "top": 0,
            "right": s0,
            "bottom": s0,
        }
    )

    bbox_left = 0
    bbox_top = 0
    bbox_right = s0
    bbox_bottom = s0

    for i in range(1, len(fibs)):
        s = fibs[i]
        dx, dy = directions[i % 4]

        if dx == 1:  # right
            left = bbox_right
            top = bbox_bottom - s
            right = left + s
            bottom = bbox_bottom
        elif dy == -1:  # up
            left = bbox_right - s
            top = bbox_top - s
            right = bbox_right
            bottom = bbox_top
        elif dx == -1:  # left
            left = bbox_left - s
            top = bbox_top
            right = bbox_left
            bottom = top + s
        else:  # down (dy == 1)
            left = bbox_left
            top = bbox_bottom
            right = left + s
            bottom = top + s

        squares.append(
            {
                "size": s,
                "left": left,
                "top": top,
                "right": right,
                "bottom": bottom,
            }
        )

        bbox_left = min(bbox_left, left)
        bbox_top = min(bbox_top, top)
        bbox_right = max(bbox_right, right)
        bbox_bottom = max(bbox_bottom, bottom)

    return squares, (bbox_left, bbox_top, bbox_right, bbox_bottom)


def center_layout(
    bbox: tuple[float, float, float, float],
) -> tuple[float, float]:
    """Compute offsets to center the layout around origin (0, 0)."""
    bx, by, bx2, by2 = bbox
    mid_x = (bx + bx2) / 2
    mid_y = (by + by2) / 2
    return -mid_x, -mid_y


def compute_spiral_path(all_squares: list[dict]) -> str:
    """Build SVG path with quarter-circle arcs through the Fibonacci squares.

    Each arc is a 90-degree quarter circle. The first arc starts at the
    opposite diagonal corner; subsequent arcs chain from the previous
    arc's endpoint, producing proper quarter circles (chord = r*sqrt(2)).
    """
    if not all_squares:
        return ""

    arc_geo = compute_arc_geometry(all_squares)
    parts = []

    start = arc_geo[0]["start"]
    parts.append(f"M {start[0]},{start[1]}")

    for i, geo in enumerate(arc_geo):
        r = all_squares[i]["size"]
        end = geo["end"]
        parts.append(f"A {r},{r} 0 0 0 {end[0]},{end[1]}")

    return " ".join(parts)


def arc_start(sq: dict, d: int) -> tuple[float, float]:
    """Return the opposite diagonal corner for a quarter-circle arc (only used for i=0)."""
    if d == 0:
        return (sq["left"], sq["bottom"])
    elif d == 1:
        return (sq["right"], sq["bottom"])
    elif d == 2:
        return (sq["right"], sq["top"])
    else:
        return (sq["left"], sq["top"])


def arc_end(sq: dict, d: int) -> tuple[float, float]:
    """Return the end point for an arc."""
    if d == 0:
        return (sq["right"], sq["top"])
    elif d == 1:
        return (sq["left"], sq["top"])
    elif d == 2:
        return (sq["left"], sq["bottom"])
    else:
        return (sq["right"], sq["bottom"])


def arc_corner(sq: dict, d: int) -> tuple[float, float]:
    """Return the pivot corner of the square for a quarter-circle arc.

    The arc center is always a corner of the square.
    """
    if d == 0:
        return (sq["right"], sq["bottom"])
    elif d == 1:
        return (sq["left"], sq["bottom"])
    elif d == 2:
        return (sq["left"], sq["top"])
    else:
        return (sq["right"], sq["top"])


# Start angle and sweep per direction — fixed by the golden spiral geometry.
# Every arc is a quarter circle (π/2). No trig needed.
_ARC_START_ANGLES = (math.pi, 0.0, 0.0, math.pi)
_ARC_SWEEPS = (math.pi / 2, -math.pi / 2, math.pi / 2, -math.pi / 2)


def compute_arc_geometry(all_squares: list[dict]) -> list[dict]:
    """Compute parametric arc geometry for each square in the spiral.

    Each arc is a 90-degree quarter circle. Returns start/end points and
    center/angle params for parametric evaluation (tip tracking).

    Each result dict has:
        start: (x, y) arc start point
        end: (x, y) arc end point
        arc_params: (cx, cy, r, start_angle, sweep)
    """
    results = []
    for i, sq in enumerate(all_squares):
        d = i % 4
        start = arc_start(sq, d) if i == 0 else arc_end(all_squares[i - 1], (i - 1) % 4)
        cx, cy = arc_corner(sq, d)
        results.append({
            "start": start,
            "end": arc_end(sq, d),
            "arc_params": (cx, cy, sq["size"], _ARC_START_ANGLES[d], _ARC_SWEEPS[d]),
        })
    return results


def compute_cumulative_bboxes(
    all_squares: list[dict],
) -> list[tuple[float, float, float, float]]:
    """Compute cumulative bounding box after each square is added."""
    cum_left = all_squares[0]["left"]
    cum_top = all_squares[0]["top"]
    cum_right = all_squares[0]["right"]
    cum_bottom = all_squares[0]["bottom"]

    bboxes = []
    for sq in all_squares:
        cum_left = min(cum_left, sq["left"])
        cum_top = min(cum_top, sq["top"])
        cum_right = max(cum_right, sq["right"])
        cum_bottom = max(cum_bottom, sq["bottom"])
        bboxes.append((cum_left, cum_top, cum_right, cum_bottom))
    return bboxes


