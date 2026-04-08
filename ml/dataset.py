# ml/dataset.py
import torch
from torch.utils.data import Dataset


class LotteryDataset(Dataset):
    """Sliding-window dataset over historical draws.

    Each sample is (context, target) where:
      context: (context_len, num_count) multi-hot float tensor of past draws
      target:  (num_count,) multi-hot float tensor of the next draw
    """

    def __init__(
        self,
        draws: list[tuple[str, list[int]]],
        context_len: int = 30,
        num_range: tuple[int, int] = (1, 39),
        analyze_count: int | None = None,
    ):
        self.lo, self.hi = num_range
        self.num_count = self.hi - self.lo + 1
        self.context_len = context_len

        # Optionally truncate to regular balls only (e.g. 638: 6 of 7)
        if analyze_count is not None:
            draws = [(d, nums[:analyze_count]) for d, nums in draws]
        self.draws = draws

    def __len__(self) -> int:
        return max(0, len(self.draws) - self.context_len)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        context_draws = self.draws[idx : idx + self.context_len]
        target_draw = self.draws[idx + self.context_len]

        context = torch.zeros(self.context_len, self.num_count)
        for i, (_, nums) in enumerate(context_draws):
            for n in nums:
                if self.lo <= n <= self.hi:
                    context[i, n - self.lo] = 1.0

        target = torch.zeros(self.num_count)
        for n in target_draw[1]:
            if self.lo <= n <= self.hi:
                target[n - self.lo] = 1.0

        return context, target


def is_oos_split(
    draws: list[tuple[str, list[int]]],
    cutoff_year: int = 2024,
) -> tuple[list, list]:
    """Split draws into in-sample (IS) and out-of-sample (OOS)."""
    is_draws = [(d, nums) for d, nums in draws if int(d[:4]) < cutoff_year]
    oos_draws = [(d, nums) for d, nums in draws if int(d[:4]) >= cutoff_year]
    return is_draws, oos_draws
