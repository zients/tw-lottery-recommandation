# ml/predict.py
from pathlib import Path
import torch

from ml.model import LotteryTransformer
from ml.train import CHECKPOINT_DIR


def checkpoint_path(lottery_type: str) -> Path:
    return CHECKPOINT_DIR / f"{lottery_type}_best.pt"


def has_model(lottery_type: str) -> bool:
    return checkpoint_path(lottery_type).exists()


def predict(
    draws: list[tuple[str, list[int]]],
    lottery_type: str,
    num_range: tuple[int, int],
    analyze_count: int,
    pick: int,
    context_len: int = 30,
    n_combos: int = 3,
) -> list[list[int]]:
    """Generate n_combos recommendations using the trained transformer model."""
    num_count = num_range[1] - num_range[0] + 1
    lo = num_range[0]

    model = LotteryTransformer(num_count)
    model.load_state_dict(torch.load(checkpoint_path(lottery_type), weights_only=True))
    model.train(False)

    recent = draws[-context_len:]
    if len(recent) < context_len:
        raise ValueError(f"Need at least {context_len} draws, got {len(recent)}")

    ctx = torch.zeros(1, context_len, num_count)
    for i, (_, nums) in enumerate(recent):
        for n in nums[:analyze_count]:
            if lo <= n <= num_range[1]:
                ctx[0, i, n - lo] = 1.0

    with torch.no_grad():
        logits = model(ctx).squeeze(0)
    probs = torch.sigmoid(logits)

    combos = []
    seen = set()
    attempts = 0
    while len(combos) < n_combos and attempts < 500:
        attempts += 1
        noise = torch.randn_like(probs) * 0.05
        indices = (probs + noise).topk(pick).indices.sort().values.tolist()
        key = tuple(indices)
        if key not in seen:
            seen.add(key)
            combos.append([i + lo for i in indices])

    return combos
