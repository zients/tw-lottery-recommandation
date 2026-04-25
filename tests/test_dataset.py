# tests/test_dataset.py
import pytest
from ml.dataset import is_oos_split

DRAWS = [(f"2024-01-{i:02d}", [1, 2, 3, 4, 5]) for i in range(1, 11)]  # 10 draws


def test_default_ratio_splits_80_20():
    is_draws, oos_draws = is_oos_split(DRAWS)
    assert len(is_draws) == 8
    assert len(oos_draws) == 2


def test_oos_takes_latest_draws():
    is_draws, oos_draws = is_oos_split(DRAWS, oos_ratio=0.3)
    assert oos_draws == DRAWS[-3:]
    assert is_draws == DRAWS[:-3]


def test_zero_ratio_returns_all_in_sample():
    is_draws, oos_draws = is_oos_split(DRAWS, oos_ratio=0.0)
    assert is_draws == DRAWS
    assert oos_draws == []


def test_small_dataset_rounds_down():
    # 3 draws * 0.2 = 0.6 → int() truncates to 0 OOS
    small = DRAWS[:3]
    is_draws, oos_draws = is_oos_split(small, oos_ratio=0.2)
    assert len(is_draws) == 3
    assert len(oos_draws) == 0


def test_empty_input():
    assert is_oos_split([]) == ([], [])


def test_invalid_ratio_raises():
    with pytest.raises(ValueError):
        is_oos_split(DRAWS, oos_ratio=1.0)
    with pytest.raises(ValueError):
        is_oos_split(DRAWS, oos_ratio=-0.1)
