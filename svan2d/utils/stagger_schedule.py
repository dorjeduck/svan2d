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
    offsets within [t_start, t_end]. Two ways to control the slot duration:

    - `overlap`: fraction of slot duration shared with the next slot (0.0 = contiguous,
      0.5 = each slot starts halfway through the previous one). Slot duration is derived
      from overlap and the window span.

    - `slot_duration`: explicit duration for each element's animation in timeline units.
      Overlap is derived internally. Use this when you want a fixed animation length
      regardless of n (e.g. always 50% of the total window).

    Exactly one of `overlap` or `slot_duration` may be supplied. Default is overlap=0.0.

    The `direction` controls which elements animate first via StaggerDirection.

    Args:
        n:             Number of elements.
        t_start:       Timeline start (default 0.0).
        t_end:         Timeline end (default 1.0).
        overlap:       Fraction of slot duration overlapping with the next (default 0.0).
        slot_duration: Fixed duration for each element's slot in timeline units.
        direction:     Order in which elements receive their stagger offset (default FORWARD).

    Examples:
        # Fixed overlap — slot duration scales with n:
        schedule = StaggerSchedule(9, t_start=0.1, t_end=0.9, overlap=0.3)

        # Fixed slot duration — overlap scales with n:
        schedule = StaggerSchedule(365, t_end=1.0, slot_duration=0.5)

        t_start, t_end = schedule[i]
    """

    def __init__(
        self,
        n: int,
        *,
        t_start: float = 0.0,
        t_end: float = 1.0,
        overlap: float | None = None,
        slot_duration: float | None = None,
        direction: StaggerDirection = StaggerDirection.FORWARD,
    ):
        if overlap is not None and slot_duration is not None:
            raise ValueError("supply either overlap or slot_duration, not both")

        span = t_end - t_start

        if slot_duration is not None:
            if n > 1 and slot_duration >= span:
                raise ValueError("slot_duration must be less than the total span")
            resolved_overlap = 1.0 - slot_duration * (n - 1) / span if n > 1 else 0.0
        else:
            resolved_overlap = overlap if overlap is not None else 0.0

        self._n = n
        self._t_start = t_start
        self._t_end = t_end
        self._overlap = resolved_overlap
        self._slot_duration = slot_duration
        self._direction = direction
        self._slots = self._compute(n, t_start, t_end, resolved_overlap, direction)

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
        if self._slot_duration is not None:
            param_str = f"slot_duration={self._slot_duration:.4f}"
        else:
            param_str = f"overlap={self._overlap:.4f}"
        print(
            f"StaggerSchedule  n={self._n}  "
            f"direction={self._direction.name}  "
            f"t=[{self._t_start:.4f}, {self._t_end:.4f}]  "
            f"{param_str}"
        )
        header = f"{'index':>5}  {'t_start':>8}  {'t_end':>8}  {'duration':>9}"
        print(header)
        print("-" * len(header))
        for i, (s, e) in enumerate(self._slots):
            print(f"{i:>5}  {s:>8.4f}  {e:>8.4f}  {e - s:>9.4f}")
