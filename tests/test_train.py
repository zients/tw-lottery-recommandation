import torch
import pytest

import ml.train as train_mod
from ml.train import coverage


class TinyLotteryModel(torch.nn.Module):
    def __init__(self, num_count: int):
        super().__init__()
        self.linear = torch.nn.Linear(num_count, num_count)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x[:, -1, :])


def _training_draws(count: int, num_count: int = 5) -> list[tuple[str, list[int]]]:
    return [
        (
            f"2024-01-{i + 1:02d}",
            [((i + offset) % num_count) + 1 for offset in range(2)],
        )
        for i in range(count)
    ]


def _patch_fast_training(monkeypatch: pytest.MonkeyPatch, tmp_path):
    monkeypatch.setattr(train_mod, "LotteryTransformer", TinyLotteryModel)
    monkeypatch.setattr(train_mod, "CHECKPOINT_DIR", tmp_path)


def _make_logits(probs: list[list[float]]) -> torch.Tensor:
    """Build logits whose sigmoid yields the given probabilities."""
    p = torch.tensor(probs)
    # sigmoid^-1(p) = log(p / (1 - p)); avoid 0/1 with clamp
    p = p.clamp(1e-6, 1 - 1e-6)
    return torch.log(p / (1 - p))


def test_coverage_perfect_prediction_returns_one():
    # 2 samples, 5 classes; pick top 2; both targets fully inside top-2
    logits = _make_logits([
        [0.9, 0.9, 0.1, 0.1, 0.1],  # top-2 = {0, 1}
        [0.1, 0.1, 0.9, 0.9, 0.1],  # top-2 = {2, 3}
    ])
    targets = torch.tensor([
        [1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0],
    ], dtype=torch.float)
    assert coverage(logits, targets, pick=2) == 1.0


def test_coverage_zero_when_no_overlap():
    logits = _make_logits([
        [0.9, 0.9, 0.1, 0.1, 0.1],  # top-2 = {0, 1}
    ])
    targets = torch.tensor([[0, 0, 1, 1, 0]], dtype=torch.float)
    assert coverage(logits, targets, pick=2) == 0.0


def test_coverage_partial_overlap():
    # top-2 picks {0, 1}; target is {0, 2} → 1 of 2 correct = 0.5
    logits = _make_logits([
        [0.9, 0.9, 0.1, 0.1, 0.1],
    ])
    targets = torch.tensor([[1, 0, 1, 0, 0]], dtype=torch.float)
    assert coverage(logits, targets, pick=2) == 0.5


def test_coverage_averages_over_batch():
    logits = _make_logits([
        [0.9, 0.9, 0.1, 0.1, 0.1],  # match {0, 1} fully → 1.0
        [0.9, 0.9, 0.1, 0.1, 0.1],  # match {2, 3} not at all → 0.0
    ])
    targets = torch.tensor([
        [1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0],
    ], dtype=torch.float)
    assert coverage(logits, targets, pick=2) == 0.5


def test_train_rejects_insufficient_in_sample_data():
    with pytest.raises(ValueError, match="Not enough IS data"):
        train_mod.train(
            _training_draws(3),
            lottery_type="539",
            num_range=(1, 5),
            analyze_count=2,
            pick=2,
            context_len=3,
            epochs=1,
        )


def test_train_saves_checkpoint_without_oos_data(monkeypatch, tmp_path):
    _patch_fast_training(monkeypatch, tmp_path)

    best_path = train_mod.train(
        _training_draws(4),
        lottery_type="539",
        num_range=(1, 5),
        analyze_count=2,
        pick=2,
        context_len=2,
        epochs=10,
        batch_size=2,
    )

    assert best_path == tmp_path / "539_best.pt"
    assert best_path.exists()


def test_train_evaluates_oos_and_saves_best_checkpoint(monkeypatch, tmp_path):
    _patch_fast_training(monkeypatch, tmp_path)

    best_path = train_mod.train(
        _training_draws(12),
        lottery_type="539",
        num_range=(1, 5),
        analyze_count=2,
        pick=2,
        context_len=3,
        epochs=10,
        batch_size=2,
    )

    assert best_path == tmp_path / "539_best.pt"
    assert best_path.exists()
