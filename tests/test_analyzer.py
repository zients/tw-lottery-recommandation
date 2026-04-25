# tests/test_analyzer.py
from analyzer.analyzer import (
    frequency,
    hot_numbers,
    cold_numbers,
    recommend,
    recommend_special,
)

SAMPLE_DRAWS = [
    ("2024-01-01", [1, 2, 3, 4, 5]),
    ("2024-01-02", [1, 2, 6, 7, 8]),
    ("2024-01-03", [1, 9, 10, 11, 12]),
    ("2024-01-04", [13, 14, 15, 16, 17]),
    ("2024-01-05", [18, 19, 20, 21, 22]),
]

def test_frequency_counts_correctly():
    freq = frequency(SAMPLE_DRAWS)
    assert freq[1] == 3
    assert freq[2] == 2
    assert freq[13] == 1
    assert freq.get(39, 0) == 0

def test_frequency_returns_all_39_numbers():
    freq = frequency(SAMPLE_DRAWS)
    assert len(freq) == 39
    assert all(freq[n] >= 0 for n in range(1, 40))

def test_hot_numbers_returns_5():
    hot = hot_numbers(SAMPLE_DRAWS, window=5)
    assert len(hot) == 5

def test_hot_numbers_includes_most_frequent():
    hot = hot_numbers(SAMPLE_DRAWS, window=5)
    assert 1 in hot  # appears 3 times

def test_cold_numbers_returns_5():
    cold = cold_numbers(SAMPLE_DRAWS, window=5)
    assert len(cold) == 5

def test_hot_and_cold_no_overlap():
    hot = set(hot_numbers(SAMPLE_DRAWS, window=5))
    cold = set(cold_numbers(SAMPLE_DRAWS, window=5))
    assert len(hot & cold) == 0

def test_recommend_returns_3():
    result = recommend(SAMPLE_DRAWS)
    assert len(result) == 3

def test_recommend_each_has_5_numbers():
    result = recommend(SAMPLE_DRAWS)
    for combo in result:
        assert len(combo) == 5

def test_recommend_numbers_in_range():
    result = recommend(SAMPLE_DRAWS)
    for combo in result:
        assert all(1 <= n <= 39 for n in combo)

def test_recommend_distinct_combinations():
    result = recommend(SAMPLE_DRAWS)
    tuples = [tuple(sorted(c)) for c in result]
    assert len(set(tuples)) == 3


# --- recommend_special (used by 638 威力彩 special ball) -----------------

# Each draw is (date, [6 regular numbers..., special]). recommend_special
# counts the LAST element of each draw and returns the most-frequent value
# within the given special_range.
SPECIAL_DRAWS = [
    ("2024-01-01", [1, 2, 3, 4, 5, 6, 3]),  # special=3
    ("2024-01-02", [7, 8, 9, 10, 11, 12, 3]),  # special=3
    ("2024-01-03", [13, 14, 15, 16, 17, 18, 5]),  # special=5
    ("2024-01-04", [19, 20, 21, 22, 23, 24, 3]),  # special=3
    ("2024-01-05", [1, 2, 3, 4, 5, 6, 7]),  # special=7
]


def test_recommend_special_returns_most_frequent():
    # 3 appears 3×, 5 once, 7 once → expect 3
    assert recommend_special(SPECIAL_DRAWS, (1, 8)) == 3


def test_recommend_special_returns_int_in_range():
    result = recommend_special(SPECIAL_DRAWS, (1, 8))
    assert isinstance(result, int)
    assert 1 <= result <= 8


def test_recommend_special_ignores_out_of_range():
    # 99 is outside (1, 8); should be ignored, fall back to in-range max
    drawss = SPECIAL_DRAWS + [("2024-01-06", [1, 2, 3, 4, 5, 6, 99])]
    assert recommend_special(drawss, (1, 8)) == 3


def test_recommend_special_handles_empty_numbers():
    # empty draw shouldn't crash; falls back to lo with 0 count
    result = recommend_special([("2024-01-01", [])], (1, 8))
    assert result == 1  # all zero counts → max returns first key (lo)
