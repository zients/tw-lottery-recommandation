# analyzer/analyzer.py
import random


def frequency(draws: list[tuple], num_range: tuple[int, int] = (1, 39)) -> dict[int, int]:
    lo, hi = num_range
    counts = {n: 0 for n in range(lo, hi + 1)}
    for _, numbers in draws:
        for n in numbers:
            if n in counts:
                counts[n] += 1
    return counts


def hot_numbers(draws: list[tuple], window: int = 30,
                num_range: tuple[int, int] = (1, 39), top: int = 5) -> list[int]:
    recent = draws[-window:] if len(draws) >= window else draws
    freq = frequency(recent, num_range)
    return [n for n, _ in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:top]]


def cold_numbers(draws: list[tuple], window: int = 30,
                 num_range: tuple[int, int] = (1, 39), top: int = 5) -> list[int]:
    recent = draws[-window:] if len(draws) >= window else draws
    freq = frequency(recent, num_range)
    hot = set(hot_numbers(draws, window, num_range, top))
    return [n for n, _ in sorted(
        [(n, c) for n, c in freq.items() if n not in hot],
        key=lambda x: x[1]
    )[:top]]


def recommend_special(draws: list[tuple], special_range: tuple[int, int]) -> int:
    """Pick the most frequent special ball (last element of each draw's numbers)."""
    lo, hi = special_range
    counts: dict[int, int] = {n: 0 for n in range(lo, hi + 1)}
    for _, numbers in draws:
        if numbers:
            n = numbers[-1]
            if n in counts:
                counts[n] += 1
    return max(counts, key=lambda n: counts[n])


def recommend(draws: list[tuple], cfg: dict | None = None) -> list[list[int]]:
    """Generate 3 recommended combinations based on frequency and optional filters.

    cfg keys used: num_range, analyze_count, odd_range, sum_range
    Defaults to 539 rules when cfg is None.
    """
    if cfg is None:
        cfg = {"num_range": (1, 39), "analyze_count": 5,
               "odd_range": (2, 3), "sum_range": (80, 120)}

    lo, hi = cfg["num_range"]
    pick = cfg["analyze_count"]
    odd_range = cfg.get("odd_range")
    sum_range = cfg.get("sum_range")

    freq = frequency(draws, (lo, hi))
    candidates = sorted(range(lo, hi + 1), key=lambda n: freq[n], reverse=True)[:20]

    def valid(combo: list[int]) -> bool:
        if odd_range:
            odd_count = sum(1 for n in combo if n % 2 != 0)
            if not (odd_range[0] <= odd_count <= odd_range[1]):
                return False
        if sum_range:
            if not (sum_range[0] <= sum(combo) <= sum_range[1]):
                return False
        return True

    results: list[list[int]] = []
    attempts = 0
    while len(results) < 3 and attempts < 1000:
        attempts += 1
        combo = sorted(random.sample(candidates, min(pick, len(candidates))))
        if valid(combo) and combo not in results:
            results.append(combo)

    # fallback: draw from full range
    while len(results) < 3:
        combo = sorted(random.sample(range(lo, hi + 1), pick))
        if valid(combo) and combo not in results:
            results.append(combo)

    return results
