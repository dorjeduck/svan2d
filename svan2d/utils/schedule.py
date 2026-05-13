from collections.abc import Mapping
from enum import Enum


class OverlapMode(Enum):
    LEAD_IN = "lead_in"        # B starts early — A's end unchanged
    LEAD_OUT = "lead_out"      # A ends late — B's start unchanged
    SYMMETRIC = "symmetric"    # both adjust equally by overlap / 2


class WeightedSchedule:
    """Map named weights to (t_start, t_end) slots on a timeline.

    Weights are relative to each other and normalized to proportional fractions
    of the timeline range [t_start, t_end].

    Overlap — relay race model:
        Like runners in a relay race, the next animation (B) starts moving before
        the previous one (A) has fully finished. A's end point does not move —
        only B's start is pulled earlier. The total timeline length is preserved.
        In this class, `overlap` is the amount (in timeline units) by which the
        slots blend into each other, interpreted according to `mode`:

        LEAD_IN (default): B's start is pulled earlier by `overlap`. A's end unchanged.
        LEAD_OUT:          A's end is extended by `overlap`. B's start unchanged.
        SYMMETRIC:         A's end extends by `overlap / 2`, B's start pulls earlier
                           by `overlap / 2`.

    Args:
        weights:          Ordered dict of {name: weight}. Weights are relative.
        t_start:          Timeline start (default 0.0).
        t_end:            Timeline end (default 1.0).
        mode:             How overlap is applied (default OverlapMode.LEAD_IN).
        default_overlap:  Overlap amount in timeline units, applied to all slot
                          boundaries except the first, unless overridden via `overlaps`.
        overlaps:         Per-slot override of overlap amount, keyed by slot name (B).
                          Use 0.0 to explicitly suppress overlap for a specific slot.
                          Omit a key to use `default_overlap`.

    Example:
        schedule = WeightedSchedule(
            {"intro": 1, "main": 3, "outro": 1},
            t_end=0.8,
            default_overlap=0.05,
            overlaps={"main": 0.0},  # no overlap: main waits for intro to finish
        )
        start, end = schedule["main"]
    """

    def __init__(
        self,
        weights: Mapping[str, float],
        *,
        t_start: float = 0.0,
        t_end: float = 1.0,
        mode: OverlapMode = OverlapMode.LEAD_IN,
        default_overlap: float = 0.0,
        overlaps: Mapping[str, float] | None = None,
    ):
        self._t_start = t_start
        self._t_end = t_end
        self._mode = mode
        self._default_overlap = default_overlap
        self._overlaps: Mapping[str, float] = overlaps or {}
        self._slots = self._compute(weights, t_start, t_end, mode, default_overlap, self._overlaps)

    @staticmethod
    def _compute(
        weights: Mapping[str, float],
        t_start: float,
        t_end: float,
        mode: OverlapMode,
        default_overlap: float,
        overlaps: Mapping[str, float],
    ) -> dict[str, tuple[float, float]]:
        total = sum(weights.values())
        span = t_end - t_start
        slots: dict[str, tuple[float, float]] = {}
        cursor = 0.0

        for name, w in weights.items():
            size = (w / total) * span
            natural_start = t_start + cursor
            slot_start = natural_start

            if slots:
                overlap = overlaps.get(name, default_overlap)
                prev_name = next(reversed(slots))
                prev_start, prev_end = slots[prev_name]

                if mode == OverlapMode.LEAD_IN:
                    slot_start = natural_start - overlap
                elif mode == OverlapMode.LEAD_OUT:
                    slots[prev_name] = (prev_start, prev_end + overlap)
                elif mode == OverlapMode.SYMMETRIC:
                    slots[prev_name] = (prev_start, prev_end + overlap / 2)
                    slot_start = natural_start - overlap / 2

            slots[name] = (slot_start, natural_start + size)
            cursor += size

        return slots

    def slots(self) -> dict[str, tuple[float, float]]:
        return dict(self._slots)

    def __getitem__(self, key: str) -> tuple[float, float]:
        return self._slots[key]

    def print_slots(self) -> None:
        names = list(self._slots.keys())
        name_w = max(len(k) for k in names)

        print(
            f"WeightedSchedule  "
            f"mode={self._mode.name}  "
            f"t=[{self._t_start:.4f}, {self._t_end:.4f}]  "
            f"default_overlap={self._default_overlap:.4f}"
        )
        if self._overlaps:
            overrides = ", ".join(f"{k}={v:.4f}" for k, v in self._overlaps.items())
            print(f"  overlaps: {overrides}")

        header = f"{'name':<{name_w}}  {'t_start':>8}  {'t_end':>8}  {'duration':>9}  {'overlap':>9}"
        print(header)
        print("-" * len(header))

        for i, (name, (t_start, t_end)) in enumerate(self._slots.items()):
            if i == 0:
                overlap_str = "—"
            else:
                val = self._overlaps.get(name, self._default_overlap)
                marker = " *" if name in self._overlaps else ""
                overlap_str = f"{val:.4f}{marker}"
            print(f"{name:<{name_w}}  {t_start:>8.4f}  {t_end:>8.4f}  {t_end - t_start:>9.4f}  {overlap_str:>9}")
