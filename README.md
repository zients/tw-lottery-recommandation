# TW Lottery Recommendation

[![CI](https://github.com/zients/tw-lottery-recommendation/actions/workflows/test.yml/badge.svg)](https://github.com/zients/tw-lottery-recommendation/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.14+-blue.svg)](pyproject.toml)

Taiwan lottery draw analyzer & number recommender with a Transformer ML model. Supports multiple lottery types.

Data source: [Taiwan Lottery official API](https://api.taiwanlottery.com)

## ⚠️ Disclaimer

This project is for **educational, research, and entertainment purposes only**. Lottery draws are inherently random; the machine-learning model **cannot and does not predict winning numbers**, and no result is guaranteed. Please gamble responsibly and within your means.

This project is **not affiliated with, endorsed by, or connected to the Taiwan Lottery Co., Ltd.** in any way. Data is retrieved from its publicly available API. The authors accept no liability for any loss arising from use of this software.

## Daily Prediction Website

**https://zients.github.io/tw-lottery-recommendation/**

A GitHub Pages static site updated daily at 23:00 TST via GitHub Actions. Each day the workflow:

1. Fetches the latest draw results for all lottery types
2. Retrains the Transformer model (50 epochs)
3. Generates an HTML report with predictions for each lottery type
4. Deploys to GitHub Pages

## Supported Lotteries

| `--type` | Name | Format |
|----------|------|--------|
| `539` | Daily 539 | Pick 5, range 1–39 |
| `649` | Lotto 649 | Pick 6, range 1–49 |
| `638` | Super Lotto 638 | Pick 6 (1–38) + bonus ball (1–8) |
| `3d` | 3D Lottery | 3 digits, 0–9 |
| `4d` | 4D Lottery | 4 digits, 0–9 |

## Installation

```bash
uv sync
```

## Usage

### Update draw data

```bash
uv run lottery update --type 539                          # continues from latest DB record, or fetches from the beginning
uv run lottery update --type 649 --from-month 2024-01    # specify a start month
```

### Statistics

```bash
uv run lottery stats --type 539
```

Output:
- Top 10 most frequent numbers (all-time)
- Hot / cold numbers (last 30 draws)
- Bonus ball frequency Top 5 (638 only)

### Number recommendation

```bash
uv run lottery recommend --type 638
```

Generates 3 recommended combinations based on:
- Historical frequency (top 20 candidates)
- Odd/even ratio and sum range filters (539 / 649 / 638)
- Bonus ball recommendation (638 only)
- Transformer ML model when a trained checkpoint is available

### Train ML model

```bash
uv run lottery train --type 539 --epochs 100
```

Trains a Transformer model and saves the best checkpoint to `ml/checkpoints/`. Once trained, `recommend` will automatically use ML predictions.

### Generate HTML report locally

```bash
# 1. Update data and train models first
uv run lottery update --type 539   # repeat for each type
uv run lottery train --type 539    # repeat for each type

# 2. Generate the report
uv run python scripts/generate_report.py
```

Output is written to `dist/index.html` and `dist/YYYY-MM-DD.html`.

### Run tests

```bash
uv run pytest
```
