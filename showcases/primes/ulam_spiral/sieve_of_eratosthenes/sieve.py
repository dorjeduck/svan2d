import sys
from enum import Enum, auto


class NumberStatus(Enum):
    CANDIDATE = auto()
    PRIME = auto()
    SIEVE_PRIME = auto()  # act as sieve prime at this step
    COMPOSITE = auto()


class Sieve:
    def __init__(self, x):
        self.limit = x
        self.is_candidate = [True] * (x + 1)
        self.status_map = {
            i: {
                "status": NumberStatus.CANDIDATE,
                "identified_at_step": None,
                "sieve_prime_at_step": None,  # Active: When it sifts others
                "by_prime": None,
            }
            for i in range(x + 1)
        }

        # Step 0: Definitions
        for i in [0, 1]:
            if i <= x:
                self.is_candidate[i] = False
                self.status_map[i].update(
                    {"status": NumberStatus.COMPOSITE, "identified_at_step": 0}
                )

        self.p = 2
        self.current_step = 0
        self.is_complete = False

    def step(self):
        if self.is_complete:
            return None

        # Find the next sifting prime
        while self.p * self.p <= self.limit:
            if self.is_candidate[self.p]:
                break
            self.p += 1
        else:
            # Final Wrap-up: Remaining candidates are identified as PRIME
            self.current_step += 1
            for i in range(2, self.limit + 1):
                if self.status_map[i]["status"] == NumberStatus.CANDIDATE:
                    self.status_map[i].update(
                        {
                            "status": NumberStatus.PRIME,
                            "identified_at_step": self.current_step,
                            "by_prime": i,
                        }
                    )
            self.is_complete = True
            return {"step": self.current_step, "action": "final_wrap_up"}

        self.current_step += 1
        active_p = self.p
        p_sq = active_p**2

        # 1. Update active sifter status
        if self.status_map[active_p]["identified_at_step"] is None:
            self.status_map[active_p]["identified_at_step"] = self.current_step

        self.status_map[active_p].update(
            {
                "status": NumberStatus.SIEVE_PRIME,
                "sieve_prime_at_step": self.current_step,
                "by_prime": active_p,
            }
        )

        # 2. Identification: Primes between p and p^2
        for i in range(active_p + 1, p_sq):
            if (
                i <= self.limit
                and self.status_map[i]["status"] == NumberStatus.CANDIDATE
            ):
                self.status_map[i].update(
                    {
                        "status": NumberStatus.PRIME,
                        "identified_at_step": self.current_step,
                        "by_prime": i,
                    }
                )

        # 3. Sifting: Multiples starting at p^2 are COMPOSITE
        for i in range(p_sq, self.limit + 1, active_p):
            if self.is_candidate[i]:
                self.is_candidate[i] = False
                self.status_map[i].update(
                    {
                        "status": NumberStatus.COMPOSITE,
                        "identified_at_step": self.current_step,
                        "by_prime": active_p,
                    }
                )

        self.p += 1
        return {"step": self.current_step, "active_sifter": active_p}

    def run_all(self):
        while not self.is_complete:
            self.step()
        return self.status_map

    def get_total_steps(self):
        return self.current_step

    def get_full_report(self):
        return self.status_map

    def get_step_stats(self):
        """
        Compute cumulative statistics per step.
        Returns a list of dicts (indexed by step number) with:
        - sieve_prime: the prime used to sieve at this step (None if not applicable)
        - num_primes: cumulative primes discovered (excluding 0, 1)
        - num_composites: cumulative composites discovered (excluding 0, 1)
        - num_unclassified: remaining unclassified numbers
        """
        if not self.is_complete:
            raise RuntimeError("Sieve must be complete before calling get_step_stats()")

        total_numbers = self.limit - 1  # numbers 2 to limit

        # Build step -> sieve_prime mapping
        sieve_prime_at: dict[int, int | None] = {0: None}  # step 0 has no sieve prime
        for num, data in self.status_map.items():
            if data["sieve_prime_at_step"] is not None:
                sieve_prime_at[data["sieve_prime_at_step"]] = num

        # Final step has no sieve prime (wrap-up)
        if self.current_step not in sieve_prime_at:
            sieve_prime_at[self.current_step] = None

        stats = []
        for step in range(self.current_step + 1):
            primes = 0
            composites = 0
            for num in range(2, self.limit + 1):
                data = self.status_map[num]
                identified = data["identified_at_step"]
                if identified is not None and identified <= step:
                    if data["status"] in (NumberStatus.PRIME, NumberStatus.SIEVE_PRIME):
                        primes += 1
                    elif data["status"] == NumberStatus.COMPOSITE:
                        composites += 1

            stats.append({
                "sieve_prime": sieve_prime_at.get(step),
                "num_primes": primes,
                "num_composites": composites,
                "num_unclassified": total_numbers - primes - composites,
            })

        return stats


def print_sieve_audit(limit):
    sieve = Sieve(limit)
    sieve.run_all()

    report = sieve.get_full_report()
    total_steps = sieve.get_total_steps()

    print(f"Sieve Audit Report (Limit: {limit} | Total Steps: {total_steps})")
    print(
        f"{'Num':<4} | {'Status':<12} | {'Identified':<12} | {'Sieve Prime':<10} | {'By Prime'}"
    )
    print("-" * 65)

    for i in range(limit + 1):
        data = report[i]

        # Formatting for readability
        status = data["status"].name
        ident = (
            f"Step {data['identified_at_step']}"
            if data["identified_at_step"] is not None
            else "-"
        )
        sift = (
            f"Step {data['sieve_prime_at_step']}"
            if data["sieve_prime_at_step"] is not None
            else "-"
        )
        resp = (
            data["by_prime"] if data["by_prime"] is not None else "-"
        )

        print(f"{i:<4} | {status:<12} | {ident:<12} | {sift:<10} | {resp}")


# Run it
if __name__ == "__main__":
    print_sieve_audit(30)
