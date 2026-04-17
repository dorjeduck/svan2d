from enum import Enum


class StaggerDirection(Enum):
    FORWARD = "forward"          # 0, 1, 2, … n-1
    REVERSE = "reverse"          # n-1, … 1, 0
    FROM_CENTER = "from_center"  # middle first, spreading outward
    FROM_EDGES = "from_edges"    # outer elements first, converging inward
    ALTERNATING = "alternating"  # 0, n-1, 1, n-2, …


def _stagger_positions(n: int, direction: StaggerDirection) -> list[int]:
    """Return positions[i] = stagger slot index (0 = first to animate) for element i."""
    if direction == StaggerDirection.FORWARD:
        return list(range(n))
    if direction == StaggerDirection.REVERSE:
        return list(range(n - 1, -1, -1))

    if direction == StaggerDirection.FROM_CENTER:
        center = (n - 1) / 2.0
        order = sorted(range(n), key=lambda i: abs(i - center))
    elif direction == StaggerDirection.FROM_EDGES:
        center = (n - 1) / 2.0
        order = sorted(range(n), key=lambda i: -abs(i - center))
    else:  # ALTERNATING
        order = []
        left, right = 0, n - 1
        while left <= right:
            order.append(left)
            if left != right:
                order.append(right)
            left += 1
            right -= 1

    positions = [0] * n
    for p, i in enumerate(order):
        positions[i] = p
    return positions


class StaggerSchedule:
    """Distribute N equal-duration animation slots across a timeline, staggered by index order.

    Each element gets the same animation duration. Elements start at evenly spaced
    offsets within [t_start, t_end]. The `overlap` parameter controls how much
    adjacent slots overlap: 0.0 means contiguous (no overlap), 0.5 means each slot
    starts halfway through the previous one.

    The `direction` controls which elements animate first via StaggerDirection.

    Args:
        n:           Number of elements.
        t_start:     Timeline start (default 0.0).
        t_end:       Timeline end (default 1.0).
        overlap:     Fraction of slot duration shared with the next slot (default 0.0).
        direction:   Order in which elements receive their stagger offset (default FORWARD).

    Example:
        schedule = StaggerSchedule(
            9,
            t_start=0.1,
            t_end=0.9,
            overlap=0.3,
            direction=StaggerDirection.FROM_CENTER,
        )
        t_start, t_end = schedule[i]
    """

    def __init__(
        self,
        n: int,
        *,
        t_start: float = 0.0,
        t_end: float = 1.0,
        overlap: float = 0.0,
        direction: StaggerDirection = StaggerDirection.FORWARD,
    ):
        self._n = n
        self._t_start = t_start
        self._t_end = t_end
        self._overlap = overlap
        self._direction = direction
        self._slots = self._compute(n, t_start, t_end, overlap, direction)

    @staticmethod
    def _compute(
        n: int,
        t_start: float,
        t_end: float,
        overlap: float,
        direction: StaggerDirection,
    ) -> list[tuple[float, float]]:
        span = t_end - t_start
        # solve: d * ((n-1) * (1 - overlap) + 1) = span
        d = span / ((n - 1) * (1 - overlap) + 1) if n > 1 else span
        delay = d * (1 - overlap)

        positions = _stagger_positions(n, direction)
        return [
            (t_start + positions[i] * delay, t_start + positions[i] * delay + d)
            for i in range(n)
        ]

    def __getitem__(self, index: int) -> tuple[float, float]:
        return self._slots[index]

    def print_slots(self) -> None:
        print(
            f"StaggerSchedule  n={self._n}  "
            f"direction={self._direction.name}  "
            f"t=[{self._t_start:.4f}, {self._t_end:.4f}]  "
            f"overlap={self._overlap:.4f}"
        )
        header = f"{'index':>5}  {'t_start':>8}  {'t_end':>8}  {'duration':>9}"
        print(header)
        print("-" * len(header))
        for i, (s, e) in enumerate(self._slots):
            print(f"{i:>5}  {s:>8.4f}  {e:>8.4f}  {e - s:>9.4f}")
