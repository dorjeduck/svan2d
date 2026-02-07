from svan2d.core.color import Color

from config import COLOR_ONE, COLOR_PRIME, COLOR_COMPOSITE


def ring_to_total_number(ring: int):
    return (2 * ring + 1) ** 2


def get_spiral_position(n: int) -> tuple[int, int]:
    """Return (x, y) grid coordinates for number n (1-indexed) in Ulam spiral.

    The spiral starts at (0, 0) and winds counter-clockwise:
    1→(0,0), 2→(1,0), 3→(1,-1), 4→(0,-1), 5→(-1,-1), 6→(-1,0), 7→(-1,1), ...
    """
    if n == 1:
        return (0, 0)

    # Find which ring/layer this number is in
    # Ring k contains numbers from (2k-1)^2 + 1 to (2k+1)^2
    k = 0
    while (2 * k + 1) ** 2 < n:
        k += 1

    # Position within the ring
    ring_start = (2 * k - 1) ** 2 + 1 if k > 0 else 2
    pos_in_ring = n - ring_start
    side_length = 2 * k

    # Start position for this ring (right side, one above center)
    x, y = k, -k + 1

    # Walk around the ring
    if pos_in_ring < side_length:  # Going up (right side)
        y += pos_in_ring
    elif pos_in_ring < 2 * side_length:  # Going left (top side)
        y = k
        x = k - (pos_in_ring - side_length + 1)
    elif pos_in_ring < 3 * side_length:  # Going down (left side)
        x = -k
        y = k - (pos_in_ring - 2 * side_length + 1)
    else:  # Going right (bottom side)
        x = -k + (pos_in_ring - 3 * side_length + 1)
        y = -k

    return (x, y)
